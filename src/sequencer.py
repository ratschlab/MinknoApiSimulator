from prelude import *
from test_utils import *
from enum import Enum
from minknow_api import data_pb2, data_pb2_grpc
from multiprocessing import Process
from dataclasses import dataclass
import time
from read5 import read

import threading
import queue

SAMPLE_DURATION = .4    # .4 or .8
CHUNK_SIZE = 1600 * int(SAMPLE_DURATION / .4)


class Sequence:
    def __init__(self, id, signal):
        """
        Encapsulates a sequence of signal values
        :param id: sequence-id
        :param signal: signals (numpy array)
        """
        self.id = id
        self.signal = signal
        self.window_start = 0
        self.window_end = min(len(self.signal)-self.window_start, CHUNK_SIZE)

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
        self.window_end = min(len(self.signal) - self.window_start, CHUNK_SIZE)

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
    def __init__(self, r5):
        """
        Encapsulates a nanopore channel
        :param r5: read5 signal file handle
        """
        self.r5 = r5
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
                try:
                    rid = next(self.r5)
                    if rid is None:
                        self.sequence = None
                        self.file_consumed = True
                    else:
                        self.sequence = Sequence(rid, self.r5.getSignal(rid))
                        self.stop_sending = False
                except StopIteration:
                    self.sequence = None
                    self.file_consumed = True

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
    def __init__(self, filename: str, n_channels: int):
        """
        Create a sequencer.
        :param filename: file containing signals (pod5, fast5, slow5, blow5)
        :param n_channels: number of pores/channels
        """
        self.n_channels = n_channels
        self.r5 = read(filename)
        self.pores = [Pore(self.r5) for _ in range(n_channels)]
        self.request_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.done = False
        self.last_sampled = 0.0
        self.thread = None

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
        self.last_sampled = time.monotonic()
        while not self.done:
            action_requests = self.__collect_action_requests()
            action_responses = self.__perform_actions(action_requests)
            data_response = self.__update_pores()
            sleep_time = SAMPLE_DURATION - (time.monotonic() - self.last_sampled)
            if sleep_time > 0:
                time.sleep(SAMPLE_DURATION - (time.monotonic() - self.last_sampled))
            self.last_sampled = time.monotonic()
            self.response_queue.put((action_responses, data_response))
            blurt("{}A-{}D".format(len(action_responses), len(data_response)), color=RED)

    def __update_pores(self):
        """
        Update the data on all pores.
        :return: None
        """
        data_responses = {}
        for i in range(self.n_channels):
            response = self.pores[i].get_signal_chunk()
            if response:
                data_responses[i+1] = response    # again, i+1 because channels are 1-indexed
            self.pores[i].update()
        return data_responses


    def __collect_action_requests(self):
        action_requests = []
        while not self.request_queue.empty():
            action_requests.append(self.request_queue.get())
        return action_requests

    def __perform_actions(self, actions):
        return [self.pores[action.channel-1].perform_action(action) for action in actions]

