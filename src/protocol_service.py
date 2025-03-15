from prelude import *
from minknow_api import protocol_pb2, protocol_pb2_grpc

class ProtocolService(protocol_pb2_grpc.ProtocolServiceServicer):
    def get_run_info(self, request, context):
        info("protocol: get_run_info")
        return protocol_pb2.ProtocolRunInfo(
            run_id = "test_run",
            software_versions = protocol_pb2.GetVersionInfoResponse(
                minknow=protocol_pb2.GetVersionInfoResponse.MinknowVersion(
                    major=6, minor=0, patch=0, full="6.0.0"
                ),
                bream="8.2.5",
                distribution_version="6.0.0",
                basecaller_build_version="7.4.12+0e5e75c49",
                basecaller_connected_version="7.4.12+0e5e75c49"
            )
        )

    def get_current_protocol_run(self, request, context):
        # info("protocol: get_current_protocol_run")
        return protocol_pb2.ProtocolRunInfo(
            run_id = "test_run",
            output_path = "/home/sayan/PyCharmProjects/MinknoApiSimulator/simout",
            state = protocol_pb2.ProtocolState.PROTOCOL_RUNNING,
            phase = protocol_pb2.ProtocolPhase.PHASE_SEQUENCING,
            software_versions=protocol_pb2.GetVersionInfoResponse(
                minknow=protocol_pb2.GetVersionInfoResponse.MinknowVersion(
                    major=6, minor=0, patch=0, full="6.0.0"
                ),
                bream="8.2.5",
                distribution_version="6.0.0",
                basecaller_build_version="7.4.12+0e5e75c49",
                basecaller_connected_version="7.4.12+0e5e75c49"
            )
        )