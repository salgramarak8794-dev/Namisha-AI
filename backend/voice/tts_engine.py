import asyncio
import os
import io
import math
import struct
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List

class TTSEngine:
    def __init__(self, voice_config: Dict[str, Any]):
        self.config = voice_config
        self.voice_name = voice_config.get("edge_tts_voice", "en-US-AnaNeural")
        self.speed = voice_config.get("speaking_speed", 1.0)
        self.volume = voice_config.get("volume", 1.0)
        self.muted = voice_config.get("muted", False)
        self.temp_dir = Path(tempfile.gettempdir()) / "namisha_audio"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def set_muted(self, muted: bool):
        self.muted = muted

    async def generate_speech(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Synthesizes speech and returns file path + simulated amplitude profile for lip-sync.
        """
        if self.muted or not text.strip():
            return None

        # Clean any leftover emotion tags from speech text
        import re
        clean_text = re.sub(r"\[emotion:[a-zA-Z_]+\]", "", text).strip()
        if not clean_text:
            return None

        output_file = self.temp_dir / f"tts_{os.getpid()}_{hash(clean_text) % 100000}.mp3"
        
        # 1. Try Edge-TTS (high quality natural voice)
        try:
            import edge_tts
            # Format rate and pitch
            rate_percent = int((self.speed - 1.0) * 100)
            rate_str = f"{rate_percent:+d}%"
            communicate = edge_tts.Communicate(clean_text, self.voice_name, rate=rate_str)
            await communicate.save(str(output_file))
            if output_file.exists() and output_file.stat().st_size > 0:
                return {
                    "file_path": str(output_file),
                    "text": clean_text,
                    "engine": "edge_tts"
                }
        except Exception as e:
            print(f"Edge-TTS failed ({e}), falling back to Windows Native TTS...")

        # 2. Fallback to Windows SAPI5 (100% offline, 0% CPU, instant)
        try:
            wav_file = output_file.with_suffix(".wav")
            # Generate speech via Windows PowerShell SAPI to WAV
            escaped_text = clean_text.replace('"', '`"').replace("'", "''")
            cmd = f"""
            Add-Type -AssemblyName System.Speech;
            $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;
            $synth.SelectVoice('Microsoft Zira Desktop');
            $synth.SetOutputToWaveFilePath('{str(wav_file)}');
            $synth.Speak('{escaped_text}');
            $synth.Dispose();
            """
            proc = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-Command", cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            if wav_file.exists() and wav_file.stat().st_size > 0:
                return {
                    "file_path": str(wav_file),
                    "text": clean_text,
                    "engine": "sapi5"
                }
        except Exception as e:
            print(f"SAPI5 fallback failed: {e}")

        return None
