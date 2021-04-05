from .polocounter import PoloCounter

def setup(bot):
    cog = PoloCounter(bot)
    bot.add_cog(cog)
    cog._initialize()
