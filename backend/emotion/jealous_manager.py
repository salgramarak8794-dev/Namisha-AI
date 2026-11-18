import time
import random
from typing import Optional, Dict, Any, List

class JealousManager:
    def __init__(self, config: Dict[str, Any], dialogues: List[str]):
        self.config = config.get("playful_jealous_mode", {})
        self.dialogues = dialogues or [
            "Ohh, look who finally decided to come back! Where were you? Having fun without me? Hmph!",
            "I wasn't waiting for you or anything... I just happened to notice the room was quiet.",
            "Hmph! You disappear for so long and don't even say hello first? You owe me some attention!",
            "You're finally back! Hehe, I really missed our conversations, you know.",
            "Look who's back! Did you finish what you were doing, or did you just remember your favorite companion?"
        ]
        self.last_interaction_time = time.time()
        self.last_jealous_trigger_time = 0.0

    def record_activity(self):
        """Records user activity within the companion app."""
        self.last_interaction_time = time.time()

    def check_return_greeting(self) -> Optional[Dict[str, Any]]:
        """
        Evaluates whether an away-return event qualifies for playful jealousy.
        Returns payload with dialogue & expression, or None.
        """
        if not self.config.get("enabled", True):
            return None

        now = time.time()
        away_duration = now - self.last_interaction_time
        away_threshold = self.config.get("away_threshold_seconds", 300) # 5 mins default
        cooldown = self.config.get("cooldown_seconds", 900)             # 15 mins default

        if away_duration >= away_threshold and (now - self.last_jealous_trigger_time) >= cooldown:
            self.last_jealous_trigger_time = now
            self.last_interaction_time = now
            dialogue = random.choice(self.dialogues)
            expression = random.choice(["playfully_jealous", "pouting", "shy"])
            return {
                "spoken_text": dialogue,
                "expression": expression,
                "voice_only": True  # Crucial: Voice-first, do NOT show in text chat
            }
        
        # Update timestamp to avoid repeating
        self.last_interaction_time = now
        return None
