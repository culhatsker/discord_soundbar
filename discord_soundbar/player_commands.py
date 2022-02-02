import asyncio
import traceback
from typing import Dict, List
from functools import wraps

import discord
from discord.ext import commands

from discord_soundbar.audio_source import AudioTrack

from .music_player import MusicPlayerState
from .views import render_queue, render_error


def user_is_listener(f):
    @wraps(f)
    async def _new_f(self, ctx, *args, **kwargs):
        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel to use this command")
            return
        return await f(self, ctx, *args, **kwargs)
    return _new_f


def session_exists(f):
    @wraps(f)
    async def _new_f(self, ctx, *args, **kwargs):
        try:
            session = self._sessions[ctx.guild]
        except KeyError:
            await ctx.send("Nothing is playing")
            return
        return await f(self, ctx, session, *args, **kwargs)
    return _new_f


class MusicPlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._sessions: Dict[discord.Guild, MusicPlayerState] = {}

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Join a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, query):
        """Play music from different sources"""
        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel to use this command")
            return
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        try:
            new_tracks = await AudioTrack.from_query(query)
        except Exception as ex:
            await ctx.send(embed=render_error(repr(ex)))
        try:
            session = self._sessions[ctx.guild]
            if not session.active:
                raise KeyError
        except KeyError:
            session = MusicPlayerState(ctx)
            self._sessions[ctx.guild] = session
            session.play_session()
        session.add(new_tracks)
    
    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        """Show tracks in queue"""
        try:
            session = self._sessions[ctx.guild]
            if not session.active:
                raise KeyError
            await ctx.send(embed=render_queue(session.items, title="Next up..."))
        except KeyError:
            await ctx.send("Nothing is playing")

    @commands.command()
    async def skip(self, ctx):
        """Skip current track, start next one"""
        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel to use this command")
            return
        try:
            session = self._sessions[ctx.guild]
        except KeyError:
            await ctx.send("Nothing is playing")
            return
        session.skip()

    @commands.command(aliases=["s"])
    async def seek(self, ctx, position: str):
        """Seek (fast forward) to a given position"""
        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel to use this command")
            return
        try:
            session = self._sessions[ctx.guild]
        except KeyError:
            await ctx.send("Nothing is playing")
            return
        # position = parse_timedelta(position)
        session.seek(position)

    @commands.command(aliases=["vol", "v"])
    async def volume(self, ctx, volume: int):
        """Changes global player volume"""
        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel to use this command")
            return
        try:
            session = self._sessions[ctx.guild]
        except KeyError:
            await ctx.send("Nothing is playing")
            return
        session.volume(volume)

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel to use this command")
            return
        try:
            session = self._sessions[ctx.guild]
            if not session.active:
                raise KeyError
            session.stop()
        except KeyError:
            await ctx.send("Nothing is playing")

