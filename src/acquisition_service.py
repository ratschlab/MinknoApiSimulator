from prelude import *
from minknow_api import acquisition_pb2, acquisition_pb2_grpc

class AcquisitionService(acquisition_pb2_grpc.AcquisitionServiceServicer):
    def get_progress(self, request, context):
        info("acquisition: get_progress")
        return acquisition_pb2.GetProgressResponse(
            acquisition_pb2.GetProgressResponse.RawPerChannel(
                acquired = 123, processed = 456
            )
        )