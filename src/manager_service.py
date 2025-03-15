from prelude import *
from minknow_api import manager_pb2, manager_pb2_grpc
from minknow_api import instance_pb2, device_pb2

class ManagerService(manager_pb2_grpc.ManagerServiceServicer):

    def get_version_info(self, request, context):
        info("manager: get_version_info")
        return instance_pb2.GetVersionInfoResponse (
            minknow=instance_pb2.GetVersionInfoResponse.MinknowVersion(major=6, minor=0, patch=0, full="6.0.0"),
            bream="4.5.6",
            distribution_version="16.0.0",
            distribution_status=instance_pb2.GetVersionInfoResponse.DistributionStatus.STABLE,
            protocol_configuration="a.b.c",
            installation_type=instance_pb2.GetVersionInfoResponse.InstallationType.NC,
            basecaller_build_version="7.4.12+0e5e75c49",
            basecaller_connected_version="7.4.12+0e5e75c49"
        )

    def flow_cell_positions(self, request, context):
        info("manager: flow_cell_positions")
        # Create a single flow cell position
        flow_cell_position = manager_pb2.FlowCellPosition(
            name="MN12345",
            location=manager_pb2.FlowCellPosition.Location(x=0, y=0),
            state=manager_pb2.FlowCellPosition.State.STATE_RUNNING,
            rpc_ports=manager_pb2.FlowCellPosition.RpcPorts(secure=50051, secure_grpc_web=50052),
            error_info="",
            is_integrated=False,
            can_sequence_offline=True,
            protocol_state=manager_pb2.SimpleProtocolState.PROTOCOL_RUNNING,
            is_simulated=True,
            device_type=device_pb2.GetDeviceInfoResponse.DeviceType.MINION,
            parent_name="MN12345",
            firmware_is_updating=False,
            has_progress=False,
            progress_percent=0,
            progress_eta_seconds=0
        )

        # Create the response with the single flow cell position
        response = manager_pb2.FlowCellPositionsResponse(
            total_count=1,
            positions=[flow_cell_position]
        )

        # Yield the response
        yield response

