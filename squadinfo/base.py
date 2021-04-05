from discord import Colour, Embed
from redbot.core import commands
from redbot.core.bot import Red

from .api import BattleNetAPI


class SquadInfo(commands.Cog):
    def __init__(self, bot: Red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot: Red = bot
        self.api = None

    @commands.group(name="squadinfo")
    async def squad(self, ctx: commands.GuildContext):
        """Des informations pour les serveurs français de Squad!"""
        pass

    @squad.command(aliases=["jsfr"])
    async def joinsquadfr(self, ctx: commands.Context):
        """Obtiens des informations sur le serveur Joinsquad.fr!"""
        try:
            await self.prepare_api()
        except AttributeError:
            return await ctx.send("Il me manque la clé d'API!")
        await ctx.send(embed=await self.get_embed(await self.return_server(2509807)))

    @squad.command()
    async def p2(self, ctx: commands.Context):
        """Obtiens des informations sur le serveur P²!"""
        try:
            await self.prepare_api()
        except AttributeError:
            return await ctx.send("Il me manque la clé d'API!")
        await ctx.send(embed=await self.get_embed(await self.return_server(3599487)))

    @squad.command()
    async def ffa1(self, ctx: commands.Context):
        """Obtiens des informations sur le serveur FFA1!"""
        try:
            await self.prepare_api()
        except AttributeError:
            return await ctx.send("Il me manque la clé d'API!")
        await ctx.send(embed=await self.get_embed(await self.return_server(9324028)))

    @squad.command()
    async def ffa2(self, ctx: commands.Context):
        """Obtiens des informations sur le serveur FFA2!"""
        try:
            await self.prepare_api()
        except AttributeError:
            return await ctx.send("Il me manque la clé d'API!")
        await ctx.send(embed=await self.get_embed(await self.return_server(9231088)))

    @squad.command()
    async def id(self, ctx: commands.Context, id_serveur: int):
        """Obtenez l'état d'un serveur par son ID.

        Pour obtenir l'ID d'un serveur:

        1. Chercher le serveur sur battlemetrics.
        2. Récupérer la suite de nombre dans l'URL.
        """
        try:
            await self.prepare_api()
        except AttributeError:
            return await ctx.send("Il me manque la clé d'API!")
        await ctx.send(embed=await self.get_embed(await self.return_server(id_serveur)))

    async def prepare_api(self):
        if not self.api:
            keys = await self.bot.get_shared_api_tokens("battlemetrics")
            if apikey := keys.get("api_key", None) is None:
                raise AttributeError("Missing API key.")
            self.api = BattleNetAPI(apikey)

    async def return_server(self, server_id: int):
        return await self.api.obtain_server_info(server_id)

    @staticmethod
    async def get_embed(informations: dict):
        info = informations["data"]["attributes"]
        embed = Embed(
            title=info.get("name", "Introuvable"),
            color=Colour.from_rgb(0, 0, 0),
            description=f"Rang du serveur: {info.get('rank', 'Introuvable')}",
        )
        embed.add_field(
            name="Joueurs en ligne:",
            value=f"{info.get('players', 'Introuvable')} / {info.get('maxPlayers', 'Introuvable')}",
        )
        details = info.get("details", None)
        if details:
            embed.add_field(
                name="Map en cours:",
                value=details.get("map", "Introuvable").replace("_", " "),
            )
            embed.add_field(name="Mode:", value=details.get("gameMode", "Introuvable"))
            embed.add_field(name="Version:", value=details.get("version", "Introuvable"))
        embed.set_footer(
            text=f"Status: {'En ligne' if info.get('status', None) == 'online' else info['status']}"
        )
        return embed
