import asyncio
import traceback
from typing import Dict, List

import discord
from discord.ext import commands
from discord.ext.commands.context import Context

from .queue import MusicPlayerQueue, QueueItem
from .views import render_queue, render_volume, render_error, render_track


class MusicPlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._sessions: Dict[discord.Guild, MusicPlayerQueue] = {}

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Join a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command(aliases=["p", "elvinplay", "ep"])
    async def play(self, ctx, *, query):
        """Play music from different sources"""

        elvinmode = ctx.invoked_with in ["elvinplay", "ep"]

        new_session = False
        try:
            session = self._sessions[ctx.guild]
        except KeyError:
            session = MusicPlayerQueue()
            self._sessions[ctx.guild] = session
            new_session = True

        try:
            new_items: List[QueueItem] = await QueueItem.from_query(
                query, user_tag=ctx.message.author.name, elvin=elvinmode)
            if new_items and len(new_items) > 1:
                # render new items if playlist
                await ctx.send(embed=render_queue(new_items))
        except Exception as error:
            traceback.print_exc()
            await ctx.send(embed=render_error(repr(error)))
            return
        session.add(new_items)
        await ctx.message.add_reaction("👍")
        if new_session:
            await self.play_session(ctx)
    
    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        """Show tracks in queue"""
        await ctx.send(embed=render_queue(
            self._sessions[ctx.guild].queue, title="Next up..."))

    @commands.command()
    async def skip(self, ctx):
        """Skip current track, start next one"""
        ctx.voice_client.stop()

    @commands.command(aliases=["s"])
    async def seek(self, ctx, position: str):
        """Seek (fast forward) to a given position"""
        try:
            parts = list(map(int, position.strip().split(":")))
        except Exception:
            await ctx.send("Invalid position format: either put "
                "number of seconds (e.g. `260`) or position "
                "in format mm:ss or hh:mm:ss (e.g. `10:02`)")
            return
        try:
            session = self._sessions[ctx.guild]
            session.seek_position = ":".join(map(str, parts))
        except KeyError:
            await ctx.send("Nothing is playing")

    @commands.command(aliases=["vol", "v"])
    async def volume(self, ctx, volume: int):
        """Changes global player volume"""

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
            traceback.print_exc()
            await ctx.send(embed=render_error(repr(error)))
        finally:
            await ctx.voice_client.disconnect()
            del self._sessions[ctx.guild]

    async def _play_session(self, ctx: Context, session):
        after_play = lambda err: err and print(f"Player error: {err}")
        while True:
            try:
                current_track: QueueItem = await self.wait_for_value(
                    session.pop_track, timeout=5*60)
            except TimeoutError:
                await ctx.send("Bye, bitch. Call me again if you need more music.")
                return
            try:
                if current_track.position:
                    seek_to=current_track.position.total_seconds()
                else:
                    seek_to=None
                pcm_audio = await current_track.get_playable_source(seek_to=seek_to)
                await ctx.send(embed=render_track(current_track, title="Now playing"))
                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()
                ctx.voice_client.play(pcm_audio, after=after_play)
            except Exception as error:
                traceback.print_exc()
                await ctx.send(embed=render_error(repr(error)))
                continue
            while True:
                if ctx.voice_client is None:
                    # actually it's an error
                    return
                if not ctx.voice_client.is_playing():
                    break
                if session.seek_position:
                    ctx.voice_client.stop()
                    ctx.voice_client.play(
                        await current_track.get_playable_source(
                            seek_to=session.seek_position, cached=True),
                        after=after_play
                    )
                    session.seek_position = None
                await asyncio.sleep(0.1)
