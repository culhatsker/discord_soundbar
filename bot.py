
import os
import asyncio

from discord.ext import commands
from discord import Intents

from discord_soundbar.player_commands import MusicPlayerCommands


DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
if DISCORD_TOKEN is None:
    print("Specify DISCORD_TOKEN environment variable to run this bot.")
    exit(-1)


async def main():
    intents = Intents.default()
    intents.message_content = True
    intents.typing = False
    intents.presences = False
    bot = commands.Bot(
        command_prefix=commands.when_mentioned_or("%"),
        description='Soundbar Music Bot',
        intents=intents)

    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user} (ID: {bot.user.id})')
        print('------')

    await bot.add_cog(MusicPlayerCommands(bot))

    try:
        await bot.start(DISCORD_TOKEN)
    finally:
        if not bot.is_closed():
            await bot.close()

asyncio.get_event_loop().run_until_complete(main())
