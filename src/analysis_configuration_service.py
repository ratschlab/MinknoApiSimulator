from logs import *
from minknow_api import analysis_configuration_pb2, analysis_configuration_pb2_grpc
import google.protobuf.wrappers_pb2 as wrappers_pb2
import config


class AnalysisConfigurationService(analysis_configuration_pb2_grpc.AnalysisConfigurationServiceServicer):

    def get_read_classifications(self, request, context):
        response = analysis_configuration_pb2.GetReadClassificationsResponse(
            read_classifications = config.read_classifications
        )
        return response

    def get_analysis_configuration(self, request, context):
        # read_detection.break_reads_after_seconds.value
        return analysis_configuration_pb2.AnalysisConfiguration(
            read_detection = analysis_configuration_pb2.ReadDetectionParams(
                break_reads_after_seconds=wrappers_pb2.DoubleValue(value=config.params.chunk_time)
            )
        )