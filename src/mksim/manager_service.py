from minknow_api import manager_pb2, manager_pb2_grpc
from minknow_api import device_pb2

from instance_service import get_instance_version_info
import config

class ManagerService(manager_pb2_grpc.ManagerServiceServicer):

    def get_version_info(self, request, context):
        return get_instance_version_info()

    def flow_cell_positions(self, request, context):
        # Create a single flow cell position
        flow_cell_position = manager_pb2.FlowCellPosition(
            name=config.params.name,
            location=manager_pb2.FlowCellPosition.Location(x=0, y=0),
            state=manager_pb2.FlowCellPosition.State.STATE_RUNNING,
            rpc_ports=manager_pb2.FlowCellPosition.RpcPorts(secure=config.params.port, secure_grpc_web=config.params.port + 1),
            error_info="",
            is_integrated=False,
            can_sequence_offline=True,
            protocol_state=manager_pb2.SimpleProtocolState.PROTOCOL_RUNNING,
            is_simulated=True,
            device_type=device_pb2.GetDeviceInfoResponse.DeviceType.MINION,
            parent_name=config.params.name,
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

