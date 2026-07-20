"""Audio recording via sounddevice."""

import threading
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"


class AudioRecorder:
    def __init__(self):
        self._stream = None
        self._frames = []
        self._recording = False
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            self._frames = []
            self._recording = True
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=self._audio_callback,
        )
        self._stream.start()

    def _audio_callback(self, indata, frames, time_info, status):
        if self._recording:
            with self._lock:
                self._frames.append(indata.copy())

    def stop(self) -> np.ndarray:
        with self._lock:
            self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        with self._lock:
            if self._frames:
                return np.concatenate(self._frames).flatten()
            return np.array([], dtype=np.float32)

    @property
    def is_recording(self) -> bool:
        return self._recording
