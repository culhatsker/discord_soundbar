# discord_soundbar
Discord music bot

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

If you use a fallback proxy feature, but have only SOCKS5 proxies in
possession then you may want to use a socks-to-http proxy converter
such as this one [https://github.com/KaranGauswami/socks-to-http-proxy].
