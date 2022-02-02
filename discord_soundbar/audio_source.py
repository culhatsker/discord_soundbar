import argparse
import json
from datetime import datetime, timedelta
from time import time

import aiohttp
import discord

from .services import youtube_search, youtube_audio_source


DEFAULT_VOLUME = 0.5


class AudioTrack:
    ffmpeg_options="-vn -bufsize 5"
    ffmpeg_before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"

    fields = {
        "url": (str, "l"),
        "artist": (str, "a"),
        "title": (str, "t"),
        "duration": (lambda s: timedelta(seconds=s), "d"),
        "usertag": (str, "u")
    }

    def __init__(self, url, artist=None, title=None, duration=None, usertag=None):
        self.url = url
        self.artist = artist
        self.title = title
        if duration and not isinstance(duration, timedelta):
            duration = timedelta(seconds=duration)
        self.duration = duration
        self.usertag = usertag

    def serialize(self):
        def simplify_arg(val):
            if isinstance(val, timedelta):
                val = val.total_seconds()
            return val

        return self.__class__.__name__ + ":" + json.dumps({
            fshort: simplify_arg(getattr(self, fname))
            for fname, (_ftype, fshort) in AudioTrack.fields.items()
        })

    @staticmethod
    def from_serialized(data):
        def argparser(argt):
            def _argparser(val):
                if val is not None:
                    return argt(val)
            return _argparser

        classname, data = data.split(":", 1)
        cls = AUDIOTRACK_CLASSES[classname]
        j = json.loads(data)
        return cls(**{
            fname: argparser(ftype)(j[fshort])
            for fname, (ftype, fshort) in cls.fields.items()
        })

    @staticmethod
    async def from_query(query):
        query = query.strip()
        if not (query.startswith("https://") or query.startswith("http://")):
            query = await youtube_search.get_first_result(query)
        async with aiohttp.ClientSession() as session:
            async with session.head(query) as response:
                content_type = response.headers.get("Content-Type")
                if not content_type:
                    # handle error
                    pass
                mime_type = content_type.split(";")[0]
        if mime_type.split("/")[0] in {"audio", "video"}:
            return [AudioTrack(url=query)]
        return await YTDLAudioTrack.from_query(query)

    async def get_streaming_url(self):
        return self.url
    
    def get_audio_source(self, volume=100, seek_to=None):
        before_options = self.ffmpeg_before_options
        if seek_to:
            before_options += " -ss " + seek_to
        return discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(
            self.get_streaming_url(), options=self.ffmpeg_options,
            before_options=before_options), volume=volume)

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


class YTDLAudioTrack(AudioTrack):
    @staticmethod
    async def from_url(url):
        ytdl_info = await youtube_audio_source.get_info(url)
        return [YTDLAudioTrack(info, url) for info in ytdl_info]
    
    @staticmethod
    def from_ytdl_info(info, url):
        duration = info.get("duration")
        artist = info.get("artist")
        creator = info.get("creator")
        uploader = info.get("uploader")
        if uploader and uploader.endswith(" - Topic"):
            uploader = uploader.rsplit(" - ", 1)[0]
        channel = artist or creator or uploader
        track = info.get("track")
        title = track or info.get("title")
        obj = YTDLAudioTrack(url=url, artist=channel,
            title=title, duration=timedelta(seconds=duration))
        obj._ytdl_info = info
        obj._ytdl_dt = datetime.now()
        return obj

    async def get_streaming_url(self):
        if hasattr(self, "_ytdl") and (datetime.now() - self._ytdl_dt) > timedelta(seconds=5*60):
            self._ytdl_info = await youtube_audio_source.get_info(self.url)
            self._ytdl_dt = datetime.now()
        return self._ytdl_info["url"]


AUDIOTRACK_CLASSES = {
    "AudioTrack": AudioTrack,
    "YTDLAudioTrack": YTDLAudioTrack
}
