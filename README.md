# discord_soundbar
Discord music bot

## Getting started

1) Get Discord API KEY, set `DISCORD_BOT_TOKEN` environment variable

2) [Optional] Get YouTube API KEY, set `YOUTUBE_API_KEY` variable

3) Get `ffmpeg` executable, either install it via package manager, or build
from sources

4) Start by running `python3 bot.py`

## Dependencies

Bot requires you to have ffmpeg installed however the one that comes with
ubuntu requires X11 and some other Desktop related libs that aren't actually
required to decode music. You might want to build ffmpeg from sources to
exclude these dependencies, use these configure options to do so:

```
cd ffmpeg
./configure --prefix=/home/bifidock/misc/ffmpeg/install_dir \
    --disable-shared --disable-runtime-cpudetect --disable-doc \
    --disable-avdevice --disable-x86asm --disable-xlib \
    --disable-everything \
    --enable-openssl --enable-network \
    --enable-lzma --enable-zlib --enable-iconv --enable-sndio \
    --enable-decoders --enable-encoders --enable-demuxers \
    --enable-muxers --enable-protocols \
    --enable-filter=aresample
```
