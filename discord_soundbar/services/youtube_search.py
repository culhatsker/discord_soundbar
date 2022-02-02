import asyncio
import logging


try:
    from youtube_api_search import YoutubeSearch
    # searches for music videos only, requires YouTube API key
except ImportError:
    logging.warning("Can't import built-in YouTube search module, "
        "falling back to `youtube_search` from PYPI")
    from youtube_search import YoutubeSearch
    # sometimes finds crappy videos instead of music, doesn't require API key


async def get_first_result(query):
    def _search(query):
        return YoutubeSearch(query, max_results=5).videos
    results = await asyncio.get_event_loop()\
        .run_in_executor(None, _search, query)
    if not results:
        raise Exception("Can't find anything on YouTube for this search query.")
    return "https://www.youtube.com" + results[0]["url_suffix"]


__all__ = ["YoutubeSearch", "get_first_result"]
