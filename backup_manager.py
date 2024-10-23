# backup_manager.py

import logging
from file_scanner import calculate_file_hash
from database_manager import DatabaseManager
from pathlib import Path
from colorama import Fore, Style
import shutil
import config
import os

class BackupManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging to use the LOGS_DIR from config."""
        logs_dir = Path(config.LOGS_DIR)
        logs_dir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            filename=f"{logs_dir}/backup.log",
            filemode="a",
            format="%(asctime)s - %(levelname)s - %(message)s",
            level=logging.INFO  # Use INFO level to avoid verbose DEBUG logs unless necessary
        )

    def backup_file(self, file_path, source_base_dir):
        """
        Backup a file if its checksum (hash) has changed since the last backup,
        or if the backup file is missing.

        :param file_path: Full path to the file to be backed up.
        :param source_base_dir: Base directory to calculate relative path for backup.
        """
        try:
            file_path = Path(file_path).resolve()  # Resolve the absolute path
            relative_path, backup_path = self._prepare_backup_paths(file_path, source_base_dir)

            # Calculate file hash (checksum) once
            file_hash = calculate_file_hash(file_path, config.HASH_ALGORITHM)

            # Only proceed if the file needs backing up (missing or modified)
            if self._should_backup_file(file_path, backup_path, file_hash):
                self._perform_backup(file_path, backup_path, file_hash)
            else:
                print(f"{Fore.YELLOW}Skipped {file_path}: no changes detected (checksum match).{Style.RESET_ALL}")
                logging.info(f"Skipped {file_path}: no changes detected (checksum match).")

        except FileNotFoundError:
            self._log_error(f"Error: {file_path} not found.")
        except PermissionError:
            self._log_error(f"Error: Permission denied for {file_path}.")
        except Exception as e:
            self._log_error(f"Unexpected error: {str(e)}")

    def _prepare_backup_paths(self, file_path, source_base_dir):
        """
        Prepare the relative and backup paths for a file.

        :param file_path: Full path of the source file.
        :param source_base_dir: Base directory of the source.
        :return: Tuple containing the relative path and backup path.
        """
        # Ensure each source has its own backup directory by adding the source_base_dir name
        source_name = source_base_dir.name

        # Calculate the relative path of the file within its source directory
        relative_path = file_path.relative_to(source_base_dir)

        # Construct the backup path so each source gets its own place inside BACKUP_DIR
        backup_path = Path(config.BACKUP_DIR) / source_name / relative_path

        # Ensure that the parent directory of the backup file exists
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        return relative_path, backup_path

    def _should_backup_file(self, file_path, backup_path, file_hash):
        """
        Determine if the file should be backed up (checksum mismatch or missing backup).

        :param file_path: Full path to the source file.
        :param backup_path: Full path to the backup file.
        :param file_hash: Hash of the source file.
        :return: Boolean indicating whether to back up the file.
        """
        # If backup file is missing, return True (needs backup)
        if not backup_path.exists():
            print(f"{Fore.GREEN}Backing up {file_path}: backup file missing.{Style.RESET_ALL}")
            logging.info(f"Backing up {file_path}: backup file missing.")
            return True

        # Compare the file hash with the stored hash from the database
        stored_hash = self.db_manager.get_file_hash(file_path)
        if file_hash != stored_hash:
            return True

        # No backup needed if file is unchanged
        return False

    def _perform_backup(self, file_path, backup_path, file_hash):
        """
        Perform the backup by copying the file and updating the database.

        :param file_path: Full path to the source file.
        :param backup_path: Full path to the destination (backup) file.
        :param file_hash: Hash of the source file.
        """
        try:
            self._copy_file(file_path, backup_path)
            self._update_db(file_path, file_hash)
            print(f"{Fore.GREEN}Backed up {file_path} to {backup_path}{Style.RESET_ALL}")
            logging.info(f"Backed up {file_path} to {backup_path}")
        except Exception as e:
            self._log_error(f"Failed to backup {file_path} to {backup_path}: {str(e)}")

    def _update_db(self, file_path, file_hash):
        """Update the database with file metadata and hash."""
        mod_time = os.path.getmtime(file_path)
        file_size = os.path.getsize(file_path)
        self.db_manager.update_file_data(file_path, file_hash, mod_time, file_size)

    def _copy_file(self, source, destination):
        """Handles file copying with error logging."""
        try:
            shutil.copy2(source, destination)
            print(f"{Fore.BLUE}Copying {source} to {destination}{Style.RESET_ALL}")
            logging.debug(f"Copying {source} to {destination}")
        except Exception as e:
            self._log_error(f"Failed to copy {source} to {destination}: {str(e)}")

    def _log_error(self, message):
        """Helper to log errors and display them in red."""
        print(f"{Fore.RED}{message}{Style.RESET_ALL}")
        logging.error(message)

    def remove_deleted_backups(self, source_base_dir):
        """
        Remove backup files that no longer exist in the source directory.

        :param source_base_dir: The base directory of the source to scan.
        """
        backup_dir = Path(config.BACKUP_DIR) / source_base_dir.name
        for backup_file in backup_dir.rglob('*'):
            relative_path = backup_file.relative_to(Path(config.BACKUP_DIR) / source_base_dir.name)
            source_file = source_base_dir / relative_path

            if not source_file.exists():
                self._delete_file(backup_file)

    def _delete_file(self, file_path):
        """Handles file deletion with error logging."""
        try:
            file_path.unlink()
            print(f"{Fore.RED}Deleted {file_path}{Style.RESET_ALL}")
            logging.debug(f"Deleted {file_path}")
        except Exception as e:
            self._log_error(f"Failed to delete {file_path}: {str(e)}")