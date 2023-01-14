import asyncio

import yt_dlp as youtube_dl

from .proxy import proxies


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


def make_instance(proxy=None):
    options = {
        'format': 'bestaudio/best',
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'default_search': 'auto'
    }
    if proxy:
        options["proxy"] = proxy
    return youtube_dl.YoutubeDL(options)


proxy_instances = {
    pname: make_instance(proxy)
    for pname, proxy in proxies.items()
}
proxy_instances[None] = make_instance()


async def ytdl_query(url, proxy_name):
    ytdl = proxy_instances[proxy_name]

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

    if 'entries' in data:
        playlist = data['entries']
    else:
        playlist = [data]

    return (proxy_name, playlist)


async def ytdl_query_autoproxy(url, proxy_name=None):
    try:
        return await ytdl_query(url, proxy_name)
    except youtube_dl.DownloadError as err:
        if proxy_name is not None:
            raise
        if "Video unavailable" not in err.msg:
            raise

    done, _pending = await asyncio.wait([
        ytdl_query(url, instance)
        for instance in proxy_instances.keys()
        if not instance == None
    ], return_when=asyncio.FIRST_COMPLETED)

    return next(iter(done)).result()
