import asyncio
from datetime import timedelta
from dataclasses import dataclass

import aiohttp
import discord
from youtube_search import YoutubeSearch

from . import youtube_dl_glue


DEFAULT_VOLUME = 0.5


@dataclass
class AudioTrackInfo:
    artist: str
    title: str
    duration: timedelta
    user_tag: object = None

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
            return f" {days} days {hours} hours {mins} minutes {secs} seconds"
        elif hours:
            return f" {hours}:{mins}:{secs}"
        else:
            return f" {mins}:{secs}"


class AudioSource:
    ffmpeg_options="-vn -bufsize 5"
    ffmpeg_before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"


    def __init__(self):
        self._info = None
    
    @staticmethod
    async def _get_mime_type_of_url(url):
        async with aiohttp.ClientSession() as session:
            async with session.head(url) as response:
                content_type = response.headers.get("Content-Type")
                if content_type:
                    return content_type.split(";")[0]
                return None

    @staticmethod
    async def from_query(query):
        query = query.strip()
        if not (query.startswith("https://") or query.startswith("http://")):
            return await YouTubeSearchAudioSource.from_query(query)
        mime_type = await AudioSource._get_mime_type_of_url(query)
        if mime_type.split("/")[0] in {"video", "audio"}:
            return await PlainAudioSource.from_query(query)
        else:
            return await YTDLAudioSource.from_query(query)

    async def get_track_info(self):
        raise NotImplementedError()

    @property
    async def track_info(self) -> AudioTrackInfo:
        if not hasattr(self, "_track_info"):
            self._track_info: AudioTrackInfo = self.get_track_info()
            if hasattr(self, "user_tag"):
                self._track_info.user_tag = self.user_tag
        return self._track_info

    def get_streaming_url(self):
        raise NotImplementedError()

    def get_audio_source(self):
        before_options = self.ffmpeg_before_options
        if hasattr(self, "seek_to"):
            before_options += " -ss " + self.seek_to
        return discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(
            self.get_streaming_url(), options=self.ffmpeg_options,
            before_options=before_options), volume=DEFAULT_VOLUME)


class PlainAudioSource(AudioSource):
    def __init__(self, url) -> None:
        super().__init__()
        self.url = url

    @staticmethod
    async def from_query(query):
        mime_type = await PlainAudioSource._get_mime_type_of_url(query)
        if mime_type.split("/")[0] not in {"audio", "video"}:
            raise ValueError
        return [PlainAudioSource(query)]

    def get_track_info(self):
        return AudioTrackInfo(artist=None, title=None, duration=None)
    
    def get_streaming_url(self):
        return self.url


class YTDLAudioSource(AudioSource):
    def __init__(self, ytdl_info):
        super().__init__()
        self._ytdl_info = ytdl_info

    @staticmethod
    async def from_query(query):
        ytdl_info = await youtube_dl_glue.get_info(query)
        return [YTDLAudioSource(info) for info in ytdl_info]

    def get_track_info(self):
        info = self._ytdl_info
        duration = info.get("duration")
        artist = info.get("artist")
        creator = info.get("creator")
        uploader = info.get("uploader")
        if uploader and uploader.endswith(" - Topic"):
            uploader = uploader.rsplit(" - ", 1)[0]
        channel = artist or creator or uploader
        track = info.get("track")
        title = track or info.get("title")
        return AudioTrackInfo(artist=channel, title=title,
            duration=timedelta(seconds=duration))

    def get_streaming_url(self):
        return self._ytdl_info["url"]


class YouTubeSearchAudioSource(AudioSource):
    @staticmethod
    async def from_query(query):
        def _search(query):
            return YoutubeSearch(query, max_results=5).videos
        results = await asyncio.get_event_loop()\
            .run_in_executor(None, _search, query)
        if not results:
            raise Exception("Can't find anything on YouTube for this search query.")
        first_result_url = "https://www.youtube.com" + results[0]["url_suffix"]
        return await YTDLAudioSource.from_query(first_result_url)