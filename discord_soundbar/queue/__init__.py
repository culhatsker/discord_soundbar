from typing import List

from datetime import timedelta
from dataclasses import dataclass, asdict
from json import dumps, loads

from aiohttp import request
from discord import FFmpegPCMAudio, PCMVolumeTransformer

from .providers import Provider, FileProvider, YTDLProvider


SEARCH_PROVIDER = YTDLProvider

QUEUE_PROVIDERS = {
    "ytdl": YTDLProvider,
    "file": FileProvider
}


async def get_mime_type_of_url(url):
    async with request("HEAD", url) as response:
        content_type = response.headers.get("Content-Type")
        if content_type:
            return content_type.split(";")[0]
        return None


def get_ffaudio_from_streaming_url(streaming_url, volume, seek_to):
    before_options = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
    if seek_to:
        before_options += " -ss " + seek_to
    ffaudio = FFmpegPCMAudio(
        streaming_url,
        options="-vn",
        before_options=before_options
    )
    ffaudio = PCMVolumeTransformer(ffaudio, volume=volume)
    ffaudio.url = streaming_url
    return ffaudio


@dataclass
class QueueItem:
    provider_name: str

    # these are fields filled by Provider
    query: str
    artist: str
    title: str
    duration: timedelta
    # ----

    user_tag: str = None

    @staticmethod
    async def from_query(query, user_tag=None) -> "QueueItem":
        query = query.strip()
        provider = None
        if not (query.startswith("https://") or query.startswith("http://")):
            # Not an url -> trying to search it on YouTube
            query, provider = await SEARCH_PROVIDER.transform_search_query(query)

        if not provider:
            mime_type = await get_mime_type_of_url(query)
            if mime_type.split("/")[0] in {"video", "audio"}:
                # Url points to a video/audio file -> playing it
                provider = FileProvider
            else:
                # Url is something else -> trying to resolve it via YTDL
                provider = YTDLProvider
        return [
            QueueItem(
                provider_name=provider.name,
                user_tag=user_tag,
                **qinfo
            )
            for qinfo in await provider.from_query(query)
        ]
    
    @property
    def serialized(self) -> str:
        d = asdict(self)
        d.duration = d.duration.total_seconds()
        return dumps(d)
    
    @staticmethod
    def from_serialised(s) -> "QueueItem":
        d = loads(s)
        d.duration = timedelta(seconds=d.duration)
        return QueueItem(**d)

    @property
    def provider(self) -> Provider:
        return QUEUE_PROVIDERS[self.provider_name]

    async def get_playable_source(self, volume=0.5, seek_to=0) -> PCMVolumeTransformer:
        streaming_url = await self.provider.get_streaming_url(self.query)
        return get_ffaudio_from_streaming_url(streaming_url, volume, seek_to)

    @property
    def str_duration(self):
        if self.duration is None:
            return ''
        days = self.duration.days
        remain = self.duration.seconds
        secs = remain % 60
        remain //= 60
        mins = remain % 60
        hours = remain // 60
        if days:
            return f" {days}d {hours}h {mins}m {secs}s"
        elif hours:
            return f" {hours}h {mins}m {secs}s"
        else:
            return f" {mins}h {secs}s"


class MusicPlayerQueue:
    def __init__(self) -> None:
        self._queue: List[QueueItem] = []
        # self._current = None
        self.seek_position = None

    @property
    def queue(self):
        return self._queue[:]

    def add(self, new_items):
        self._queue.extend(new_items)

    def is_empty(self):
        return not bool(self._queue)

    def pop_track(self) -> QueueItem:
        # self._current = None
        if self.is_empty():
            return None
        # self._current = self._queue.pop(0)
        return self._queue.pop(0)  # self._current
