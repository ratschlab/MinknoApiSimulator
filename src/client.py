import ssl

import grpc

from minknow_api import Connection
from credentials import *
from minknow_api import manager_service

def main():
    # ssl_creds = grpc.ssl_channel_credentials(
    #     root_certificates=load_credential_from_file(SERVER_CERT_FILE),
    #     private_key=load_credential_from_file(CLIENT_KEY_FILE),
    #     certificate_chain=load_credential_from_file(CLIENT_CERT_FILE),
    # )
    #
    # GRPC_CHANNEL_OPTIONS = [
    #     ("grpc.max_send_message_length", 16 * 1024 * 1024),
    #     ("grpc.max_receive_message_length", 16 * 1024 * 1024),
    #     ("grpc.http2.min_time_between_pings_ms", 1000),
    #     (
    #         "grpc.ssl_target_name_override",
    #         "localhost",
    #     ),  # that's what our cert's CN is
    # ]
    #
    # channel = grpc.secure_channel("localhost:50051", ssl_creds, GRPC_CHANNEL_OPTIONS)
    # manager = manager_service.ManagerService(channel)
    # response = manager.get_version_info()
    # print(response)

    try:
        c = Connection(host='localhost', port=50051,
                       client_certificate_chain=load_credential_from_file(CLIENT_CERT_FILE),
                       client_private_key=load_credential_from_file(CLIENT_KEY_FILE)
                       )
        print('Connection established')
        print(c.device.get_flow_cell_info().channel_count)
    except grpc.RpcError as e:
        print("Error connecting to server: %s" % e)



if __name__ == "__main__":
    main()
