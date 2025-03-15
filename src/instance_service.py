from prelude import *
from minknow_api import instance_pb2, instance_pb2_grpc

class InstanceService(instance_pb2_grpc.InstanceServiceServicer):
    def get_version_info(self, request, context):
        info("instance: get_version_info")
        return instance_pb2.GetVersionInfoResponse(
            minknow=instance_pb2.GetVersionInfoResponse.MinknowVersion(major=6, minor=0, patch=0, full="6.0.0"),
            bream="4.5.6",
            distribution_version="6.0.0",
            distribution_status=instance_pb2.GetVersionInfoResponse.DistributionStatus.STABLE,
            protocol_configuration="a.b.c",
            installation_type=instance_pb2.GetVersionInfoResponse.InstallationType.NC,
            basecaller_build_version="7.4.12+0e5e75c49",
            basecaller_connected_version="7.4.12+0e5e75c49"
        )