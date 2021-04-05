from json.decoder import JSONDecodeError
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
import aiohttp
import discord
from typing import Optional
import asyncio
from .commands import Commands
from traceback import format_exception

BASE_URL = "https://www.googleapis.com/youtube/v3/channels?part={type}&id={id}&key={key}"
POLO8_ID = "UC3yUthlHZTZvwRjRUjrZdVw"


class Statistics:
    def __init__(self, data: dict):
        try:
            stats = data["items"][0]["statistics"]

            self.total_view = int(stats["viewCount"])
            self.subscribers = int(stats["subscriberCount"])
            self.videos = int(stats["videoCount"])
        except KeyError:
            raise ValueError("JSON infos are incorrect.")


class Brandings:
    def __init__(self, data: dict):
        try:
            settings = data["items"][0]["brandingSettings"]
            chan = settings["channel"]

            self.name = chan["title"]
            self.description = chan["description"]
            self.color = chan["profileColor"]
            self.country = chan["country"]

            self.image = settings["image"]["bannerExternalUrl"]
        except KeyError:
            raise ValueError("JSON infos are incorrect.")


def return_rgb(hex: str):
    return tuple(int(hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))


class PoloCounter(Commands, commands.Cog):
    def __init__(self, bot: Red, *args, **kwargs):
        self.bot = bot

        self.config = Config.get_conf(self, identifier=654658752265, force_registration=True)
        self.config.register_global(inchannel=None, message=None)

        self._statistics_cache = None
        self._branding_cache = None

        super().__init__(*args, **kwargs)

    @staticmethod
    def build_embed(statistics: Statistics, brandings: Brandings):
        rgb = return_rgb(brandings.color)
        embed = discord.Embed(
            title="Statistique pour {name} [{country}] :".format(
                name=brandings.name, country=brandings.country
            ),
            description=brandings.description,
            colour=discord.Colour.from_rgb(*rgb),
        )
        embed.set_image(url=brandings.image)

        embed.add_field(
            name="\N{BUST IN SILHOUETTE} Abonnés", value=str(statistics.subscribers), inline=True
        )
        embed.add_field(
            name="\N{EYE}\N{VARIATION SELECTOR-16} Vues",
            value=str(statistics.total_view),
            inline=True,
        )
        embed.add_field(
            name="\N{SLOT MACHINE} Vidéos",
            value=str(statistics.videos) + " au total.",
            inline=True,
        )
        return embed

    async def update_informations(
        self, *, fetch_stats: bool = False, fetch_branding: bool = False
    ):
        # Obtain API key
        keys = await self.bot.get_shared_api_tokens("youtube")
        if not keys.get("api_key", None):
            raise IndexError("Missing API key.")
        api_key = keys["api_key"]

        async with aiohttp.ClientSession() as session:
            # Obtain brandings
            if fetch_branding:
                brands = await self.get_raw_brandings_for(POLO8_ID, session, api_key)
            else:
                brands = None
            # Obtain statistics
            if fetch_stats:
                stats = await self.get_raw_stats_for(POLO8_ID, session, api_key)
            else:
                stats = None
        self.convert_raw(brands or self._branding_cache, stats or self._statistics_cache)
        return True

    def convert_raw(self, brandings_raw: dict, stats_raw: dict):
        if not isinstance(brandings_raw, Brandings):
            # In case we got self._branding_cache
            self._branding_cache = Brandings(brandings_raw)
        if not isinstance(stats_raw, Statistics):
            # Same as above, but with self._statistics_cache
            self._statistics_cache = Statistics(stats_raw)

    @staticmethod
    async def get_raw_brandings_for(channel_id: str, session: aiohttp.ClientSession, api_key: str):
        async with session.get(
            BASE_URL.format(type="brandingSettings", id=channel_id, key=api_key)
        ) as request:
            if request.status != 200:
                raise ValueError("Status code is not 200.")
            try:
                return await request.json()
            except JSONDecodeError:
                raise ValueError("Answer is not a JSON.")

    @staticmethod
    async def get_raw_stats_for(channel_id: str, session: aiohttp.ClientSession, api_key: str):
        async with session.get(
            BASE_URL.format(type="statistics", id=channel_id, key=api_key)
        ) as request:
            if request.status != 200:
                raise ValueError("Status code is not 200.")
            try:
                return await request.json()
            except JSONDecodeError:
                raise ValueError("Answer is not a JSON.")

    async def send_message(self, channel: discord.TextChannel) -> Optional[discord.Message]:
        await self.update_informations(
            fetch_stats=not bool(self._statistics_cache),
            fetch_branding=not bool(self._branding_cache),
        )
        try:
            message = await channel.send(
                embed=self.build_embed(self._statistics_cache, self._branding_cache)
            )
            return message
        except discord.Forbidden:
            await self.bot.send_to_owners(
                "Unable to send a message in the configured channel for PoloCounter.\nLoop "
                "closed."
            )
            return
        except discord.HTTPException as e:
            await self.bot.send_to_owners(f"Unexpected error for PoloCounter: {e}\nLoop closed.")

    async def fetch_message(
        self, channel: discord.TextChannel, message_id: int
    ) -> Optional[discord.Message]:
        try:
            message = await channel.fetch_message(message_id)
        except discord.Forbidden as e:
            await self.bot.send_to_owners(
                f"Unable to fetch message for PoloCounter: {str(e)}\nLoop closed."
            )
            return
        except discord.NotFound as original_error:
            await self.config.message.clear()
            raise original_error
        except discord.HTTPException as e:
            await self.bot.send_to_owners(f"Unexpected error for PoloCounter: {e}\nLoop closed.")
            return
        return message

    async def _update_loop(self):
        await self.bot.wait_until_red_ready()
        try:
            testing = self.bot.get_channel(828084078321467412)
            config = await self.config.all()
            channel = self.bot.get_channel(config["inchannel"])
            await testing.send("LOOP DEMAREE, ENVOIE/MISE A JOUR DU PREMIER MESSAGE")
            if channel is None:
                await self.bot.send_to_owners(
                    "The channel for PoloCounter is not set, please set one in order to allow "
                    "the loop to run."
                )
                return

            # Obtention du message
            if config["message"]:
                await testing.send("MESSAGE TROUVE, RECUPERATION")
                try:
                    message = await self.fetch_message(channel, config["message"])
                except discord.NotFound:
                    message = await self.send_message(channel)
                    if not message:
                        return
                    await testing.send("MISE A JOUR CONFIG")
                    await self.config.message.set(message.id)
                if not message:
                    return

            # On le crée si il ne l'étais pas
            else:
                await testing.send("AUCUN MESSAGE TROUVE, CREATION")
                message = await self.send_message(channel)
                if not message:
                    return
                else:
                    await self.config.message.set(message.id)

            # At this point, we should have obtained the message.
            while True:
                try:
                    await testing.send("MISE A JOUR EN COURS")
                    await self.update_informations(
                        fetch_stats=not bool(self._statistics_cache),
                        fetch_branding=not bool(self._branding_cache),
                    )
                    await testing.send("EDITION DU MESSAGE")
                    embed = self.build_embed(self._statistics_cache, self._branding_cache)
                    await message.edit(
                        content=None, embed=embed
                    )
                except discord.Forbidden:
                    await self.bot.send_to_owners(
                        "Unable to edit message in the configured channel for PoloCounter.\nLoop "
                        "closed."
                    )
                    return
                except discord.HTTPException as e:
                    await self.bot.send_to_owners(
                        f"Unexpected error for PoloCounter: {e}\nLoop still running."
                    )
                await testing.send("LE MESSAGE SEMBLE EDITE")
                await asyncio.sleep(21600)  # See you in 6 hours!
        except Exception as e:
            await self.bot.send_to_owners(
                box(str("".join(format_exception(type(e),e, e.__traceback__))), lang='python')
            )
            return

    async def _clean_loop(self):
        await self.bot.wait_until_red_ready()
        testing = self.bot.get_channel(828084078321467412)
        while True:
            await asyncio.sleep(21600)
            self._statistics_cache = None
            self._branding_cache = None
            await testing.send("CACHES SUPPRIME")

    def cog_unload(self):
        for task in asyncio.all_tasks():
            if task.get_name() in ("Polo8: Cleaner", "Polo8: Updater"):
                task.cancel()

    def _initialize(self):
        self.bot.loop.create_task(self._clean_loop(), name="Polo8: Cleaner")
        self.bot.loop.create_task(self._update_loop(), name="Polo8: Updater")
