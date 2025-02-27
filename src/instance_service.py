from prelude import *
from minknow_api import instance_pb2, instance_pb2_grpc

class InstanceService(instance_pb2_grpc.InstanceServiceServicer):
    def get_version_info(self, request, context):
        info("instance: get_version_info")
        return instance_pb2.GetVersionInfoResponse(
            minknow=instance_pb2.GetVersionInfoResponse.MinknowVersion(major=1, minor=2, patch=3, full="1.2.3"),
            bream="4.5.6",
            distribution_version="1.2.3",
            distribution_status=instance_pb2.GetVersionInfoResponse.DistributionStatus.STABLE,
            protocol_configuration="a.b.c",
            installation_type=instance_pb2.GetVersionInfoResponse.InstallationType.NC
        )