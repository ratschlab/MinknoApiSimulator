import asyncio
from grpclib.client import Channel
from lib.minknow_api import manager


async def main():
    channel = Channel(host="127.0.0.1", port=50051)
    manager_service = manager.ManagerServiceStub(channel)
    response = await manager_service.get_version_info(manager.GetVersionInfoRequest())
    print(response)
    response = await manager_service.local_authentication_token_path(manager.LocalAuthenticationTokenPathRequest())
    print(response)

    channel.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())