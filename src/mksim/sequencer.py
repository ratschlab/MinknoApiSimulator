import queue
import threading
import time
from time import sleep

from minknow_api import data_pb2, acquisition_pb2
from read5 import read
from pathlib import Path

from test_utils import *
import config

class Reader:
    VALID_EXTENSIONS = ('.fast5', '.pod5', '.slow5', '.blow5')

    def __init__(self):
        Log.info("Creating reader on", config.params.input)

        if not isinstance(config.params.input, list):
            Log.error("Input must be a list of paths.")
            self.signal_files = []
            self.done = True
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

        # Final check after the loop
        if not found_files_set:
            Log.error("Failed to initialize reader: No valid signal files found in any provided paths.")
            self.signal_files = []
            self.done = True
        else:
            self.signal_files = sorted(list(found_files_set))
            self.done = False
            Log.info(f"Reader created. Found {len(self.signal_files)} unique file(s).")
            self.__open_next_file()

    def _discover_files(self, path: Path) -> list[str]:
        """
        Finds all valid signal files using pathlib.
        Returns a list of file paths as strings.
        """
        if path.is_file():
            if path.suffix not in self.VALID_EXTENSIONS:
                raise ValueError(f'File {path} does not have a valid extension.')
            return [str(path)]  # Return as a list of strings

        if path.is_dir():
            # This list comprehension is much cleaner than the for-loop
            found_files = [
                str(file) for file in path.iterdir()
                if file.suffix in self.VALID_EXTENSIONS and file.is_file()
            ]

            if not found_files:
                raise ValueError(f'No valid signal files found in directory: {path}')
            return found_files

        raise ValueError(f'Input path {path} is not a file or directory.')

    def __open_next_file(self):
        if self.signal_files:
            filename = self.signal_files.pop(0)
            self.r5 = read(filename)
        else: self.done = True

    def __next__(self):
        while not self.done:
            try:
                rid = next(self.r5)
                return Sequence(rid, self.r5.getSignal(rid))
            except StopIteration:
                self.__open_next_file()
                continue
        return None

    def __iter__(self):
        return self


class Sequence:
    def __init__(self, id, signal):
        """
        Encapsulates a sequence of signal values
        :param id: sequence-id
        :param signal: signals (numpy array)
        """
        self.id = id
        self.signal = signal
        self.CHUNK_SIZE = int(config.params.sample_rate * config.params.chunk_time)
        self.window_start = 0
        self.window_end = min(len(self.signal)-self.window_start, self.CHUNK_SIZE)

    def has_more(self):
        """
        Checks if the sequence has more signal values
        :return: bool
        """
        return self.window_start < self.window_end

    def advance(self):
        """
        Advances the sequence window
        :return: None
        """
        self.window_start = self.window_end
        self.window_end = min(len(self.signal) - self.window_start, self.CHUNK_SIZE)

    def get_signal(self):
        """
        Returns the signal values in the current window
        :return: GetLiveReadsResponse.ReadData object
        """
        length = self.window_end - self.window_start
        return data_pb2.GetLiveReadsResponse.ReadData(
            id=self.id,
            chunk_classifications=[83],  # strand
            chunk_length=length,
            raw_data=self.signal[self.window_start:self.window_end].tobytes(),
        )


class Pore:
    def __init__(self, reader: Reader):
        """
        Encapsulates a nanopore channel
        :param r5: read5 signal file handle
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

    def update(self):
        """
        Update the pore by either advancing the sequence through the pore or admitting a new sequence
        Remember if there are no more sequences in the file
        :return: None
        """
        if not self.file_consumed:
            if self.sequence and self.sequence.has_more():
                self.sequence.advance()
            else:
                self.sequence = next(self.reader)
                self.stop_sending = False
                if not self.sequence: self.file_consumed = True
                else: self.n_reads += 1

    def get_signal_chunk(self):
        """
        Returns the chunk of signals from the sequence currently in the pore
        :return: GetLiveReadsResponse.ReadData object or None if there is no more sequence or the client explicitly requested
        to not send any more data
        """
        if not self.file_consumed and not self.stop_sending and self.sequence and self.sequence.has_more():
            return self.sequence.get_signal()
        return None

    def __eject(self):
        """
        Ejects a sequence from the pore
        :return: None
        """
        self.sequence = None

    def perform_action(self, action):
        """
        Performs a given action, which can be to either eject (unblock) the sequence or ignore further data from it
        :param action: GetLiveReadsResponse.ActionRequest object
        :return: GetLiveReadsResponse.ActionResponse object
        """
        action_id = action.action_id
        read_id = action.id if action.HasField('id') else None
        if (not read_id and self.sequence) or (self.sequence and read_id != self.sequence.id):
            if action.HasField('unblock'):
                self.__eject()
                self.n_ejected += 1
            elif action.HasField('stop_further_data'):
                self.stop_sending = True
                self.n_proceeded += 1
            return data_pb2.GetLiveReadsResponse.ActionResponse(
                action_id=action_id, response=data_pb2.GetLiveReadsResponse.ActionResponse.Response.SUCCESS
            )
        else:
            # there is no sequence in the pore, or the read_id of the action does not match with the current sequence
            self.n_missed += 1
            return data_pb2.GetLiveReadsResponse.ActionResponse(
                action_id=action_id, response=data_pb2.GetLiveReadsResponse.ActionResponse.Response.FAILED_READ_FINISHED
            )


class Sequencer:
    def __init__(self):
        """
        Create a sequencer.
        :param filename: file containing signals (pod5, fast5, slow5, blow5)
        :param n_channels: number of pores/channels
        """
        self.n_channels = config.params.channel_count
        self.reader = Reader()
        self.pores = [Pore(self.reader) for _ in range(self.n_channels)]
        self.request_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.done = False
        self.last_sampled = 0.0
        self.samples_since_start = 0
        self.thread = None
        self.n_iters = 0
        self.total_sleep_time = 0
        self.log_interval = 10  # logs will be printer every `self.log_interval` iterations
        self._acquisition_state = acquisition_pb2.AcquisitionState.ACQUISITION_STARTING
        Log.info('ACQUISITION_STARTING')

    def get_queues(self):
        """
        Returns the request and response queues
        :return: a tuple of (request_queue, response_queue)
        """
        return self.request_queue, self.response_queue

    def start(self):
        Path(config.params.output_path).mkdir(parents=True, exist_ok=True)
        self.thread = threading.Thread(target=self.__run)
        self.thread.start()

    def stop(self):
        self.done = True    # fixme - not thread-safe
        self.thread.join()
        config.stop_event.set()

    def __run(self):
        """
        Runs the sequencer in a new thread which does the following in a loop
        1. reads signal chunks on all pores.
        2. checks the request queue for action requests.
        3. takes any actions requested and save action responses.
        4. wait till SAMPLE_DURATION has elapsed on the timer (last_sampled).
        5. send the signal data and action responses on response queue.
        :return: None
        """
        sleep(config.params.wait_seconds)
        self._acquisition_state = acquisition_pb2.AcquisitionState.ACQUISITION_RUNNING
        Log.info('ACQUISITION_RUNNING')
        self.last_sampled = time.monotonic()
        while not self.done:
            action_requests = self.__collect_action_requests()
            action_responses = self.__perform_actions(action_requests)
            data_response, n_samples = self.__update_pores()
            if self.reader.done:
                self._acquisition_state = acquisition_pb2.AcquisitionState.ACQUISITION_COMPLETED
                self.done = True
            else:
                sleep_time = config.params.chunk_time - (time.monotonic() - self.last_sampled)
                self.total_sleep_time += sleep_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.last_sampled = time.monotonic()
                self.n_iters += 1
                if self.n_iters % self.log_interval == 0:
                    Log.status(self.get_status())
                    self.total_sleep_time = 0
                self.response_queue.put(
                    (action_responses, data_response, self.samples_since_start, self.samples_since_start / config.params.sample_rate)
                )
                self.samples_since_start += n_samples
        print()
        Log.info('ACQUISITION_COMPLETED')
        # wait for 5 seconds for clients to disconnect
        sleep(5)
        config.stop_event.set()

    def __update_pores(self):
        """
        Update the data on all pores.
        :return: None
        """
        n_samples = 0
        data_responses = {}
        for i in range(self.n_channels):
            response = self.pores[i].get_signal_chunk()
            if response:
                data_responses[i+1] = response    # again, i+1 because channels are 1-indexed
                n_samples += response.chunk_length
            self.pores[i].update()
        return data_responses, n_samples


    def __collect_action_requests(self):
        action_requests = []
        while not self.request_queue.empty():
            action_requests.append(self.request_queue.get())
        return action_requests

    def __perform_actions(self, actions):
        return [self.pores[action.channel-1].perform_action(action) for action in actions]

    @property
    def acquired(self):
        """Number of samples (per channel) acquired from the device"""
        return int(self.samples_since_start / config.params.channel_count)

    @property
    def processed(self):
        """Number of samples (per channel) passed to the analysis pipeline for processing."""
        return self.acquired

    @property
    def acquisition_state(self):
        # acquisition_pb2.AcquisitionState.ACQUISITION_RUNNING or ACQUISITION_STARTING or ACQUISITION_COMPLETED
        return self._acquisition_state

    @property
    def name(self):
        return config.params.name

    def get_status(self):
        return "#Iters: {}, Read: {}, Ejected: {}, Passed: {}, Missed: {}, Avg. wait: {:.2f}s".format(
            self.n_iters,
            sum(pore.n_reads for pore in self.pores),
            sum(pore.n_ejected for pore in self.pores),
            sum(pore.n_proceeded for pore in self.pores),
            sum(pore.n_missed for pore in self.pores),
            self.total_sleep_time/self.log_interval
        )


