from prelude import *
from enum import Enum
from minknow_api import data_pb2, data_pb2_grpc
# from reader import server
from multiprocessing import Process
# import zmq
from dataclasses import dataclass
import time
from read5 import read

import threading
import queue


blow5_file = "/scratch/Zymo/signal/blow5/s180/0/Sigs-0.blow5"
fast5_file = "/scratch/Zymo/signal/fast5/s180/0/Sigs-0.fast5"
pod5_file = "/data/PBA70346_skip_5c03b04e_00bcc91b_0.pod5"
CHUNK_SIZE = 1600

@dataclass
class Read:
    def __init__(self, rid, signal):
        self.rid = rid
        self.signal = signal

def package_read(read: Read, start: int):
    length = min(CHUNK_SIZE, len(read.signal) - start)
    return data_pb2.GetLiveReadsResponse.ReadData(
        id=read.rid,
        chunk_classifications=[83], # strand
        chunk_length=length,
        raw_data=read.signal[start:start + length].tobytes(),
    )


class ReadDataThreads:
    def __init__(self, filename, n_channels):
        self.r5 = read(filename)
        self.n_channels = n_channels
        self.reads = [None for _ in range(n_channels)]
        self.offsets = [0 for _ in range(n_channels)]
        self.stop_receiving = set()
        self.eject = set()

    def _update(self):
        for i in range(self.n_channels):
            if self.reads[i] is not None:
                advance = min(CHUNK_SIZE, len(self.reads[i].signal) - self.offsets[i])
                self.offsets[i] += advance
            if self.reads[i] is None or len(self.reads[i].signal) == self.offsets[i]:
                rid = next(self.r5)
                if rid is not None:
                    self.reads[i] = Read(rid, self.r5.getSignal(rid))
                    self.offsets[i] = 0
                else:
                    self.reads[i] = None
                    self.offsets[i] = 0

    def _eject(self, i):
        self.reads[i] = None

    def get_data(self):
        data = {}
        self._update()
        for i in range(self.n_channels):
            if i in self.stop_receiving:
                continue # don't add the read to the result
            elif i in self.eject:
                self._eject(i)
            elif self.reads[i] is not None:
                data[i+1] = package_read(self.reads[i], self.offsets[i])
        return data

class DataService(data_pb2_grpc.DataServiceServicer):
    def __init__(self):
        self.setup = False
        self.first_channel = 0
        self.last_channel = 0
        self.raw_data_type = data_pb2.GetLiveReadsRequest.RawDataType.KEEP_LAST
        # self.reader_process = Process(target=server)
        # self.reader_process.start()
        # self.context = zmq.Context()
        # self.server_socket = self.context.socket(zmq.REQ)
        # self.server_socket.connect("ipc:///tmp/mksim")
        self.read_data_threads = ReadDataThreads(blow5_file, 512)
        self.last_sampled = time.time()


    def _setup(self, config):
        info("data: get_live_reads.setup")
        print(f"Received StreamSetup: first_channel={config.first_channel}, "
              f"last_channel={config.last_channel}, "
              f"raw_data_type={config.raw_data_type}")
        self.setup = True
        self.first_channel = config.first_channel
        self.last_channel = config.last_channel
        self.raw_data_type = config.raw_data_type
        # self.sample_minimum_chunk_size = config.sample_minimum_chunk_size
        # if config.max_unblock_read_length.HasField("max_unblock_read_length_samples"):
        #     info("unblock_read_length in samples: max_unblock_read_length_samples")
        # elif config.max_unblock_read_length.HasField("max_unblock_read_length_seconds"):
        #     info("unblock_read_length in seconds: max_unblock_read_length_seconds")
        # self.accepted_first_chunk_classifications = config.accepted_first_chunk_classifications

    def _perform_actions(self, actions):
        info("data: perform_actions")
        return [self._perform_action(action) for action in actions.actions]

    def _perform_action(self, action):
        # info(f"Received Action: action_id={action.action_id}, "
        #       f"channel={action.channel}, read_id={action.id}")

        # Simulate processing the action -- todo

        return data_pb2.GetLiveReadsResponse.ActionResponse(
            action_id=action.action_id,
            response=data_pb2.GetLiveReadsResponse.ActionResponse.Response.SUCCESS
        )

    def _get_data(self):
        # self.server_socket.send_string("")
        # data = self.server_socket.recv_pyobj()
        data = self.read_data_threads.get_data()
        # current_time = time.time()
        # elapsed_time = current_time - self.last_sampled
        # if elapsed_time < 0.4:
        #     time.sleep(0.4 - elapsed_time)
        self.last_sampled = time.time()
        return data

    def get_data_types(self, request, context):
        info("data: get_data_types")
        return data_pb2.GetDataTypesResponse(
            uncalibrated_signal = data_pb2.GetDataTypesResponse.DataType(
                type=data_pb2.GetDataTypesResponse.DataType.Type.SIGNED_INTEGER, big_endian=False, size=2
            ),
            calibrated_signal = data_pb2.GetDataTypesResponse.DataType(
                type=data_pb2.GetDataTypesResponse.DataType.Type.FLOATING_POINT, big_endian=False, size=4
            ),
            bias_voltages = data_pb2.GetDataTypesResponse.DataType(
                type=data_pb2.GetDataTypesResponse.DataType.Type.SIGNED_INTEGER, big_endian=False, size=2
            )
        )

    def get_live_reads(self, request_iterator, context):
        info("data: get_live_reads")

        response_queue = queue.Queue()

        def request_handler():
            for request in request_iterator:
                if request.HasField("setup"):
                    self._setup(request.setup)
                elif request.HasField("actions"):
                    action_responses = self._perform_actions(request.actions)
                    response_queue.put(action_responses)

        # Start request handler in a separate thread
        threading.Thread(target=request_handler, daemon=True).start()

        while True:
            info("data: packaging reads...")
            data_responses = self._get_data()
            action_responses = [] if response_queue.empty() else response_queue.get()

            info("data: sending reads...")
            yield data_pb2.GetLiveReadsResponse(
                channels = data_responses,
                action_responses = action_responses,
                samples_since_start = 4000, # fixme
                seconds_since_start = 1,    # fixme
            )

            info("data: done")
            time.sleep(1)