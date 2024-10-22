import logging
from file_scanner import calculate_file_hash
from database_manager import DatabaseManager
from pathlib import Path
from colorama import Fore, Style
import shutil
import config
import os
from datetime import datetime
from multiprocessing import Pool

class BackupManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

        # Ensure that logs directory exists
        logs_dir = Path(config.LOGS_DIR)
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Configure logging to use the LOGS_DIR from config.py
        logging.basicConfig(
            filename=f"{logs_dir}/backup.log",
            filemode="a",
            format="%(asctime)s - %(levelname)s - %(message)s",
            level=logging.DEBUG  # Set to DEBUG level for detailed logging
        )

    def backup_file(self, file_path, source_base_dir):
        """
        Backs up a file if it has changed since the last backup, maintaining its relative path
        inside the backup directory structure.

        :param file_path: The full path to the file to be backed up.
        :param source_base_dir: The base directory of the source (to calculate the relative path).
        """
        try:
            file_path = Path(file_path).resolve()  # Get the absolute path

            # Calculate the relative path starting from the source_base_dir
            relative_path = file_path.relative_to(source_base_dir)  # Relative path inside the source directory

            # Full backup path for the file inside BACKUP_DIR
            backup_dir = Path(config.BACKUP_DIR) / source_base_dir.name / relative_path.parent
            backup_dir.mkdir(parents=True, exist_ok=True)  # Ensure that the backup directory exists

            # Check file metadata (modification time and size) before calculating the hash
            current_mod_time = os.path.getmtime(file_path)
            current_size = os.path.getsize(file_path)

            stored_mod_time, stored_size = self.db_manager.get_file_metadata(file_path)

            # Skip file if both modification time and size are the same
            if stored_mod_time == current_mod_time and stored_size == current_size:
                print(f"{Fore.YELLOW}Skipped {file_path}: no changes detected.{Style.RESET_ALL}")
                logging.info(f"Skipped {file_path}: no changes detected.")
                return

            # Calculate the file hash and compare with the stored hash
            file_hash = calculate_file_hash(file_path, config.HASH_ALGORITHM)
            stored_hash = self.db_manager.get_file_hash(file_path)

            if file_hash != stored_hash:
                # Copy the file to the backup directory
                backup_path = Path(config.BACKUP_DIR) / source_base_dir.name / relative_path
                self._copy_file(file_path, backup_path)

                # Log success and update both hash and metadata
                self.db_manager.update_file_data(file_path, file_hash, current_mod_time, current_size)
                print(f"{Fore.GREEN}Backed up {file_path} to {backup_path}{Style.RESET_ALL}")
                logging.info(f"Backed up {file_path} to {backup_path}")

            else:
                # Log skipping
                print(f"{Fore.YELLOW}Skipped {file_path}: no changes detected.{Style.RESET_ALL}")
                logging.info(f"Skipped {file_path}: no changes detected.")

        except FileNotFoundError:
            print(f"{Fore.RED}Error: {file_path} not found.{Style.RESET_ALL}")
            logging.error(f"Error: {file_path} not found.")
        except PermissionError:
            print(f"{Fore.RED}Error: Permission denied for {file_path}.{Style.RESET_ALL}")
            logging.error(f"Error: Permission denied for {file_path}.")
        except Exception as e:
            print(f"{Fore.RED}Unexpected error: {str(e)}{Style.RESET_ALL}")
            logging.error(f"Unexpected error: {str(e)}")

    def _copy_file(self, source, destination):
        """Handles file copying with error logging."""
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)  # Ensure destination directory exists
            shutil.copy2(source, destination)
            print(f"{Fore.BLUE}Copying {source} to {destination}{Style.RESET_ALL}")
            logging.debug(f"Copying {source} to {destination}")
        except Exception as e:
            print(f"{Fore.RED}Failed to copy {source} to {destination}: {str(e)}{Style.RESET_ALL}")
            logging.error(f"Failed to copy {source} to {destination}: {str(e)}")