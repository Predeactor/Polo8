import discord

from redbot.core import commands


class Commands:
    
    @commands.group(name="polocounter")
    @commands.cooldown(3600, 1, commands.BucketType.default)
    async def pc(self, ctx: commands.Context):
        pass

    @pc.command()
    @commands.admin_or_permissions(manage_channels=True)
    async def setchannel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """
        Définit un salon où envoyer le message de résumé de la chaîne.

        Ne donner aucun salon désactivera le système.
        """
        if not channel:
            await self.config.inchannel.clear()
            await ctx.send("Deleted.")
            return
        await self.config.inchannel.set(channel.id)
        await ctx.tick()

    @pc.command()
    @commands.cooldown(3600, 1, commands.BucketType.default)
    async def get(self, ctx: commands.Context):
        # Un message sympa
        await self.update_informations(
            fetch_stats=not bool(self._statistics_cache),
            fetch_branding=not bool(self._branding_cache),
        )

        await ctx.send(
            embed=self.build_embed(self._statistics_cache, self._branding_cache)
        )
