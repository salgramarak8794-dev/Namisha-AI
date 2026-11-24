import asyncio
import time
import numpy as np
import sounddevice as sd
from typing import Optional

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
            # Load tiny.en on CPU with int8 quantization for minimal memory (~60MB)
            self.model = WhisperModel("tiny.en", device="cpu", compute_type="int8")

    def set_muted(self, muted: bool):
        self.muted = muted

    async def record_and_transcribe(self, max_duration: float = 8.0) -> Optional[str]:
        if self.muted:
            return None

        self.load_model()
        loop = asyncio.get_event_loop()
        audio_data = await loop.run_in_executor(None, self._record_audio_vad_sync, max_duration)
        
        if audio_data is None or len(audio_data) < int(self.sample_rate * 0.4):
            return None

        try:
            segments, _ = await loop.run_in_executor(
                None,
                lambda: list(self.model.transcribe(audio_data, beam_size=1, language="en", vad_filter=True)[0])
            )
            text = " ".join([s.text for s in segments]).strip()
            # Clean hallucinated whisper artifacts on dead silence like [BLANK_AUDIO] or (music)
            if text in ("[BLANK_AUDIO]", "(music)", "(sound)", "Thank you.", "Thank you very much."):
                return None
            return text if text else None
        except Exception as e:
            print(f"Transcription error: {e}")
            return None

    def _record_audio_vad_sync(self, max_duration: float) -> Optional[np.ndarray]:
        """
        Records microphone with dynamic voice activity detection (VAD).
        Stops as soon as user finishes speaking, instead of waiting a fixed duration.
        """
        chunk_duration = 0.15  # 150ms chunks
        chunk_frames = int(chunk_duration * self.sample_rate)
        energy_threshold = 0.012  # Sensitivity threshold for human speech
        silence_threshold_seconds = 0.9  # Silence required to consider speech finished

        recorded_chunks = []
        speech_started = False
        silence_start_time = None
        start_time = time.time()

        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32") as stream:
                while True:
                    data, _ = stream.read(chunk_frames)
                    flat = data.flatten()
                    recorded_chunks.append(flat)

                    rms = float(np.sqrt(np.mean(flat**2)))
                    now = time.time()

                    if rms > energy_threshold:
                        speech_started = True
                        silence_start_time = None
                    elif speech_started:
                        if silence_start_time is None:
                            silence_start_time = now
                        elif (now - silence_start_time) >= silence_threshold_seconds:
                            # User stopped speaking for 0.9s -> stop immediately
                            break
                    else:
                        # User hasn't started speaking yet; timeout after 3.5s of silence
                        if (now - start_time) > 3.5:
                            return None

                    if (now - start_time) >= max_duration:
                        break

            if recorded_chunks and speech_started:
                return np.concatenate(recorded_chunks)
            return None
        except Exception as e:
            print(f"Audio VAD error: {e}")
            return None
