import os
import sys
import unittest
import asyncio
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from backend.memory.memory_manager import MemoryManager
from backend.emotion.emotion_engine import EmotionEngine, VALID_EXPRESSIONS
from backend.emotion.jealous_manager import JealousManager
from backend.ai.ollama_client import OllamaClient
from backend.voice.tts_engine import TTSEngine
from backend.screen.screen_capture import ScreenCapture
from backend.coding.code_assistant import CodeAssistant

class TestNamishaComponents(unittest.TestCase):
    def test_01_memory_crud(self):
        mm = MemoryManager()
        msg_id = mm.add_conversation_message("user", "Hello Namisha!", "happy")
        self.assertIsNotNone(msg_id)
        
        mm.set_user_fact("preferences", "favorite_language", "Python")
        facts = mm.get_all_facts()
        self.assertTrue(any(f["fact_key"] == "favorite_language" for f in facts))

        mm.save_project("Namisha2", str(ROOT), "Python/WebView2", "Local companion")
        projects = mm.get_all_projects()
        self.assertTrue(any(p["name"] == "Namisha2" for p in projects))

    def test_02_emotion_engine(self):
        ee = EmotionEngine()
        text, emotion = ee.extract_emotion_tag("[emotion:playfully_jealous] Where were you?!")
        self.assertEqual(emotion, "playfully_jealous")
        self.assertEqual(text, "Where were you?!")

        self.assertEqual(len(VALID_EXPRESSIONS), 15)
        for exp in VALID_EXPRESSIONS:
            _, parsed = ee.extract_emotion_tag(f"[emotion:{exp}] Test")
            self.assertEqual(parsed, exp)

    def test_03_jealous_manager_cooldown(self):
        jm = JealousManager({"playful_jealous_mode": {"enabled": True, "away_threshold_seconds": 1, "cooldown_seconds": 10}}, ["Hmph!"])
        jm.last_interaction_time = jm.last_interaction_time - 5
        res = jm.check_return_greeting()
        self.assertIsNotNone(res)
        self.assertTrue(res["voice_only"])
        self.assertEqual(res["spoken_text"], "Hmph!")
        
        res_cooldown = jm.check_return_greeting()
        self.assertIsNone(res_cooldown)

    def test_04_screen_permission_gate(self):
        sc = ScreenCapture()
        self.assertFalse(sc.permission_granted)
        with self.assertRaises(PermissionError):
            sc.capture_primary_screen()
        
        sc.set_permission(True)
        self.assertTrue(sc.permission_granted)

    def test_05_coding_assistant_sandbox(self):
        ca = CodeAssistant(str(ROOT))
        struct = ca.scan_project_structure()
        self.assertIn(".", struct)
        with self.assertRaises(PermissionError):
            ca.read_file_safe("../../Windows/System32/cmd.exe")

    def test_06_tts_speech_generation(self):
        async def run_tts():
            tts = TTSEngine({"edge_tts_voice": "en-US-AnaNeural", "speaking_speed": 1.0, "volume": 1.0, "muted": False})
            res = await tts.generate_speech("[emotion:happy] Good morning! Ready to code?")
            self.assertIsNotNone(res)
            self.assertTrue(os.path.exists(res["file_path"]))
            self.assertIn(res["engine"], ["edge_tts", "sapi5"])

        asyncio.run(run_tts())

    def test_07_ollama_connectivity(self):
        async def check_ollama():
            ollama = OllamaClient()
            running = await ollama.is_running()
            self.assertTrue(running)
            models = await ollama.list_models()
            model_names = [m["name"] for m in models]
            self.assertTrue(any("llama3.2" in n or "nammi" in n for n in model_names))

        asyncio.run(check_ollama())

if __name__ == "__main__":
    unittest.main()
