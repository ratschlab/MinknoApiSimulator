from prelude import *
from minknow_api import analysis_configuration_pb2, analysis_configuration_pb2_grpc

class AnalysisConfigurationService(analysis_configuration_pb2_grpc.AnalysisConfigurationServiceServicer):
    def get_read_classifications(self, request, context):
        info("analysis_configuration: get_read_classifications")
        response = analysis_configuration_pb2.GetReadClassificationsResponse(
            read_classifcations = {
                83: "strand",
                67: "strand1",
                77: "multiple",
                90: "zero",
                65: "adapter",
                66: "mux_uncertain",
                70: "user2",
                68: "user1",
                69: "event",
                80: "pore",
                85: "unavailable",
                84: "transition",
                78: "unclassed"
            }
        )