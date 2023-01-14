from typing import List, Dict, Optional

from datetime import timedelta

from .ytapi import youtube_search
from .ytdl import ytdl_query_autoproxy


class Provider:
    name = "unknown"

    @staticmethod
    async def from_query(_query: str) -> Dict[str, Optional[str]]:
        raise NotImplementedError

    @staticmethod
    async def get_streaming_url(_query: str) -> tuple[str, str]:
        raise NotImplementedError


class FileProvider:
    name = "file"

    @staticmethod
    async def from_query(query: str) -> Dict[str, Optional[str]]:
        return [{
            "query": query,
            "artist": None,
            "title": None,
            "duration": None
        }]

    @staticmethod
    async def get_streaming_url(query: str) -> tuple[str, str]:
        return (None, query)


class YTDLProvider:
    name = "ytdl"

    @staticmethod
    def url_from_id(id_: str) -> str:
        return f"https://www.youtube.com/watch?v={id_}"

    @staticmethod
    def get_construct_args(video_info, proxy_name) -> Dict:
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
            "duration": timedelta(seconds=duration),
            "cached_streaming_url": (proxy_name, video_info["url"])
        }

    @staticmethod
    async def from_query(query: str) -> List[Dict]:
        proxy_name, playlist = await ytdl_query_autoproxy(query)
        return [
            YTDLProvider.get_construct_args(vinfo, proxy_name)
            for vinfo in playlist
        ]

    @staticmethod
    async def get_streaming_url(query: str, proxy_name=None) -> tuple[str, str]:
        matched_proxy, info = await ytdl_query_autoproxy(query, proxy_name)
        if len(info) != 1:
            raise Exception("Trying to get info of "
                "a single video, got more than one result.")
        return (matched_proxy, info[0]["url"])

    @staticmethod
    async def transform_search_query(query: str) -> str:
        results = await youtube_search(query)
        if not results:
            return None
        video_url = results[0].get("url")
        if not video_url:
            return None
        return (video_url, YTDLProvider)
