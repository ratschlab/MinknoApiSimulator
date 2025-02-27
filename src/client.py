import ssl

import grpc

from minknow_api import Connection
from credentials import *
from minknow_api import manager_service

def main():
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
