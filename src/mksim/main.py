import grpc
from concurrent import futures
import time

from external.minknow_api.python.minknow_api import manager_pb2
from external.minknow_api.python.minknow_api import manager_pb2_grpc
from external.minknow_api.python.minknow_api import instance_pb2
from external.minknow_api.python.minknow_api import instance_pb2_grpc
from external.minknow_api.python.minknow_api import data_pb2
from external.minknow_api.python.minknow_api import data_pb2_grpc

class ManagerService(manager_pb2_grpc.ManagerServiceServicer):
    def get_version_info(self, request, context):
        return instance_pb2.GetVersionInfoResponse(
            minknow=instance_pb2.GetVersionInfoResponse.MinknowVersion(5, 4, 3, "5.4.3"),
            distribution_version="unknown",
            bream="1.2.3",
            distribution_status=instance_pb2.GetVersionInfoResponse.DistributionStatus.STABLE,
            protocol_configuration="0.0.0",
            installation_type=instance_pb2.GetVersionInfoResponse.InstallationType.NC
        )

        # return instance.GetVersionInfoResponse(
        #     minknow=instance.GetVersionInfoResponseMinknowVersion(5, 4, 3, "5.4.3"),
        #     distribution_version="unknown",
        #     bream="1.2.3",
        #     distribution_status=instance.GetVersionInfoResponseDistributionStatus.STABLE,
        #     protocol_configuration="0.0.0",
        #     installation_type=instance.GetVersionInfoResponseInstallationType.NC
        # )

    def local_authentication_token_path(self, request, context):
        return manager_pb2.LocalAuthenticationTokenPathResponse("/opt/ont/minknow/conf/rpc-certs/token")
        # return manager.LocalAuthenticationTokenPathResponse("/opt/ont/minknow/conf/rpc-certs/token")


class InstanceService(instance_pb2_grpc.InstanceServiceServicer):
    def get_version_info(self, request, context):
        return instance_pb2.GetVersionInfoResponse(
            minknow=instance_pb2.GetVersionInfoResponseMinknowVersion(5, 4, 3, "5.4.3"),
            distribution_version="unknown",
            bream="1.2.3",
            distribution_status=instance_pb2.GetVersionInfoResponseDistributionStatus.STABLE,
            protocol_configuration="0.0.0",
            installation_type=instance_pb2.GetVersionInfoResponseInstallationType.NC
        )


class DataService(data_pb2_grpc.DataServiceServicer):
    def get_live_reads(self, request_iterator, context):
        pass

    def get_data_types(self, request, context):
        pass


# Start the gRPC server
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    manager_pb2_grpc.add_ManagerServiceServicer_to_server(ManagerService(), server)
    instance_pb2_grpc.add_InstanceServiceServicer_to_server(InstanceService(), server)
    data_pb2_grpc.add_DataServiceServicer_to_server(DataService(), server)

    server.add_insecure_port("[::]:50051")  # Change this to 9501 if replacing MinKNOW
    print("MinKNOW API Server started on port 50051...")
    server.start()

    try:
        while True:
            time.sleep(86400)  # Keep running
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.stop(0)

if __name__ == "__main__":
    serve()
