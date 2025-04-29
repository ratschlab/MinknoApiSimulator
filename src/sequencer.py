import queue
import threading
import time
from time import sleep

from minknow_api import data_pb2, acquisition_pb2
from read5 import read
import os

from test_utils import *
import config

class Reader():
    def __init__(self):
        Log.info("Creating reader on", config.params.input)
        self.signal_files = []
        inputpath = os.path.abspath(config.params.input)
        if os.path.exists(inputpath):
            if os.path.isfile(inputpath):
                if not inputpath.endswith(('.fast5', '.pod5', '.slow5', '.blow5')):
                    Log.error('File %s does not have the correct extension.' % inputpath)
                else:
                    self.signal_files.append(inputpath)
            elif os.path.isdir(inputpath):
                for filename in os.listdir(inputpath):
                    if filename.endswith(('.fast5', '.pod5', '.slow5', '.blow5')):
                        self.signal_files.append(os.path.join(inputpath, filename))
                if not self.signal_files:
                    Log.error('No signal files found in %s' % inputpath)
        else: Log.error('File/Folder %s not found' % inputpath)

        self.done = False
        self.__open_next_file()

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
            elif action.HasField('stop_further_data'):
                self.stop_sending = True
            return data_pb2.GetLiveReadsResponse.ActionResponse(
                action_id=action_id, response=data_pb2.GetLiveReadsResponse.ActionResponse.Response.SUCCESS
            )
        else:
            # there is no sequence in the pore, or the read_id of the action does not match with the current sequence
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
        self._acquisition_state = acquisition_pb2.AcquisitionState.ACQUISITION_STARTING
        Log.info('ACQUISITION_STARTING')

    def get_queues(self):
        """
        Returns the request and response queues
        :return: a tuple of (request_queue, response_queue)
        """
        return self.request_queue, self.response_queue

    def start(self):
        self.thread = threading.Thread(target=self.__run)
        self.thread.start()

    def stop(self):
        self.done = True    # fixme - not thread-safe
        self.thread.join()

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
                print()
                Log.info('ACQUISITION_COMPLETED')
            else:
                sleep_time = config.params.chunk_time - (time.monotonic() - self.last_sampled)
                if sleep_time > 0:
                    time.sleep(config.params.chunk_time - (time.monotonic() - self.last_sampled))
                self.last_sampled = time.monotonic()
                Log.status("%d" % self.samples_since_start)
                self.response_queue.put(
                    (action_responses, data_response, self.samples_since_start, self.samples_since_start/config.params.sample_rate)
                )
                self.samples_since_start += n_samples

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
        yield int(self.samples_since_start/config.params.channel_count)

    @property
    def processed(self):
        """Number of samples (per channel) passed to the analysis pipeline for processing."""
        yield self.acquired

    @property
    def acquisition_state(self):
        # acquisition_pb2.AcquisitionState.ACQUISITION_RUNNING or ACQUISITION_STARTING or ACQUISITION_COMPLETED
        yield self._acquisition_state

    @property
    def name(self):
        return config.params.name


