# main.py

from multiprocessing import Pool
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

def process_file(file_data):
    """
    Worker function for processing a file in parallel.

    :param file_data: Tuple containing file_path and source_base_dir
    """
    file_path, source_base_dir = file_data

    # Each worker gets its own DatabaseManager instance
    db_manager = DatabaseManager(config.DATABASE_DIR + 'database.db')
    backup_manager = BackupManager(db_manager)

    # Backup the file
    backup_manager.backup_file(file_path, source_base_dir)

def main():
    initialize()

    # List of files and directories to back up
    if len(os.sys.argv) > 1:
        paths_to_backup = os.sys.argv[1:]
    else:
        paths_to_backup = [
            '/home/ono/Projects/gitting_the_git',
            '/home/ono/.zshrc'
        ]  # Replace with actual files or directories to back up

    # Prepare data for multiprocessing
    file_data = []
    for path in paths_to_backup:
        source_path = Path(path).resolve()
        if source_path.is_file():
            file_data.append((source_path, source_path.parent))
        elif source_path.is_dir():
            files_to_backup = scan_directory(source_path)
            for file_path in files_to_backup:
                file_data.append((file_path, source_path))
        else:
            print(f"Warning: {source_path} is not a valid file or directory.")

    # Use multiprocessing to process files in parallel
    with Pool() as pool:
        pool.map(process_file, file_data)

if __name__ == "__main__":
    main()