import grpc
from concurrent import futures
from credentials import *
from manager_service import *
from instance_service import *
from acquisition_service import *
from analysis_configuration_service import *
from data_service import *
from device_service import *
from protocol_service import *
from log_service import *
import config

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add the service implementation to the server
    sequencer = Sequencer()
    manager_pb2_grpc.add_ManagerServiceServicer_to_server(ManagerService(), server)
    instance_pb2_grpc.add_InstanceServiceServicer_to_server(InstanceService(), server)
    acquisition_pb2_grpc.add_AcquisitionServiceServicer_to_server(AcquisitionService(sequencer), server)
    analysis_configuration_pb2_grpc.add_AnalysisConfigurationServiceServicer_to_server(AnalysisConfigurationService(), server)
    data_pb2_grpc.add_DataServiceServicer_to_server(DataService(sequencer), server)
    device_pb2_grpc.add_DeviceServiceServicer_to_server(DeviceService(), server)
    protocol_pb2_grpc.add_ProtocolServiceServicer_to_server(ProtocolService(), server)
    log_pb2_grpc.add_LogServiceServicer_to_server(LogService(), server)

    # Load SSL credentials
    server_credentials = grpc.ssl_server_credentials([
        (load_credential_from_file(SERVER_KEY_FILE), load_credential_from_file(SERVER_CERT_FILE))
    ])

    # Bind the server to a secure port
    server.add_secure_port("localhost:50051", server_credentials)

    # Start the server
    server.start()
    print("Sync gRPC server is running on port 50051...")

    # Thread to watch for stop signal
    def monitor_stop():
        config.stop_event.wait()  # blocks until stop_event.set() is called
        Log.info("Stop signal received, shutting down...")
        server.stop(grace=5).wait()  # <— Gracefully stop

    threading.Thread(target=monitor_stop, daemon=True).start()

    # Keep the server running indefinitely
    server.wait_for_termination()
    Log.info("Server stopped.")


if __name__ == "__main__":
    config.get_params()
    serve()