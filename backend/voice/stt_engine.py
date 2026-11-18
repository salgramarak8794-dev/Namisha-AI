import asyncio
import numpy as np
import sounddevice as sd
from typing import Optional, Callable

class STTEngine:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.model = None
        self.is_recording = False
        self.muted = False

    def load_model(self):
        """Lazy loads Faster-Whisper model only when requested to save RAM."""
        if self.model is None:
            from faster_whisper import WhisperModel
            # Load tiny.en on CPU with int8 quantization for minimal memory
            self.model = WhisperModel("tiny.en", device="cpu", compute_type="int8")

    def set_muted(self, muted: bool):
        self.muted = muted

    async def record_and_transcribe(self, duration_seconds: float = 4.0) -> Optional[str]:
        if self.muted:
            return None

        self.load_model()
        
        # Run blocking audio capture in thread executor to keep event loop free
        loop = asyncio.get_event_loop()
        audio_data = await loop.run_in_executor(None, self._record_audio_sync, duration_seconds)
        
        if audio_data is None or len(audio_data) == 0:
            return None

        # Check audio energy threshold to avoid transcribing dead silence
        rms = np.sqrt(np.mean(audio_data**2))
        if rms < 0.01:
            return None

        # Transcribe
        segments, _ = await loop.run_in_executor(None, self.model.transcribe, audio_data, {"beam_size": 1})
        text = " ".join([s.text for s in segments]).strip()
        return text if text else None

    def _record_audio_sync(self, duration: float) -> Optional[np.ndarray]:
        try:
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32"
            )
            sd.wait()
            # sd.wait() cleanly releases stream
            return recording.flatten()
        except Exception as e:
            print(f"Audio recording error: {e}")
            return None
