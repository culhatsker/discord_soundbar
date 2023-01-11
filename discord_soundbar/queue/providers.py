from typing import List, Dict, Optional

from datetime import timedelta

from .ytapi import youtube_search
from .ytdl import ytdl_query


class Provider:
    name = "unknown"

    @staticmethod
    async def from_query(_query: str) -> Dict[str, Optional[str]]:
        raise NotImplementedError

    @staticmethod
    async def get_streaming_url(_query: str) -> str:
        raise NotImplementedError


class FileProvider:
    name = "file"

    @staticmethod
    async def from_query(query: str) -> Dict[str, Optional[str]]:
        return [{
            "query": query,
            "artist": None,
            "title": None,
            "suration": None
        }]

    @staticmethod
    async def get_streaming_url(query: str) -> str:
        return query


class YTDLProvider:
    name = "ytdl"

    @staticmethod
    def url_from_id(id_: str) -> str:
        return f"https://www.youtube.com/watch?v={id_}"

    @staticmethod
    def get_construct_args(video_info) -> Dict:
        duration = video_info.get("duration")
        artist = video_info.get("artist")
        creator = video_info.get("creator")
        uploader = video_info.get("uploader")
        if uploader and uploader.endswith(" - Topic"):
            uploader = uploader.rsplit(" - ", 1)[0]
        channel = artist or creator or uploader
        track = video_info.get("track")
        title = track or video_info.get("title")
        return {
            "query": YTDLProvider.url_from_id(video_info["id"]),
            "artist": channel,
            "title": title,
            "duration": timedelta(seconds=duration)
        }

    @staticmethod
    async def from_query(query: str) -> List[Dict]:
        return [
            YTDLProvider.get_construct_args(vinfo)
            for vinfo in await ytdl_query(query)
        ]

    @staticmethod
    async def get_streaming_url(query: str) -> str:
        info = await ytdl_query(query)
        if len(info) != 1:
            return None
        return info[0]["url"]

    @staticmethod
    async def transform_search_query(query: str) -> str:
        results = await youtube_search(query)
        if not results:
            return None
        video_url = results[0].get("url")
        if not video_url:
            return None
        return (video_url, YTDLProvider)
