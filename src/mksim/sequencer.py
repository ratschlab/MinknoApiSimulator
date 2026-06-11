import queue
import threading
import time
from time import sleep
import random

from minknow_api import data_pb2, acquisition_pb2
import pyslow5
from pathlib import Path

from .test_utils import *
from . import config


class Reader:
    VALID_EXTENSIONS = ('.slow5', '.blow5')

    def __init__(self):
        self.r5 = None
        Log.info("Creating reader on", config.params.input)

        if not isinstance(config.params.input, list):
            Log.error("Input must be a list of paths.")
            self.signal_files = []
            self._done = threading.Event()
            self._done.set()
            return

        found_files_set = set()

        for path_str in config.params.input:
            try:
                input_path = Path(path_str).resolve(strict=True)
                files_from_path = self._discover_files(input_path)
                found_files_set.update(files_from_path)

            except FileNotFoundError:
                Log.warn(f"Input path not found, skipping: {path_str}")
            except ValueError as e:
                Log.warn(f"Error processing path '{path_str}', skipping: {e}")

        if not found_files_set:
            Log.error("Failed to initialize reader: No valid signal files found in any provided paths.")
            self.signal_files = []
            self._done = threading.Event()
            self._done.set()
        else:
            self.signal_files = sorted(list(found_files_set))
            # use threading.Event for done so reads/writes are safe
            # across threads if the threading model is ever extended.
            self._done = threading.Event()
            Log.info(f"Reader created. Found {len(self.signal_files)} unique file(s).")
            self.__open_next_file()

    @property
    def done(self) -> bool:
        """Thread-safe read of the done flag."""
        return self._done.is_set()

    def _discover_files(self, path: Path) -> list[str]:
        """
        Finds all valid signal files using pathlib, recursing into subdirectories.
        Returns a list of file path strings.
        """
        if path.is_file():
            if path.suffix not in self.VALID_EXTENSIONS:
                raise ValueError(f'File {path} does not have a valid extension.')
            return [str(path)]

        if path.is_dir():
            # use rglob instead of iterdir so nested subdirectories
            # (e.g. data/gut/community1/*.blow5) are discovered automatically.
            found_files = [
                str(file) for file in path.rglob('*')
                if file.suffix in self.VALID_EXTENSIONS and file.is_file()
            ]

            if not found_files:
                raise ValueError(f'No valid signal files found in directory: {path}')
            return found_files

        raise ValueError(f'Input path {path} is not a file or directory.')

    def __open_next_file(self):
        if hasattr(self, 'r5') and self.r5 is not None:
            self.r5.close()
        if self.signal_files:
            filename = self.signal_files.pop(0)
            self.r5 = pyslow5.Open(filename, 'r')
        else:
            self._done.set()

    def __next__(self):
        while not self.done:
            try:
                read = next(self.r5.seq_reads(aux='all'))
                return Sequence(read['read_id'], read['signal'])
            except StopIteration:
                self.__open_next_file()
                continue
        return None

    def __iter__(self):
        return self


class Sequence:
    def __init__(self, id, signal):
        """
        Encapsulates a sequence of raw signal values and manages windowed
        chunk delivery.

        :param id:     read / sequence identifier
        :param signal: raw signal as a numpy array

        Note: zero-length signals (len(signal) == 0) are handled gracefully —
        has_more() returns False immediately and no chunks are delivered.
        """
        self.id = id
        self.signal = signal
        self.CHUNK_SIZE = int(
            config.get_sample_rate(config.params.profile) * config.params.chunk_time
        )
        self.window_start = 0
        self.window_end = min(self.CHUNK_SIZE, len(self.signal))
        self.current_chunk = 0

        # Truncate each read to this many chunks before delivering to the client.
        # This simulates the real-time constraint that only the first N chunks of
        # a read are available when Readfish makes its accept/reject decision.
        # Set in config as `benchmark_chunks` (0 = deliver the full signal).
        self.benchmark_chunk_limit = (
            config.params.benchmark_chunks if config.params.benchmark_chunks > 0 else float('inf')
        )

    def has_more(self) -> bool:
        """
        Returns True if there is remaining signal to deliver AND the benchmark
        chunk limit has not been reached.

        The chunk limit truncates reads at the simulator level so that all tools
        are evaluated on an identical signal prefix, independent of full read
        length. This avoids modifying Readfish and ensures a fair comparison
        across tools with different internal stopping behaviour.
        """
        signal_remaining = self.window_start < self.window_end
        within_chunk_limit = self.current_chunk < self.benchmark_chunk_limit
        return signal_remaining and within_chunk_limit

    def advance(self):
        """
        Slides the delivery window forward by one CHUNK_SIZE.
        """
        self.window_start = self.window_end
        self.window_end = min(self.window_start + self.CHUNK_SIZE, len(self.signal))
        self.current_chunk += 1

    def get_signal(self):
        """
        Returns a GetLiveReadsResponse.ReadData protobuf for the current window.
        """
        length = self.window_end - self.window_start
        return data_pb2.GetLiveReadsResponse.ReadData(
            id=self.id,
            chunk_classifications=[83],  # 83 == strand signal
            chunk_length=length,
            raw_data=self.signal[self.window_start:self.window_end].tobytes(),
        )


class Pore:
    def __init__(self, reader: Reader):
        """
        Encapsulates a single nanopore channel.

        All pores share the same Reader instance.  Reads are distributed
        across pores in arrival order (first-come, first-served from the
        shared iterator).  This is intentional: it mirrors real pore
        behaviour where any available pore picks up the next molecule.

        :param reader: shared Reader instance
        """
        self.reader = reader
        self.sequence = None
        self.stop_sending = False
        self.file_consumed = False

        # stats
        self.n_ejected = 0
        self.n_proceeded = 0
        self.n_reads = 0
        self.n_missed = 0

        # FIX #7: pre-load the first sequence so the very first call to
        # get_signal_chunk() returns data rather than None.  Previously
        # __init__ left self.sequence = None, causing the first chunk of the
        # first read on every pore to be silently dropped.
        self._load_next_sequence()

    def _load_next_sequence(self):
        """
        Pull the next sequence from the shared Reader.
        Marks the pore as file_consumed if the reader is exhausted.
        Resets stop_sending so the new read streams normally.
        """
        self.sequence = next(self.reader)
        self.stop_sending = False
        if self.sequence is None:
            self.file_consumed = True
        else:
            self.n_reads += 1

    def update(self):
        """
        Called once per iteration after get_signal_chunk().

        Always advances the current sequence window first.  If the sequence is
        now exhausted (or was ejected), conditionally loads the next sequence
        gated by the occupancy probability.  This separates two concerns that
        were previously conflated:

          - advance()        : move the delivery window forward (always correct
                               to do after a chunk has been delivered)
          - _load_next_seq() : admit a new molecule to the pore (gated by
                               occupancy, only when the current read is done)

        Previously, has_more() was evaluated before advance(), so the window
        still pointed at the just-delivered chunk.  The check accidentally
        worked because a pore with one chunk remaining would pass the else
        branch and advance, then fail has_more() on the next iteration.
        Making the sequencing explicit removes that fragility.
        """
        if self.file_consumed:
            return

        if self.sequence is not None:
            self.sequence.advance()

        # After advancing, check whether the read is fully delivered (or was
        # ejected by setting sequence to None).  If so, admit the next read
        # subject to the occupancy gate.
        read_finished = self.sequence is None or not self.sequence.has_more()
        if read_finished:
            if random.random() < config.params.occupancy:
                self._load_next_sequence()

    def get_signal_chunk(self):
        """
        Returns the current signal chunk, or None if the pore is idle /
        stop_sending was requested / all reads have been consumed.
        """
        if (
            not self.file_consumed
            and not self.stop_sending
            and self.sequence
            and self.sequence.has_more()
        ):
            return self.sequence.get_signal()
        return None

    def __eject(self):
        """
        Immediately removes the current sequence from the pore so that
        update() will load the next one on the following iteration.
        """
        self.sequence = None

    def perform_action(self, action):
        """
        Applies an action (unblock or stop_further_data) received from the
        Read Until client.

        FIX #1: the original condition was inverted — it applied the action
        when read_id != self.sequence.id (stale / wrong-read actions) and
        returned FAILED when the IDs matched (the correct case).  The correct
        logic is: apply the action when the pore holds a sequence AND the
        requested read_id either matches or was not specified.

        :param action: GetLiveReadsResponse.ActionRequest protobuf
        :return:       GetLiveReadsResponse.ActionResponse protobuf
        """
        action_id = action.action_id
        read_id = action.id if action.HasField('id') else None

        # Apply the action only if:
        #   - a sequence is currently in the pore, AND
        #   - either no read_id was specified, OR it matches the current read.
        if self.sequence and (not read_id or read_id == self.sequence.id):
            if action.HasField('unblock'):
                self.__eject()
                self.n_ejected += 1
            elif action.HasField('stop_further_data'):
                self.stop_sending = True
                self.n_proceeded += 1
            return data_pb2.GetLiveReadsResponse.ActionResponse(
                action_id=action_id,
                response=data_pb2.GetLiveReadsResponse.ActionResponse.Response.SUCCESS,
            )
        else:
            # No sequence in pore, or read_id refers to a read that has
            # already finished / been replaced.
            self.n_missed += 1
            return data_pb2.GetLiveReadsResponse.ActionResponse(
                action_id=action_id,
                response=data_pb2.GetLiveReadsResponse.ActionResponse.Response.FAILED_READ_FINISHED,
            )


class Sequencer:
    def __init__(self):
        """
        Create a sequencer that replays raw signal files over the MinKNOW
        gRPC API.  Configuration (input paths, channel count, chunk timing,
        occupancy, etc.) is read from config.params.
        """
        self.n_channels = config.params.channel_count
        self.reader = Reader()
        self.pores = [Pore(self.reader) for _ in range(self.n_channels)]
        self.request_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self._done_event = threading.Event()
        self.last_sampled = 0.0
        self.samples_since_start = 0
        self.thread = None
        self.n_iters = 0
        self.total_sleep_time = 0.0
        self.log_interval = 10
        self._acquisition_state = acquisition_pb2.AcquisitionState.ACQUISITION_STARTING
        Log.info('ACQUISITION_STARTING')

    @property
    def done(self) -> bool:
        return self._done_event.is_set()

    def get_queues(self):
        """Returns the (request_queue, response_queue) pair used by the gRPC layer."""
        return self.request_queue, self.response_queue

    def start(self):
        Path(config.params.output_path).mkdir(parents=True, exist_ok=True)
        self.thread = threading.Thread(target=self.__run, daemon=True)
        self.thread.start()

    def stop(self):
        self._done_event.set()
        self.thread.join()
        config.stop_event.set()

    def __run(self):
        """
        Main sequencer loop (runs in its own thread):
          1. Collect pending action requests from the request queue.
          2. Apply actions to the appropriate pores.
          3. Advance pore state and collect signal chunks.
          4. Enqueue (action_responses, signal_data, sample_count, elapsed_s)
             for the gRPC layer to forward to the client.
          5. Sleep for the remainder of the chunk window, then repeat.
        """
        sleep(config.params.wait_seconds)
        self._acquisition_state = acquisition_pb2.AcquisitionState.ACQUISITION_RUNNING
        Log.info('ACQUISITION_RUNNING')
        self.total_sleep_time = 0.0
        self.last_sampled = time.monotonic()

        while not self.done:
            action_requests  = self.__collect_action_requests()
            action_responses = self.__perform_actions(action_requests)
            data_response, n_samples = self.__update_pores()

            self.samples_since_start += n_samples
            self.n_iters += 1                          # FIX: increment on every iteration,
                                                       # including the final one
            sample_rate = config.get_sample_rate(config.params.profile)

            if self.reader.done:
                # enqueue the final batch before marking acquisition
                # complete so the gRPC layer can deliver the last responses
                # (including any action responses) to the client.
                self.response_queue.put((
                    action_responses,
                    data_response,
                    self.samples_since_start,
                    self.samples_since_start / sample_rate,
                ))
                self._acquisition_state = acquisition_pb2.AcquisitionState.ACQUISITION_COMPLETED
                self._done_event.set()
            else:
                sleep_time = config.params.chunk_time - (time.monotonic() - self.last_sampled)
                self.total_sleep_time += max(sleep_time, 0.0)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.last_sampled = time.monotonic()

                if self.n_iters % self.log_interval == 0:
                    Log.status(self.get_status())
                    self.total_sleep_time = 0.0

                self.response_queue.put((
                    action_responses,
                    data_response,
                    self.samples_since_start,
                    self.samples_since_start / sample_rate,
                ))

        print()
        Log.info('ACQUISITION_COMPLETED')
        # Wait for the client to drain and disconnect, but return early if
        # stop_event is set so we don't block the thread unnecessarily.
        # FIX: was sleep(5), which always blocked for the full 5 seconds.
        config.stop_event.wait(timeout=5)
        config.stop_event.set()

    def __update_pores(self):
        """
        For each channel: emit a signal chunk if the pore is actively
        sequencing, then advance pore state.

        The occupancy gate (random.random() < occupancy) is now handled inside
        Pore.update() when a read finishes, keeping this method free of
        occupancy logic.
        """
        n_samples = 0
        data_responses = {}

        for i in range(self.n_channels):
            pore = self.pores[i]

            # Always deliver signal if the pore is actively sequencing.
            response = pore.get_signal_chunk()
            if response:
                data_responses[i + 1] = response   # channels are 1-indexed
                n_samples += response.chunk_length

            pore.update()

        return data_responses, n_samples

    def __collect_action_requests(self):
        action_requests = []
        while not self.request_queue.empty():
            action_requests.append(self.request_queue.get())
        return action_requests

    def __perform_actions(self, actions):
        return [self.pores[action.channel - 1].perform_action(action) for action in actions]

    # ------------------------------------------------------------------
    # Properties exposed to the gRPC service layer
    # ------------------------------------------------------------------

    @property
    def acquired(self) -> int:
        """Number of samples (per channel) acquired from the device."""
        return int(self.samples_since_start / self.n_channels)

    @property
    def processed(self) -> int:
        """Number of samples (per channel) passed to the analysis pipeline."""
        return self.acquired

    @property
    def acquisition_state(self):
        return self._acquisition_state

    @property
    def name(self) -> str:
        return config.params.name

    def get_status(self) -> str:
        avg_wait = (
            self.total_sleep_time / self.log_interval
            if self.log_interval > 0
            else 0.0
        )
        return (
            "#Iters: {}, Read: {}, Ejected: {}, Passed: {}, Missed: {}, "
            "Avg. wait: {:.3f}s".format(
                self.n_iters,
                sum(p.n_reads     for p in self.pores),
                sum(p.n_ejected   for p in self.pores),
                sum(p.n_proceeded for p in self.pores),
                sum(p.n_missed    for p in self.pores),
                avg_wait,
            )
        )