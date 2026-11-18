import re
from typing import Tuple, Optional

VALID_EXPRESSIONS = {
    "neutral", "happy", "smiling", "blushing", "shy", "pouting",
    "playfully_jealous", "sad", "concerned", "surprised", "curious",
    "excited", "sleepy", "thinking", "laughing"
}

class EmotionEngine:
    def __init__(self):
        self.current_emotion = "neutral"

    def extract_emotion_tag(self, text: str) -> Tuple[str, str]:
        """
        Extracts [emotion:xxx] from text and returns (clean_text, emotion)
        """
        match = re.search(r"\[emotion:([a-zA-Z_]+)\]", text, re.IGNORECASE)
        if match:
            raw_emotion = match.group(1).lower().strip()
            clean_text = re.sub(r"\[emotion:[a-zA-Z_]+\]", "", text, flags=re.IGNORECASE).strip()
            if raw_emotion in VALID_EXPRESSIONS:
                self.current_emotion = raw_emotion
                return clean_text, raw_emotion
        
        # Fallback to sentiment heuristics if no explicit tag
        detected = self.infer_from_text(text)
        return text, detected

    def infer_from_text(self, text: str) -> str:
        lower = text.lower()
        if any(w in lower for w in ["haha", "hehe", "lol", "lmao", "hilarious", "so funny"]):
            return "laughing"
        if any(w in lower for w in ["hmph", "jealous", "ignore me", "forget about me"]):
            return "playfully_jealous"
        if any(w in lower for w in ["pout", "meanie", "unfair"]):
            return "pouting"
        if any(w in lower for w in ["cute", "blush", "flatter", "pretty", "love you"]):
            return "blushing"
        if any(w in lower for w in ["shy", "embarrassed", "giggle"]):
            return "shy"
        if any(w in lower for w in ["yay", "awesome", "fantastic", "hooray", "celebrate"]):
            return "excited"
        if any(w in lower for w in ["smile", "glad", "nice to meet", "welcome"]):
            return "smiling"
        if any(w in lower for w in ["happy", "good job", "wonderful", "great"]):
            return "happy"
        if any(w in lower for w in ["sad", "unfortunate", "sorry", "crying", "depressed"]):
            return "sad"
        if any(w in lower for w in ["worried", "concerned", "are you okay", "take care", "rest"]):
            return "concerned"
        if any(w in lower for w in ["what?!", "no way", "really?", "surprised", "whoa"]):
            return "surprised"
        if any(w in lower for w in ["wonder", "curious", "how does", "why is"]):
            return "curious"
        if any(w in lower for w in ["tired", "sleepy", "yawn", "exhausted"]):
            return "sleepy"
        if any(w in lower for w in ["let's see", "thinking", "hmm", "analyzing", "calculating"]):
            return "thinking"
        
        return self.current_emotion or "neutral"
