from typing import List

import discord

from .audio_source import AudioTrack


BRAND_COLOR = 0xe291d6


def render_track(track_info, title="New track"):
    return discord.Embed(title=title, description=f"**{track_info.title}** "
        f"by **{track_info.artist}** ({track_info.str_duration}) "
        f"added by **{track_info.user_tag}**", color=BRAND_COLOR)


def render_queue(queue_info: List[AudioTrack], title="New tracks") -> discord.Embed:
    description = '\n'.join(
        f'♫ **{i.title}** by **{i.artist}** ({i.duration}) added by **{i.usertag}**'
        for i in queue_info
    )
    return discord.Embed(title=title,
        description=description, color=BRAND_COLOR)


def render_volume(volume: int) -> discord.Embed:
    return discord.Embed(title=f'Volume changed to {volume}', color=BRAND_COLOR)


def render_error(traceback_str: str) -> discord.Embed:
    return discord.Embed(description="Player got an unexpected error: \n"
        f"```{traceback_str}```")
