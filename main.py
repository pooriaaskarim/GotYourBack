# main.py

from pathlib import Path
from database_manager import DatabaseManager
from backup_manager import BackupManager
from file_scanner import scan_directory
import config
import os

def initialize():
    """Ensure that all necessary directories exist before running the backup."""
    app_dirs = [Path(x) for x in [config.BASE_DIR, config.BACKUP_DIR, config.LOGS_DIR, config.DATABASE_DIR]]
    for directory in app_dirs:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f'Created directory: {directory}')

def main():
    initialize()

    # Initialize the DatabaseManager with in-memory database and backup/reload mechanism using DATABASE_DIR
    db_manager = DatabaseManager(config.DATABASE_DIR)
    backup_manager = BackupManager(db_manager)

    # List of files and directories to back up
    if len(os.sys.argv) > 1:
        paths_to_backup = os.sys.argv[1:]
    else:
        paths_to_backup = [
            '/home/ono/Projects/gitting_the_git',
            '/home/ono/Projects/Audiong',
            '/home/ono/.zshrc'
        ]  # Replace with actual files or directories to back up

    # Process each path for backup
    for path in paths_to_backup:
        source_path = Path(path).resolve()

        if source_path.is_file():
            # Backup single file to BACKUP_DIR
            backup_manager.backup_file(source_path, source_path.parent)
        elif source_path.is_dir():
            # Backup all files in the directory to BACKUP_DIR
            files_to_backup = scan_directory(source_path)
            for file_path in files_to_backup:
                backup_manager.backup_file(file_path, source_path)
        else:
            print(f"Warning: {source_path} is not a valid file or directory.")

    # Backup the in-memory database to disk in DATABASE_DIR before exiting
    db_manager.backup_to_disk()

    # Close the database connection
    db_manager.close()

if __name__ == "__main__":
    main()