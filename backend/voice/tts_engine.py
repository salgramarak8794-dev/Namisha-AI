import asyncio
import os
import io
import re
import math
import struct
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List

class TTSEngine:
    def __init__(self, voice_config: Dict[str, Any]):
        self.config = voice_config
        self.voice_name = voice_config.get("edge_tts_voice", "en-US-JennyNeural")
        self.speed = voice_config.get("speaking_speed", 1.0)
        self.volume = voice_config.get("volume", 1.0)
        self.muted = voice_config.get("muted", False)
        self.temp_dir = Path(tempfile.gettempdir()) / "namisha_audio"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def set_muted(self, muted: bool):
        self.muted = muted

    def set_voice(self, voice_name: str):
        self.voice_name = voice_name

    def clean_text_for_speech(self, text: str) -> str:
        """
        Cleans markdown, tags, emojis, and code blocks so the speech sounds like
        a real, natural person talking conversationally rather than reading code/symbols.
        """
        # 1. Remove emotion tags like [emotion:happy]
        t = re.sub(r"\[emotion:[a-zA-Z_]+\]", "", text, flags=re.IGNORECASE)
        # 2. Remove code blocks (```...```)
        t = re.sub(r"```[\s\S]*?```", "Here is the code on your screen.", t)
        # 3. Remove inline code (`...`)
        t = re.sub(r"`([^`]+)`", r"\1", t)
        # 4. Remove URLs
        t = re.sub(r"https?://\S+", "", t)
        # 5. Remove markdown headers, bold, italics, bullets
        t = re.sub(r"[#*_~>]+", "", t)
        t = re.sub(r"^\s*[-+*]\s+", "", t, flags=re.MULTILINE)
        # 6. Remove common emojis that sound weird when spoken
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        t = emoji_pattern.sub("", t)
        # 7. Normalize whitespace
        t = re.sub(r"\s+", " ", t).strip()
        return t

    async def generate_speech(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Synthesizes human-sounding speech and saves to temporary mp3/wav.
        """
        if self.muted or not text.strip():
            return None

        clean_text = self.clean_text_for_speech(text)
        if not clean_text:
            return None

        output_file = self.temp_dir / f"tts_{os.getpid()}_{abs(hash(clean_text)) % 1000000}.mp3"
        
        # 1. Try Microsoft Natural Neural Voice (JennyNeural / AvaNeural)
        try:
            import edge_tts
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
            print(f"Edge-TTS failed ({e}), falling back to Windows Native SAPI...")

        # 2. Fallback to Windows SAPI5 (100% offline fallback)
        try:
            wav_file = output_file.with_suffix(".wav")
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
