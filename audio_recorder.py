"""Audio recording via sounddevice with real-time RMS volume."""

import threading
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"
RMS_SMOOTHING = 0.3  # lerp factor for smooth volume


class AudioRecorder:
    def __init__(self):
        self._stream = None
        self._frames = []
        self._recording = False
        self._lock = threading.Lock()
        self._rms = 0.0
        self._smoothed_rms = 0.0
        self.on_volume = None  # callback: (float) -> None

    def start(self) -> None:
        with self._lock:
            self._frames = []
            self._recording = True
            self._rms = 0.0
            self._smoothed_rms = 0.0
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=512,
            callback=self._audio_callback,
        )
        self._stream.start()

    def _audio_callback(self, indata, frames, time_info, status):
        if self._recording:
            with self._lock:
                self._frames.append(indata.copy())
            # Compute RMS
            rms = float(np.sqrt(np.mean(indata ** 2)))
            # Smooth with lerp
            self._smoothed_rms = self._smoothed_rms * (1 - RMS_SMOOTHING) + rms * RMS_SMOOTHING
            self._rms = self._smoothed_rms
            if self.on_volume:
                self.on_volume(self._rms)

    def stop(self) -> np.ndarray:
        with self._lock:
            self._recording = False
            self._rms = 0.0
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

    @property
    def rms(self) -> float:
        return self._rms
