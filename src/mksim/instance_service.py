
from minknow_api import instance_pb2, instance_pb2_grpc
from . import config

def get_instance_version_info():
    version_info_response = config.other_version_info
    version_info_response['minknow'] = instance_pb2.GetVersionInfoResponse.MinknowVersion(**config.minknow_version_info)
    return instance_pb2.GetVersionInfoResponse(**version_info_response)

class InstanceService(instance_pb2_grpc.InstanceServiceServicer):
    def get_version_info(self, request, context):
        return get_instance_version_info()
