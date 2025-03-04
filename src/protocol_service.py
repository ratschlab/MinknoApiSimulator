from prelude import *
from minknow_api import protocol_pb2, protocol_pb2_grpc

class ProtocolService(protocol_pb2_grpc.ProtocolServiceServicer):
    def get_run_info(self, request, context):
        info("protocol: get_run_info")
        return protocol_pb2.ProtocolRunInfo(
            run_id = "test_run"
        )

    def get_current_protocol_run(self, request, context):
        # info("protocol: get_current_protocol_run")
        return protocol_pb2.ProtocolRunInfo(
            run_id = "test_run",
            output_path = "/home/sayan/PyCharmProjects/MinknoApiSimulator/simout",
            state = protocol_pb2.ProtocolState.PROTOCOL_RUNNING,
            phase = protocol_pb2.ProtocolPhase.PHASE_SEQUENCING,
        )