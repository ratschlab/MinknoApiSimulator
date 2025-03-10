from prelude import *
from test_utils import *
from minknow_api import data_pb2, data_pb2_grpc
import time

import threading
import queue
from sequencer import Sequencer

blow5_file = "/scratch/Zymo/signal/blow5/s180/0/Sigs-0.blow5"
fast5_file = "/scratch/Zymo/signal/fast5/s180/0/Sigs-0.fast5"
pod5_file = "/data/PBA70346_skip_5c03b04e_00bcc91b_0.pod5"

class DataService(data_pb2_grpc.DataServiceServicer):
    def __init__(self):
        self.setup = False
        self.first_channel = 0
        self.last_channel = 0
        self.raw_data_type = data_pb2.GetLiveReadsRequest.RawDataType.KEEP_LAST
        self.sequencer = Sequencer(filename=blow5_file, n_channels=512)
        self.request_queue, self.response_queue = self.sequencer.get_queues()
        self.sequencer.start()

    def _setup(self, config):
        info("data: get_live_reads.setup")
        print(f"Received StreamSetup: first_channel={config.first_channel}, "
              f"last_channel={config.last_channel}, "
              f"raw_data_type={config.raw_data_type}")
        self.setup = True
        self.first_channel = config.first_channel
        self.last_channel = config.last_channel
        self.raw_data_type = config.raw_data_type

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

        def request_handler():
            try:
                for request in request_iterator:
                    if request.HasField("setup"):
                        self._setup(request.setup)
                    elif request.HasField("actions"):
                        for action in request.actions.actions:
                            self.request_queue.put(action)
            except Exception as e:
                print(e)

        # Start request handler in a separate thread
        rht = threading.Thread(target=request_handler, daemon=True)
        rht.start()

        while context.is_active():
            if not self.response_queue.empty():
                action_responses, data_responses = self.response_queue.get()
                blurt("A%d-D%d" % (len(action_responses), len(data_responses)), color=CYN)
                try:
                    yield data_pb2.GetLiveReadsResponse(
                        channels = data_responses,
                        action_responses = action_responses,
                        samples_since_start = 4000, # fixme
                        seconds_since_start = 1,    # fixme
                    )
                except Exception as e:
                    print(e)
            time.sleep(.1)

        rht.join()