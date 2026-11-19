
import json
import sqlite3
import uuid

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = PROJECT_ROOT / "data" / "chat_history.db"


class ChatStorage:

    def __init__(self, db_path=DB_PATH):

        self.db_path = Path(db_path)

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.initialize_database()

    # --------------------------------------------------
    # DATABASE CONNECTION
    # --------------------------------------------------

    @contextmanager
    def get_connection(self):

        connection = sqlite3.connect(self.db_path)

        connection.row_factory = sqlite3.Row

        # Enable foreign key constraints
        connection.execute("PRAGMA foreign_keys = ON")

        try:
            yield connection
            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    # --------------------------------------------------
    # INITIALIZE DATABASE AND TABLES
    # --------------------------------------------------

    def initialize_database(self):

        with self.get_connection() as connection:

            # Conversations table
            connection.execute("""
                CREATE TABLE IF NOT EXISTS conversations (

                    conversation_id TEXT PRIMARY KEY,

                    title TEXT NOT NULL,

                    subject TEXT NOT NULL,

                    created_at TEXT NOT NULL,

                    updated_at TEXT NOT NULL
                )
            """)

            # Messages table
            connection.execute("""
                CREATE TABLE IF NOT EXISTS messages (

                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,

                    conversation_id TEXT NOT NULL,

                    role TEXT NOT NULL,

                    content TEXT NOT NULL,

                    created_at TEXT NOT NULL,

                    sources TEXT NOT NULL DEFAULT '[]',

                    diagram TEXT,

                    FOREIGN KEY (conversation_id)
                    REFERENCES conversations(conversation_id)
                    ON DELETE CASCADE
                )
            """)

            # Index for faster conversation lookup
            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                ON messages(conversation_id)
            """)

            # --------------------------------------------------
            # DATABASE MIGRATION
            # Supports existing databases created earlier
            # --------------------------------------------------

            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(messages)"
                ).fetchall()
            }

            if "sources" not in columns:

                connection.execute("""
                    ALTER TABLE messages
                    ADD COLUMN sources TEXT NOT NULL DEFAULT '[]'
                """)

            if "diagram" not in columns:

                connection.execute("""
                    ALTER TABLE messages
                    ADD COLUMN diagram TEXT
                """)

    # --------------------------------------------------
    # CREATE NEW CONVERSATION
    # --------------------------------------------------

    def create_conversation(self, subject, title="New Chat"):

        conversation_id = str(uuid.uuid4())

        timestamp = datetime.now(timezone.utc).isoformat()

        with self.get_connection() as connection:

            connection.execute("""
                INSERT INTO conversations
                (
                    conversation_id,
                    title,
                    subject,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                conversation_id,
                title,
                subject,
                timestamp,
                timestamp
            ))

        return conversation_id

    # --------------------------------------------------
    # SAVE MESSAGE
    # --------------------------------------------------

    def add_message(
        self,
        conversation_id,
        role,
        content,
        sources=None,
        diagram=None
    ):

        timestamp = datetime.now(timezone.utc).isoformat()

        sources_json = json.dumps(
            sources or [],
            ensure_ascii=False
        )

        with self.get_connection() as connection:

            connection.execute("""
                INSERT INTO messages
                (
                    conversation_id,
                    role,
                    content,
                    created_at,
                    sources,
                    diagram
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                conversation_id,
                role,
                content,
                timestamp,
                sources_json,
                diagram
            ))

            # Update conversation activity timestamp
            connection.execute("""
                UPDATE conversations
                SET updated_at = ?
                WHERE conversation_id = ?
            """, (
                timestamp,
                conversation_id
            ))

    # --------------------------------------------------
    # UPDATE CONVERSATION TITLE
    # --------------------------------------------------

    def update_title(self, conversation_id, title):

        with self.get_connection() as connection:

            connection.execute("""
                UPDATE conversations
                SET title = ?
                WHERE conversation_id = ?
            """, (
                title,
                conversation_id
            ))

    # --------------------------------------------------
    # GET ALL CONVERSATIONS
    # --------------------------------------------------

    def get_conversations(self):

        with self.get_connection() as connection:

            rows = connection.execute("""
                SELECT *
                FROM conversations
                ORDER BY updated_at DESC
            """).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # --------------------------------------------------
    # GET MESSAGES OF A CONVERSATION
    # --------------------------------------------------

    def get_messages(self, conversation_id):

        with self.get_connection() as connection:

            rows = connection.execute("""
                SELECT *
                FROM messages
                WHERE conversation_id = ?
                ORDER BY message_id ASC
            """, (
                conversation_id,
            )).fetchall()

        messages = []

        for row in rows:

            message = dict(row)

            # Convert stored JSON sources back into Python objects
            try:
                message["sources"] = json.loads(
                    message["sources"] or "[]"
                )

            except (json.JSONDecodeError, TypeError):
                message["sources"] = []

            messages.append(message)

        return messages

    # --------------------------------------------------
    # DELETE CONVERSATION
    # --------------------------------------------------

    def delete_conversation(self, conversation_id):

        with self.get_connection() as connection:

            connection.execute("""
                DELETE FROM conversations
                WHERE conversation_id = ?
            """, (
                conversation_id,
            ))

    # --------------------------------------------------
    # DELETE ALL CONVERSATIONS
    # --------------------------------------------------

    def delete_all_conversations(self):

        with self.get_connection() as connection:

            connection.execute("""
                DELETE FROM conversations
            """)

    # --------------------------------------------------
    # GET A SINGLE CONVERSATION
    # --------------------------------------------------

    def get_conversation(self, conversation_id):

        with self.get_connection() as connection:

            row = connection.execute("""
                SELECT *
                FROM conversations
                WHERE conversation_id = ?
            """, (
                conversation_id,
            )).fetchone()

        return dict(row) if row else None
