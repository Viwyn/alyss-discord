import discord
from discord.ext import commands, tasks

class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        
    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        """Responds with Pong! and the bot's latency."""
        latency = self.bot.latency * 1000 
        await ctx.send(f"Pong! Latency: {latency:.2f} ms")
    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ping(bot))