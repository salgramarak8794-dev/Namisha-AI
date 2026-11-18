from datetime import datetime
from typing import List, Dict, Any, Optional
from .db import get_connection, init_db

class MemoryManager:
    def __init__(self):
        init_db()

    def add_conversation_message(self, role: str, content: str, emotion: str = "neutral") -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (role, content, emotion) VALUES (?, ?, ?)",
            (role, content, emotion)
        )
        msg_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return msg_id

    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, timestamp, role, content, emotion FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        # Return chronological order
        return [dict(r) for r in reversed(rows)]

    def set_user_fact(self, category: str, key: str, value: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_facts (category, fact_key, fact_value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(fact_key) DO UPDATE SET
                category=excluded.category,
                fact_value=excluded.fact_value,
                updated_at=CURRENT_TIMESTAMP
        """, (category, key, value))
        conn.commit()
        conn.close()

    def get_all_facts(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, category, fact_key, fact_value, updated_at FROM user_facts ORDER BY category, fact_key")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_fact(self, fact_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_facts WHERE id = ?", (fact_id,))
        conn.commit()
        conn.close()

    def save_project(self, name: str, path: str, tech_stack: str, notes: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO projects (name, path, tech_stack, notes, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
                path=excluded.path,
                tech_stack=excluded.tech_stack,
                notes=excluded.notes,
                updated_at=CURRENT_TIMESTAMP
        """, (name, path, tech_stack, notes))
        conn.commit()
        conn.close()

    def get_all_projects(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, path, tech_stack, notes, updated_at FROM projects ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def log_emotion(self, mood: str, user_input_snippet: str = ""):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO emotional_logs (detected_mood, user_input_snippet) VALUES (?, ?)",
            (mood, user_input_snippet[:100])
        )
        conn.commit()
        conn.close()

    def reset_all_memories(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversations")
        cursor.execute("DELETE FROM user_facts")
        cursor.execute("DELETE FROM projects")
        cursor.execute("DELETE FROM emotional_logs")
        conn.commit()
        conn.close()

    def get_relevant_context(self) -> str:
        facts = self.get_all_facts()
        projects = self.get_all_projects()
        context_parts = []
        if facts:
            fact_lines = [f"- {f['fact_key']}: {f['fact_value']}" for f in facts]
            context_parts.append("Important user facts:\n" + "\n".join(fact_lines))
        if projects:
            proj_lines = [f"- Project '{p['name']}' ({p['tech_stack']}): {p['notes']}" for p in projects[:3]]
            context_parts.append("Active projects:\n" + "\n".join(proj_lines))
        return "\n\n".join(context_parts)
