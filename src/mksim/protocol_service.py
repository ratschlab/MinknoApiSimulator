
from . import config
from minknow_api import protocol_pb2, protocol_pb2_grpc

class ProtocolService(protocol_pb2_grpc.ProtocolServiceServicer):
    def get_run_info(self, request, context):
        version_info_response = config.other_version_info
        version_info_response['minknow'] = protocol_pb2.GetVersionInfoResponse.MinknowVersion(
            **config.minknow_version_info)
        software_versions = protocol_pb2.GetVersionInfoResponse(**version_info_response)

        return protocol_pb2.ProtocolRunInfo(
            run_id = config.params.run_id,
            software_versions = software_versions
        )

    def get_current_protocol_run(self, request, context):
        version_info_response = config.other_version_info
        version_info_response['minknow'] = protocol_pb2.GetVersionInfoResponse.MinknowVersion(
            **config.minknow_version_info)
        software_versions = protocol_pb2.GetVersionInfoResponse(**version_info_response)

        return protocol_pb2.ProtocolRunInfo(
            run_id = config.params.run_id,
            output_path = config.params.output_path,
            state = protocol_pb2.ProtocolState.PROTOCOL_RUNNING,
            phase = protocol_pb2.ProtocolPhase.PHASE_SEQUENCING,
            software_versions=software_versions
        )