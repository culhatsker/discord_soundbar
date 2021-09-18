import traceback
from typing import List

import discord

from player import AudioTrackInfo


def render_queue(queue_info: List[AudioTrackInfo]) -> discord.Embed:
    description = '\n'.join(f'♫ {track.title} by {track.artist} ({track.duration}) added by {track.user.name}' for track in queue_info)
    embed = discord.Embed(title='Next up...', description=description, color=0xba2a0d)
    return embed


def render_volume(volume: int) -> discord.Embed:
    embed = discord.Embed(title='Volume changed', description=f"It is now {volume}", color=0xba2a0d)
    return embed


def render_error(error: BaseException) -> discord.Embed:
    return discord.Embed(description="Player got an unexpected error: \n"
        f"```{traceback.format_exc(error)}```")
