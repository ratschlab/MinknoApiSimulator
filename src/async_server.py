import asyncio
import ssl
from grpclib.server import Server

from lib.minknow_api import manager, instance


class ManagerService(manager.ManagerServiceBase):
    async def get_version_info(
        self, get_version_info_request: "GetVersionInfoRequest"
    ) -> "_instance__.GetVersionInfoResponse":
        return instance.GetVersionInfoResponse(
            minknow=instance.GetVersionInfoResponseMinknowVersion(5, 4, 3, "5.4.3"),
            distribution_version="unknown",
            bream="1.2.3",
            distribution_status=instance.GetVersionInfoResponseDistributionStatus.STABLE,
            protocol_configuration="0.0.0",
            installation_type=instance.GetVersionInfoResponseInstallationType.NC
        )

    async def local_authentication_token_path(
        self,
        local_authentication_token_path_request: "LocalAuthenticationTokenPathRequest",
    ) -> "LocalAuthenticationTokenPathResponse":
        return manager.LocalAuthenticationTokenPathResponse("/opt/ont/minknow/conf/rpc-certs/token")


# Start the gRPC server
async def serve():
    # print(ssl.OPENSSL_VERSION)
    # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # ssl_context.load_cert_chain("certs/server.pem", "certs/server.key")  # Server's certificate
    # ssl_context.load_verify_locations("./certs/rootCA.crt")  # Trust only our CA
    # ssl_context.verify_mode = ssl.CERT_REQUIRED  # Require client certificate

    ctx = ssl.create_default_context(
        ssl.Purpose.CLIENT_AUTH,
        cafile="certs/client.pem",
    )
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_cert_chain("certs/server.pem", "certs/server.key")
    # ctx.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20')
    ctx.set_alpn_protocols(['h2'])

    server = Server([ManagerService()])

    await server.start("localhost", 50051, ssl=ctx)
    print("🔒 mTLS MinKNOW API Server started on port 50051...")
    await server.wait_closed()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(serve())