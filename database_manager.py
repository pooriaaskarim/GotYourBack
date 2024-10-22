# database_manager.py

import sqlite3

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = self._connect()
        self.create_tables()

    def _connect(self):
        """Establishes a new connection to the database and enables WAL mode."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")  # Enable WAL mode for concurrent writes
        return conn

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS file_hashes (
                file_path TEXT PRIMARY KEY,
                hash_code TEXT,
                last_backup DATETIME,
                mod_time REAL,
                file_size INTEGER
            )
            """)

    def update_file_data(self, file_path, hash_code, mod_time, file_size):
        with self.conn:
            self.conn.execute("""
            INSERT OR REPLACE INTO file_hashes (file_path, hash_code, last_backup, mod_time, file_size)
            VALUES (?, ?, datetime('now'), ?, ?)
            """, (str(file_path), hash_code, mod_time, file_size))

    def get_file_hash(self, file_path):
        cur = self.conn.cursor()
        cur.execute("SELECT hash_code FROM file_hashes WHERE file_path = ?", (str(file_path),))
        row = cur.fetchone()
        return row[0] if row else None

    def get_file_metadata(self, file_path):
        cur = self.conn.cursor()
        cur.execute("SELECT mod_time, file_size FROM file_hashes WHERE file_path = ?", (str(file_path),))
        row = cur.fetchone()
        return row if row else (None, None)