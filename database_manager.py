# database_manager.py

import sqlite3
from pathlib import Path

class DatabaseManager:
    def __init__(self, backup_dir, backup_file='database.db'):
        """
        Initialize the DatabaseManager with in-memory SQLite and the ability to backup to disk.

        :param backup_dir: Directory where the database file will be stored.
        :param backup_file: Name of the backup database file (default is 'database.db').
        """
        self.backup_dir = Path(backup_dir)
        self.backup_file = self.backup_dir / backup_file

        # Ensure the backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Connect to in-memory SQLite database
        self.conn = sqlite3.connect(':memory:')
        self.enable_wal()
        self.create_tables()

        # Load data from disk if backup exists
        if self.backup_file.exists():
            self.load_from_disk()

    def enable_wal(self):
        """Enable Write-Ahead Logging (WAL) for better concurrency when backing up to disk."""
        with self.conn:
            self.conn.execute("PRAGMA journal_mode=WAL;")
        print("WAL mode enabled for SQLite in-memory database.")

    def create_tables(self):
        """Create necessary tables in the in-memory SQLite database."""
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
        """Update file data in the in-memory SQLite database."""
        file_path_str = str(file_path) if isinstance(file_path, Path) else file_path
        with self.conn:
            self.conn.execute("""
            INSERT OR REPLACE INTO file_hashes (file_path, hash_code, mod_time, file_size, last_backup)
            VALUES (?, ?, ?, ?, datetime('now'))
            """, (file_path_str, hash_code, mod_time, file_size))

    def get_file_hash(self, file_path):
        """Retrieve the hash code of a file from the in-memory SQLite database."""
        file_path_str = str(file_path) if isinstance(file_path, Path) else file_path
        cur = self.conn.cursor()
        cur.execute("SELECT hash_code FROM file_hashes WHERE file_path = ?", (file_path_str,))
        row = cur.fetchone()
        return row[0] if row else None

    def get_file_metadata(self, file_path):
        """Retrieve file metadata (mod_time, file_size) from the in-memory SQLite database."""
        file_path_str = str(file_path) if isinstance(file_path, Path) else file_path
        cur = self.conn.cursor()
        cur.execute("SELECT mod_time, file_size FROM file_hashes WHERE file_path = ?", (file_path_str,))
        row = cur.fetchone()
        return row if row else (None, None)

    def load_from_disk(self):
        """Load the SQLite database from a file on disk into the in-memory database."""
        with sqlite3.connect(self.backup_file) as disk_conn:
            disk_conn.backup(self.conn)
        print(f"Loaded database from {self.backup_file}")

    def backup_to_disk(self):
        """Backup the in-memory database to a file on disk."""
        with sqlite3.connect(self.backup_file) as disk_conn:
            self.conn.backup(disk_conn)
        print(f"Backed up database to {self.backup_file}")

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")