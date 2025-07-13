import json
import sqlite3

class UserData:
    def __init__(self, db_path="user_data.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                model TEXT,
                context TEXT,
                voice_enabled BOOLEAN DEFAULT FALSE
            )
            """)

    def set_user_model(self, user_id, model):
        with self.conn:
            self.conn.execute("""
            INSERT INTO users (user_id, model) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET model = excluded.model
            """, (user_id, model))

    def get_user_model(self, user_id):
        with self.conn:
            cursor = self.conn.execute("SELECT model FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else "gpt"

    def set_user_context(self, user_id, context):
        with self.conn:
            self.conn.execute("""
            INSERT INTO users (user_id, context) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET context = excluded.context
            """, (user_id, json.dumps(context)))

    def get_user_context(self, user_id):
        with self.conn:
            cursor = self.conn.execute("SELECT context FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return json.loads(result[0]) if result and result[0] else {}

    def get_user_memory(self, user_id):
        # This is a placeholder. A more robust solution would be needed.
        # For now, we'll just use the context field.
        return self.get_user_context(user_id)

    def save_context(self, user_id, new_context):
        # This is a placeholder. A more robust solution would be needed.
        # For now, we'll just use the context field.
        self.set_user_context(user_id, new_context)

    def set_voice_enabled(self, user_id, enabled):
        with self.conn:
            self.conn.execute("""
            INSERT INTO users (user_id, model, context, voice_enabled) VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET voice_enabled = excluded.voice_enabled
            """, (user_id, self.get_user_model(user_id), json.dumps(self.get_user_context(user_id)), enabled))

    def get_voice_enabled(self, user_id):
        with self.conn:
            cursor = self.conn.execute("SELECT voice_enabled FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else False


user_data = UserData()
