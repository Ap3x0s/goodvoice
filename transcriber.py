"""Whisper transcription via faster-whisper."""

import numpy as np
from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self, model_size: str = "medium", device: str = "auto"):
        self.model_size = model_size
        self.device = device
        self._model = None

    def load_model(self) -> None:
        """Load the Whisper model (slow, do once)."""
        self._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type="float16" if self.device != "cpu" else "int8",
        )

    def transcribe(
        self,
        audio: np.ndarray,
        language: str = "auto",
        punctuation: bool = True,
    ) -> str:
        """Transcribe audio array to text string."""
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        lang = None if language == "auto" else language
        segments, info = self._model.transcribe(
            audio,
            language=lang,
            beam_size=5,
            vad_filter=True,
        )

        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())

        text = " ".join(text_parts)

        if not punctuation:
            import string
            for char in string.punctuation + "—–«»…":
                text = text.replace(char, "")

        return text.strip()
