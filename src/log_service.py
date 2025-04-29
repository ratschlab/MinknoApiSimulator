
from minknow_api import log_pb2, log_pb2_grpc

class LogService(log_pb2_grpc.LogServiceServicer):
    def send_user_message(self, request, context):
        return log_pb2.SendUserMessageResponse()