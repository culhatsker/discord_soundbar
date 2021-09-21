from .audio_source import AudioSource


class MusicPlayerQueue:
    def __init__(self) -> None:
        self._queue = []
        self._queue_current = None
        self.seek_requested = None

    @property
    def next_up(self):
        return self._queue[self._queue_current:]

    def add_to_queue(self, new_items):
        self._queue.extend(new_items)

    def queue_has_items(self):
        if self._queue_current is None:
            return bool(self._queue)
        else:
            return len(self._queue) > self._queue_current + 1

    def next_track(self) -> AudioSource:
        if not self.queue_has_items():
            return None
        if self._queue_current is None:
            self._queue_current = 0
        else:
            self._queue_current += 1
        return self._queue[self._queue_current]
