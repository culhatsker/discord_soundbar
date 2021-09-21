
import os
import asyncio

from discord.ext import commands

from discord_soundbar.player_commands import MusicPlayerCommands


DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if DISCORD_BOT_TOKEN is None:
    print("Specify DISCORD_BOT_TOKEN environment variable to run this bot.")
    exit(-1)


async def main():
    bot = commands.Bot(command_prefix=commands.when_mentioned_or("%"),
        description='Music Bot')

    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user} (ID: {bot.user.id})')
        print('------')

    bot.add_cog(MusicPlayerCommands(bot))

    try:
        await bot.start(DISCORD_BOT_TOKEN)
    finally:
        if not bot.is_closed():
            await bot.close()

asyncio.get_event_loop().run_until_complete(main())
