import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

import discord
from discord.ext import commands

async def main() -> None:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix=os.getenv("BOT_PREFIX", "!"), intents=intents)

    @bot.event
    async def on_ready() -> None:
        print(f"Logged in as {bot.user} ({bot.user.id})")

    await bot.load_extension("cogs.announcements")

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is not set")

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
