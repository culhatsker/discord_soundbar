import asyncio
import traceback
from datetime import timedelta
from typing import List

from redis import Redis

from .audio_source import AudioTrack
from .views import render_error, render_track


connection = Redis("127.0.0.1", 6379)


async def wait_for_value(func, timeout, check_interval=0.1):
    max_iterations = timeout / check_interval
    iterations = 0
    while True:
        value = func()
        if value is not None:
            return value
        iterations += 1
        if iterations >= max_iterations:
            raise TimeoutError
        await asyncio.sleep(check_interval)


class MusicPlayerState:
    def __init__(self, ctx) -> None:
        self._ctx = ctx
        self._guild_id = ctx.guild.id
        self._signals = []
        self._play_task = None

    def _qkey(self):
        return f"Q{self._guild_id}"
    
    def _vkey(self):
        return f"V{self._guild_id}"

    def pop(self) -> AudioTrack:
        data = connection.lindex(self._qkey(), 0)
        if not data:
            return None
        return AudioTrack.from_serialized(data)

    def add(self, new_items: List[AudioTrack]):
        connection.rpush(self._qkey(), *map(AudioTrack.serialize, new_items))

    @property
    def items(self) -> List[AudioTrack]:
        return [AudioTrack.from_serialized(item)
            for item in connection.lrange(self._qkey(), 0, -1)]

    def stop(self):
        connection.delete(self._qkey())
        self._signals.append(("SKIP",))

    def skip(self):
        self._signals.append(("SKIP",))

    def seek(self, position: timedelta):
        self._signals.append(("SEEK", position))

    def volume(self, level: int):
        self._signals.append(("VOLUME", level))

    def _session_play_track(self, track, position=None):
        volume = connection.get(self._vkey())
        source = track.get_audio_source(volume, seek_to=position)
        after_play = lambda err: err and print(f"Player error: {err}")
        if self.ctx.voice_client.is_playing():
            self.ctx.voice_client.stop()
        self.ctx.voice_client.play(source, after=after_play)
    
    @property
    def active(self):
        if self._play_task:
            if self._play_task.done():
                return True
            else:
                self._play_task = None
        return False
    
    async def play_session(self):
        if self.active:
            return None
        self._play_task = asyncio.create_task(self._play_session())
    
    async def _play_session(self):
        while True:
            try:
                # waiting up to 15 minutes for a new track
                track: AudioTrack = await self.wait_for_value(
                    self.pop(), timeout=15*60)
                await self.ctx.send(embed=render_track(
                    track, title="Now playing"))
                self._session_play_track(track)
            except TimeoutError:
                await self.ctx.send("Bye, bitch. Call me again if you need more music.")
                return
            except Exception as error:
                traceback.print_exc()
                await self.ctx.send(embed=render_error(repr(error)))
                continue
            while True:
                if self.ctx.voice_client is None:
                    # actually it's an error
                    return
                if not self.ctx.voice_client.is_playing():
                    # finished playing
                    break
                while self._signals:
                    sname, *args = self._signals.pop()
                    if sname == "SKIP":
                        self.ctx.voice_client.stop()
                    elif sname == "SEEK":
                        pos, = args
                        self._session_play_track(track, pos)
                    elif sname == "VOLUME":
                        vol, = args
                        connection.set(self._vkey(), vol)
                        self.ctx.voice_client.source.volume = vol / 100
                await asyncio.sleep(0.1)
