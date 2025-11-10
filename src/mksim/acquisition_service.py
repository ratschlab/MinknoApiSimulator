from minknow_api import acquisition_pb2, acquisition_pb2_grpc

from .sequencer import Sequencer

class AcquisitionService(acquisition_pb2_grpc.AcquisitionServiceServicer):

    def __init__(self, sequencer: Sequencer):
        self.sequencer = sequencer

    def get_progress(self, request, context):
        # raw_per_channel
        return acquisition_pb2.GetProgressResponse(
            raw_per_channel = acquisition_pb2.GetProgressResponse.RawPerChannel(
                acquired = self.sequencer.acquired,
                processed = self.sequencer.processed,
            )
        )

    def get_acquisition_info(self, request, context):
        # state
        return acquisition_pb2.AcquisitionRunInfo(
            state = self.sequencer.acquisition_state
        )