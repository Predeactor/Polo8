from .base import SquadInfo


def setup(bot):
    cog = SquadInfo(bot)
    bot.add_cog(cog)
