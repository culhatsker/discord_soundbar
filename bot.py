
import os
import asyncio
from typing import Dict, List

import discord
from discord.ext import commands
from discord.ext.commands.context import Context

from player import MusicPlayerQueue, AudioSource, AudioTrackInfo
from views import render_queue, render_volume, render_error


DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if DISCORD_BOT_TOKEN is None:
    print("Specify DISCORD_BOT_TOKEN environment variable to run this bot.")
    exit(-1)


class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._sessions: Dict[discord.Guild, MusicPlayerQueue] = {}

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, query):
        """Plays music from different sources"""

        new_session = False
        try:
            session = self._sessions[ctx.guild]
        except KeyError:
            session = MusicPlayerQueue()
            self._sessions[ctx.guild] = session
            new_session = True
        try:
            new_items: List[AudioTrackInfo] = list(
                await AudioSource.from_query(query))
        except Exception as error:
            await ctx.send(embed=render_error(error))
            return
        for queue_item in new_items:
            queue_item.user = ctx.message.author
        session.add_to_queue(new_items)
        if new_session:
            await self.play_session(ctx)
    
    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        queue_info: List[AudioTrackInfo] = await asyncio.gather(*[
            queue_item.track_info
            for queue_item in self._sessions[ctx.guild].queue
        ])
        await ctx.send(embed=render_queue(queue_info))

    @commands.command(aliases=["s"])
    async def skip(self, ctx):
        ctx.voice_client.stop()

    @commands.command(aliases=["vol", "v"])
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(embed=render_volume(volume))

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        ctx.voice_client.stop()

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")

    @staticmethod
    async def wait_for_value(func, timeout, check_interval=0.1):
        max_iterations = timeout / check_interval
        iterations = 0
        while True:
            value = func()
            if value is not None:
                return value
            iterations += 1
            if iterations >= max_iterations:
                raise TimeoutError
            await asyncio.sleep(check_interval)

    async def play_session(self, ctx):
        try:
            session = self._sessions[ctx.guild]
            return await self._play_session(ctx, session)
        except Exception as error:
            await ctx.send(embed=render_error(error))
        finally:
            await ctx.voice_client.disconnect()
            del self._sessions[ctx.guild]

    async def _play_session(self, ctx: Context, session):
        while True:
            try:
                current_track = await self.wait_for_value(
                    session.next_track, timeout=5*60)
            except TimeoutError:
                await ctx.send("Bye, bitch. Call me again if you need more music.")
                return
            try:
                audio_source = current_track.get_audio_source()
                track_info = await current_track.track_info
                await ctx.send(f"Currently playing: {str(track_info)}")
                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()
                ctx.voice_client.play(audio_source,
                    after=lambda err: err and print(f"Player error: {err}"))
            except Exception as error:
                await ctx.send(embed=render_error(error))
                continue
            while True:
                if ctx.voice_client is None:
                    # actually it's an error
                    return
                if not ctx.voice_client.is_playing():
                    break
                await asyncio.sleep(0.1)


bot = commands.Bot(command_prefix=commands.when_mentioned_or("%"),
    description='Music Bot')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

bot.add_cog(MusicCommands(bot))
bot.run(DISCORD_BOT_TOKEN)
