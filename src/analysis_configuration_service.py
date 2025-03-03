from prelude import *
from minknow_api import analysis_configuration_pb2, analysis_configuration_pb2_grpc
import google.protobuf.wrappers_pb2 as wrappers_pb2


class AnalysisConfigurationService(analysis_configuration_pb2_grpc.AnalysisConfigurationServiceServicer):
    def get_read_classifications(self, request, context):
        info("analysis_configuration: get_read_classifications")
        response = analysis_configuration_pb2.GetReadClassificationsResponse(
            read_classifications = {
                83: "strand",
                67: "strand1",
                82: "strand2", # fixme
                81: "short_strand", # fixme
                79: "unknown_positive", # fixme
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
        return response

    def get_analysis_configuration(self, request, context):
        info("analysis_configuration: get_analysis_configuration")
        # read_detection.break_reads_after_seconds.value
        return analysis_configuration_pb2.AnalysisConfiguration(
            read_detection = analysis_configuration_pb2.ReadDetectionParams(
                break_reads_after_seconds=wrappers_pb2.DoubleValue(value=.4)
            )
        )