"""
dgai.memory.storage.sqlite — Implémentation SQLite thread-safe et transactionnelle du stockage mémoire.
"""

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from dgai.memory.errors import StorageError
from dgai.memory.storage.base import BaseMemoryStorage
from dgai.memory.types import (
    ConfidenceLevel,
    Conversation,
    ConversationMessage,
    ConversationSummary,
    LongTermMemory,
    MemoryCategory,
    SessionState,
)


class SQLiteMemoryStorage(BaseMemoryStorage):
    """
    Adaptateur de stockage SQLite avec requêtes paramétrées, intégrité référentielle (FK cascade),
    isolation stricte par user_id et gestion de concurrence multi-threads.
    """

    def __init__(self, db_path: Path | str = ":memory:"):
        self.db_path = str(db_path)
        self._lock = threading.Lock()
        # En mode :memory:, garder une connexion persistante partagée pour ne pas perdre les tables
        self._memory_conn: Optional[sqlite3.Connection] = None
        if self.db_path == ":memory:":
            self._memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._memory_conn.row_factory = sqlite3.Row
            self._memory_conn.execute("PRAGMA foreign_keys = ON;")
        else:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._memory_conn is not None:
            return self._memory_conn
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _close_connection(self, conn: sqlite3.Connection) -> None:
        if conn is not self._memory_conn:
            conn.close()

    def _init_db(self) -> None:
        """Initialise les tables et index nécessaires."""
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    # 1. Table des conversations
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS conversations (
                            id TEXT PRIMARY KEY,
                            user_id TEXT NOT NULL,
                            title TEXT NOT NULL,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL,
                            metadata TEXT NOT NULL
                        );
                    """)
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id);")

                    # 2. Table des messages (cascade delete sur conversation)
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS conversation_messages (
                            id TEXT PRIMARY KEY,
                            conversation_id TEXT NOT NULL,
                            user_id TEXT NOT NULL,
                            role TEXT NOT NULL,
                            content TEXT NOT NULL,
                            created_at TEXT NOT NULL,
                            metadata TEXT NOT NULL,
                            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                        );
                    """)
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_conv_user ON conversation_messages(conversation_id, user_id);")

                    # 3. Table des mémoires à long terme
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS long_term_memories (
                            id TEXT PRIMARY KEY,
                            user_id TEXT NOT NULL,
                            category TEXT NOT NULL,
                            content TEXT NOT NULL,
                            confidence TEXT NOT NULL,
                            source_conversation_id TEXT,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL,
                            expires_at TEXT,
                            is_deleted INTEGER NOT NULL DEFAULT 0
                        );
                    """)
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_ltm_user ON long_term_memories(user_id);")

                    # 4. Table des résumés de conversation
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS conversation_summaries (
                            conversation_id TEXT PRIMARY KEY,
                            user_id TEXT NOT NULL,
                            summary TEXT NOT NULL,
                            main_topics TEXT NOT NULL,
                            important_facts TEXT NOT NULL,
                            decisions TEXT NOT NULL,
                            open_tasks TEXT NOT NULL,
                            updated_at TEXT NOT NULL,
                            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                        );
                    """)

                    # 5. Table des sessions temporaires
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS session_states (
                            conversation_id TEXT PRIMARY KEY,
                            user_id TEXT NOT NULL,
                            current_topic TEXT,
                            goals TEXT NOT NULL,
                            decisions TEXT NOT NULL,
                            open_tasks TEXT NOT NULL,
                            updated_at TEXT NOT NULL,
                            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                        );
                    """)
            except sqlite3.Error as e:
                raise StorageError(f"Erreur d'initialisation de la base SQLite : {str(e)}") from e
            finally:
                self._close_connection(conn)

    def save_conversation(self, conversation: Conversation) -> Conversation:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("""
                        INSERT INTO conversations (id, user_id, title, created_at, updated_at, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            title = excluded.title,
                            updated_at = excluded.updated_at,
                            metadata = excluded.metadata;
                    """, (
                        conversation.id,
                        conversation.user_id,
                        conversation.title,
                        conversation.created_at,
                        conversation.updated_at,
                        json.dumps(conversation.metadata)
                    ))
                return conversation
            except sqlite3.Error as e:
                raise StorageError(f"Échec de sauvegarde de la conversation : {str(e)}") from e
            finally:
                self._close_connection(conn)

    def get_conversation(self, user_id: str, conversation_id: str) -> Optional[Conversation]:
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT id, user_id, title, created_at, updated_at, metadata
                FROM conversations
                WHERE id = ? AND user_id = ?;
            """, (conversation_id, user_id))
            row = cursor.fetchone()
            if not row:
                return None
            return Conversation(
                id=row["id"],
                user_id=row["user_id"],
                title=row["title"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata=json.loads(row["metadata"])
            )
        finally:
            self._close_connection(conn)

    def list_conversations(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Conversation]:
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT id, user_id, title, created_at, updated_at, metadata
                FROM conversations
                WHERE user_id = ?
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?;
            """, (user_id, limit, offset))
            rows = cursor.fetchall()
            return [
                Conversation(
                    id=row["id"],
                    user_id=row["user_id"],
                    title=row["title"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    metadata=json.loads(row["metadata"])
                )
                for row in rows
            ]
        finally:
            self._close_connection(conn)

    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    cursor = conn.execute("""
                        DELETE FROM conversations
                        WHERE id = ? AND user_id = ?;
                    """, (conversation_id, user_id))
                    return cursor.rowcount > 0
            finally:
                self._close_connection(conn)

    def save_message(self, message: ConversationMessage) -> ConversationMessage:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("""
                        INSERT INTO conversation_messages (id, conversation_id, user_id, role, content, created_at, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?);
                    """, (
                        message.id,
                        message.conversation_id,
                        message.user_id,
                        message.role,
                        message.content,
                        message.created_at,
                        json.dumps(message.metadata)
                    ))
                    # Mettre à jour l'horodatage de la conversation parente
                    conn.execute("""
                        UPDATE conversations SET updated_at = ? WHERE id = ? AND user_id = ?;
                    """, (message.created_at, message.conversation_id, message.user_id))
                return message
            except sqlite3.Error as e:
                raise StorageError(f"Échec de sauvegarde du message : {str(e)}") from e
            finally:
                self._close_connection(conn)

    def get_messages(
        self,
        user_id: str,
        conversation_id: str,
        limit: int = 50,
        before_id: Optional[str] = None
    ) -> List[ConversationMessage]:
        conn = self._get_connection()
        try:
            query = """
                SELECT id, conversation_id, user_id, role, content, created_at, metadata
                FROM conversation_messages
                WHERE conversation_id = ? AND user_id = ?
                ORDER BY created_at ASC
                LIMIT ?;
            """
            cursor = conn.execute(query, (conversation_id, user_id, limit))
            rows = cursor.fetchall()
            return [
                ConversationMessage(
                    id=row["id"],
                    conversation_id=row["conversation_id"],
                    user_id=row["user_id"],
                    role=row["role"],
                    content=row["content"],
                    created_at=row["created_at"],
                    metadata=json.loads(row["metadata"])
                )
                for row in rows
            ]
        finally:
            self._close_connection(conn)

    def save_long_term_memory(self, memory: LongTermMemory) -> LongTermMemory:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("""
                        INSERT INTO long_term_memories (
                            id, user_id, category, content, confidence,
                            source_conversation_id, created_at, updated_at, expires_at, is_deleted
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            category = excluded.category,
                            content = excluded.content,
                            confidence = excluded.confidence,
                            updated_at = excluded.updated_at,
                            expires_at = excluded.expires_at,
                            is_deleted = excluded.is_deleted;
                    """, (
                        memory.id,
                        memory.user_id,
                        memory.category.value,
                        memory.content,
                        memory.confidence.value,
                        memory.source_conversation_id,
                        memory.created_at,
                        memory.updated_at,
                        memory.expires_at,
                        1 if memory.is_deleted else 0
                    ))
                return memory
            except sqlite3.Error as e:
                raise StorageError(f"Échec d'enregistrement de la mémoire : {str(e)}") from e
            finally:
                self._close_connection(conn)

    def get_long_term_memory(self, user_id: str, memory_id: str) -> Optional[LongTermMemory]:
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT id, user_id, category, content, confidence,
                       source_conversation_id, created_at, updated_at, expires_at, is_deleted
                FROM long_term_memories
                WHERE id = ? AND user_id = ? AND is_deleted = 0;
            """, (memory_id, user_id))
            row = cursor.fetchone()
            if not row:
                return None
            return LongTermMemory(
                id=row["id"],
                user_id=row["user_id"],
                category=MemoryCategory(row["category"]),
                content=row["content"],
                confidence=ConfidenceLevel(row["confidence"]),
                source_conversation_id=row["source_conversation_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                expires_at=row["expires_at"],
                is_deleted=bool(row["is_deleted"])
            )
        finally:
            self._close_connection(conn)

    def list_long_term_memories(
        self,
        user_id: str,
        category: Optional[str] = None,
        include_expired: bool = False
    ) -> List[LongTermMemory]:
        conn = self._get_connection()
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            query = "SELECT * FROM long_term_memories WHERE user_id = ? AND is_deleted = 0"
            params: List[object] = [user_id]

            if category:
                query += " AND category = ?"
                params.append(category)

            if not include_expired:
                query += " AND (expires_at IS NULL OR expires_at > ?)"
                params.append(now_iso)

            query += " ORDER BY created_at DESC;"
            cursor = conn.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [
                LongTermMemory(
                    id=r["id"],
                    user_id=r["user_id"],
                    category=MemoryCategory(r["category"]),
                    content=r["content"],
                    confidence=ConfidenceLevel(r["confidence"]),
                    source_conversation_id=r["source_conversation_id"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    expires_at=r["expires_at"],
                    is_deleted=bool(r["is_deleted"])
                )
                for r in rows
            ]
        finally:
            self._close_connection(conn)

    def delete_long_term_memory(self, user_id: str, memory_id: str) -> bool:
        """Suppression définitive (DELETE effectif) du souvenir."""
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    cursor = conn.execute("""
                        DELETE FROM long_term_memories
                        WHERE id = ? AND user_id = ?;
                    """, (memory_id, user_id))
                    return cursor.rowcount > 0
            finally:
                self._close_connection(conn)

    def delete_all_user_memories(self, user_id: str) -> int:
        """Purge complète des données de mémoires durables d'un utilisateur."""
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    cursor = conn.execute("""
                        DELETE FROM long_term_memories WHERE user_id = ?;
                    """, (user_id,))
                    return cursor.rowcount
            finally:
                self._close_connection(conn)

    def save_summary(self, summary: ConversationSummary) -> ConversationSummary:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("""
                        INSERT INTO conversation_summaries (
                            conversation_id, user_id, summary, main_topics,
                            important_facts, decisions, open_tasks, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(conversation_id) DO UPDATE SET
                            summary = excluded.summary,
                            main_topics = excluded.main_topics,
                            important_facts = excluded.important_facts,
                            decisions = excluded.decisions,
                            open_tasks = excluded.open_tasks,
                            updated_at = excluded.updated_at;
                    """, (
                        summary.conversation_id,
                        summary.user_id,
                        summary.summary,
                        json.dumps(summary.main_topics),
                        json.dumps(summary.important_facts),
                        json.dumps(summary.decisions),
                        json.dumps(summary.open_tasks),
                        summary.updated_at
                    ))
                return summary
            finally:
                self._close_connection(conn)

    def get_summary(self, user_id: str, conversation_id: str) -> Optional[ConversationSummary]:
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM conversation_summaries
                WHERE conversation_id = ? AND user_id = ?;
            """, (conversation_id, user_id))
            row = cursor.fetchone()
            if not row:
                return None
            return ConversationSummary(
                conversation_id=row["conversation_id"],
                user_id=row["user_id"],
                summary=row["summary"],
                main_topics=json.loads(row["main_topics"]),
                important_facts=json.loads(row["important_facts"]),
                decisions=json.loads(row["decisions"]),
                open_tasks=json.loads(row["open_tasks"]),
                updated_at=row["updated_at"]
            )
        finally:
            self._close_connection(conn)

    def save_session_state(self, state: SessionState) -> SessionState:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("""
                        INSERT INTO session_states (
                            conversation_id, user_id, current_topic, goals,
                            decisions, open_tasks, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(conversation_id) DO UPDATE SET
                            current_topic = excluded.current_topic,
                            goals = excluded.goals,
                            decisions = excluded.decisions,
                            open_tasks = excluded.open_tasks,
                            updated_at = excluded.updated_at;
                    """, (
                        state.conversation_id,
                        state.user_id,
                        state.current_topic,
                        json.dumps(state.goals),
                        json.dumps(state.decisions),
                        json.dumps(state.open_tasks),
                        state.updated_at
                    ))
                return state
            finally:
                self._close_connection(conn)

    def get_session_state(self, user_id: str, conversation_id: str) -> Optional[SessionState]:
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM session_states
                WHERE conversation_id = ? AND user_id = ?;
            """, (conversation_id, user_id))
            row = cursor.fetchone()
            if not row:
                return None
            return SessionState(
                conversation_id=row["conversation_id"],
                user_id=row["user_id"],
                current_topic=row["current_topic"],
                goals=json.loads(row["goals"]),
                decisions=json.loads(row["decisions"]),
                open_tasks=json.loads(row["open_tasks"]),
                updated_at=row["updated_at"]
            )
        finally:
            self._close_connection(conn)
