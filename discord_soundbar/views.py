from typing import List

from discord import Embed

from discord_soundbar.queue import QueueItem


BRAND_COLOR = 0xe291d6


def render_track(track_info, title="New track"):
    return Embed(title=title, description=f"**{track_info.title}** "
        f"by **{track_info.artist}** ({track_info.str_duration}) "
        f"added by **{track_info.user_tag}**", color=BRAND_COLOR)


def render_queue(queue_info: List[QueueItem], title="New tracks") -> Embed:
    if not queue_info:
        return Embed(title="No songs in the queue.")
    description = '\n'.join(
        f'♫ **{i.title}** by **{i.artist}** ({i.str_duration}) added by **{i.user_tag}**'
        for i in queue_info
    )
    return Embed(title=title,
        description=description, color=BRAND_COLOR)


def render_volume(volume: int) -> Embed:
    return Embed(title=f'Volume changed to {volume}', color=BRAND_COLOR)


def render_error(traceback_str: str) -> Embed:
    return Embed(description="Player got an unexpected error: \n"
        f"```{traceback_str}```")
