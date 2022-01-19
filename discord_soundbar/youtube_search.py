from aiohttp import request
from os import environ


YOUTUBE_API_KEY = environ.get("YOUTUBE_API_KEY")
YOUTUBE_REGION = environ.get("YOUTUBE_REGION") or "US"
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


class APIError(Exception):
    pass


class YouTubeSearch:
    def __init__(self, query, max_results=10):
        self.query = query
        self.max_results = max_results
    
    async def youtube_search(self):
        request_coro = request("GET", SEARCH_URL, params={
            "type": "video",
            "part": "snippet",
            "safeSearch": "none",
            "q": self.query,
            "videoCategoryId": 10,
            "key": YOUTUBE_API_KEY,
            "maxResults": self.max_results
        })
        async with request_coro as resp:
            resp = await resp.json()
            if not "items" in resp:
                raise APIError
        return [
            {
                "title": r["snippet"]["title"],
                "url_suffix": "/watch?v=" + r["snippet"]["id"]["videoId"],
                # there are some other params in the response, but I don't need them
            }
            for r in resp["items"]
        ]

    def __await__(self):
        return self.youtube_search()