import sqlite3
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.db_path = self._get_db_path()
        self._init_tables()

    def _get_db_path(self) -> Path:
        """Get user‑specific AppData folder for ClauseCompare."""
        home = Path.home()
        if 'nt' in __import__('os').name:  # Windows
            app_data = home / 'AppData' / 'Local' / 'ClauseCompare'
        else:
            app_data = home / '.config' / 'clausecompare'
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data / 'clausecompare.db'

    def _init_tables(self):
        """Create tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Documents
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,  -- 'company' or 'third_party'
                    file_path TEXT,          -- optional, for reference
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_compared BOOLEAN DEFAULT 0,
                    comparison_result_id INTEGER
                )
            """)
            # Clauses
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clauses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    clause_number TEXT,
                    text TEXT NOT NULL,
                    embedding BLOB,           -- numpy array as bytes
                    metadata TEXT,            -- JSON
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)
            # Comparison results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comparison_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc1_id INTEGER NOT NULL,
                    doc2_id INTEGER NOT NULL,
                    result_json TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doc1_id) REFERENCES documents(id),
                    FOREIGN KEY (doc2_id) REFERENCES documents(id)
                )
            """)
            conn.commit()

    def get_connection(self):
        """Return a SQLite connection with row_factory = dict for convenience."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add_document(self, name: str, category: str, file_path: str = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO documents (name, category, file_path) VALUES (?, ?, ?)",
                (name, category, file_path)
            )
            conn.commit()
            return cursor.lastrowid

    def get_all_documents(self, category: str = None) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute(
                    "SELECT * FROM documents WHERE category = ? ORDER BY uploaded_at DESC",
                    (category,)
                )
            else:
                cursor.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_document(self, doc_id: int) -> Dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_document_compared(self, doc_id: int, result_id: int = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if result_id is not None:
                cursor.execute(
                    "UPDATE documents SET is_compared = 1, comparison_result_id = ? WHERE id = ?",
                    (result_id, doc_id)
                )
            else:
                cursor.execute(
                    "UPDATE documents SET is_compared = 1 WHERE id = ?",
                    (doc_id,)
                )
            conn.commit()

    def add_clauses(self, document_id: int, clauses: List[Dict]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for clause in clauses:
                embedding_blob = None
                if 'embedding' in clause and clause['embedding'] is not None:
                    embedding_blob = clause['embedding'].tobytes() if hasattr(clause['embedding'], 'tobytes') else None
                metadata_json = json.dumps(clause.get('metadata', {}))
                cursor.execute(
                    """
                    INSERT INTO clauses (document_id, clause_number, text, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (document_id, clause.get('number', ''), clause['text'], embedding_blob, metadata_json)
                )
            conn.commit()

    def get_clauses(self, document_id: int) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clauses WHERE document_id = ? ORDER BY id", (document_id,))
            rows = cursor.fetchall()
            clauses = []
            for row in rows:
                clause = dict(row)
                if clause['embedding']:
                    clause['embedding'] = np.frombuffer(clause['embedding'], dtype=np.float32)
                else:
                    clause['embedding'] = None
                clause['metadata'] = json.loads(clause['metadata'])
                clauses.append(clause)
            return clauses

    def save_comparison_result(self, doc1_id: int, doc2_id: int, result_json: dict) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO comparison_results (doc1_id, doc2_id, result_json) VALUES (?, ?, ?)",
                (doc1_id, doc2_id, json.dumps(result_json))
            )
            conn.commit()
            return cursor.lastrowid

    def get_comparison_result(self, result_id: int) -> Dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM comparison_results WHERE id = ?", (result_id,))
            row = cursor.fetchone()
            if row:
                res = dict(row)
                res['result_json'] = json.loads(res['result_json'])
                return res
            return None


    def get_stats(self) -> Dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM documents WHERE is_compared = 1")
            compared = cursor.fetchone()[0]
            pending = total - compared
            return {
                'total': total,
                'compared': compared,
                'pending': pending
            }