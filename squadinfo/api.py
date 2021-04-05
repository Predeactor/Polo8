import aiohttp

BASE_URL = "https://api.battlemetrics.com"

HEADERS = {"Authorization": None}


class BattleNetAPI:
    def __init__(self, api_key: str):
        self.api_key: str = str(api_key)
        self.headers: dict = {"Authorization": self.api_key}

    async def obtain_server_info(self, server_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                BASE_URL + f"/servers/{str(server_id)}", headers=self.headers
            ) as response:
                return await response.json()
