import asyncio
import ssl
from grpclib.client import Channel
from lib.minknow_api import manager


async def main():
    print(ssl.OPENSSL_VERSION)
    # Load client certificate and private key
    # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    # ssl_context.load_cert_chain("certs/client.pem", "certs/client.key")  # Client's certificate
    # ssl_context.load_verify_locations("certs/ca.pem")  # Trust only our CA
    # ssl_context.load_verify_locations("certs/server.crt")

    ctx = ssl.create_default_context(cafile="certs/server.pem")
    ctx.load_cert_chain("certs/client.pem", "certs/client.key")
    # ctx.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20')
    ctx.set_alpn_protocols(['h2'])

    channel = Channel(host="localhost", port=50051, ssl=ctx)
    manager_service = manager.ManagerServiceStub(channel)
    response = await manager_service.get_version_info(manager.GetVersionInfoRequest())
    print(response)
    response = await manager_service.local_authentication_token_path(manager.LocalAuthenticationTokenPathRequest())
    print(response)

    channel.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())