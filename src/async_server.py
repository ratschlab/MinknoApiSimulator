import asyncio
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
    server = Server([ManagerService()])

    await server.start("localhost", 50051)
    print("Listening on http://localhost:50051/")
    await server.wait_closed()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(serve())