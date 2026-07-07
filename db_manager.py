import sqlite3
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils import sanitize_for_json

class DatabaseManager:
    def __init__(self):
        self.db_path = self._get_db_path()
        self._init_tables()
        self._migrate_tables()

    def _get_db_path(self) -> Path:
        home = Path.home()
        if 'nt' in __import__('os').name:
            app_data = home / 'AppData' / 'Local' / 'ClauseCompare'
        else:
            app_data = home / '.config' / 'clausecompare'
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data / 'clausecompare.db'

    def _init_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    file_path TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_compared BOOLEAN DEFAULT 0,
                    comparison_result_id INTEGER
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clauses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    clause_number TEXT,
                    text TEXT NOT NULL,
                    embedding BLOB,
                    metadata TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comparison_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc1_id INTEGER NOT NULL,
                    doc2_id INTEGER NOT NULL,
                    result_json TEXT NOT NULL,
                    comparison_name TEXT DEFAULT '',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doc1_id) REFERENCES documents(id),
                    FOREIGN KEY (doc2_id) REFERENCES documents(id)
                )
            """)
            conn.commit()

    def _migrate_tables(self):
        """Add comparison_name column if it doesn't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Check if comparison_name column exists
            cursor.execute("PRAGMA table_info(comparison_results)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'comparison_name' not in columns:
                cursor.execute("ALTER TABLE comparison_results ADD COLUMN comparison_name TEXT DEFAULT ''")
                conn.commit()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ---- Document operations ----
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

    def delete_document(self, doc_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()

    # ---- Clause operations ----
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

    # ---- Comparison results ----
    def save_comparison_result(self, doc1_id: int, doc2_id: int, result_json: dict, name: str = "") -> int:
        sanitised = sanitize_for_json(result_json)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO comparison_results (doc1_id, doc2_id, result_json, comparison_name) VALUES (?, ?, ?, ?)",
                (doc1_id, doc2_id, json.dumps(sanitised), name)
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

    def get_comparison_with_docs(self, result_id: int) -> Dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cr.*, 
                       d1.name as doc1_name, d2.name as doc2_name,
                       d1.id as doc1_id, d2.id as doc2_id
                FROM comparison_results cr
                JOIN documents d1 ON cr.doc1_id = d1.id
                JOIN documents d2 ON cr.doc2_id = d2.id
                WHERE cr.id = ?
            """, (result_id,))
            row = cursor.fetchone()
            if row:
                res = dict(row)
                res['result_json'] = json.loads(res['result_json'])
                return res
            return None

    def get_all_comparisons(self) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cr.id, cr.timestamp, cr.comparison_name,
                       d1.name as doc1_name, d2.name as doc2_name,
                       d1.id as doc1_id, d2.id as doc2_id
                FROM comparison_results cr
                JOIN documents d1 ON cr.doc1_id = d1.id
                JOIN documents d2 ON cr.doc2_id = d2.id
                ORDER BY cr.timestamp DESC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

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