# versioning_manager.py

from pathlib import Path
import shutil

class VersioningManager:
    def __init__(self, backup_root_dir):
        self.backup_root_dir = Path(backup_root_dir)

    def create_versioned_backup(self, file_path, relative_path):
        """
        Creates a versioned backup by placing the file in a versioned folder,
        while preserving its relative directory structure.

        :param file_path: The full path to the file to back up.
        :param relative_path: The relative path to maintain inside the backup folder.
        """
        # Backup directory should preserve the relative path of the original directory
        backup_dir = self.backup_root_dir / relative_path.parent

        # Ensure the backup directory exists before proceeding
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Determine the next version folder (v1, v2, etc.)
        next_version = self.get_next_version(backup_dir)
        version_dir = backup_dir / f"v{next_version}"
        version_dir.mkdir(parents=True, exist_ok=True)  # Ensure that the directory exists

        # Copy the file to the versioned folder
        backup_file_path = version_dir / file_path.name
        shutil.copy2(file_path, backup_file_path)

        return str(backup_file_path)

    def get_next_version(self, backup_dir):
        """
        Returns the next version number for the backup directory.
        Ensures the backup directory exists before checking for versions.
        """
        # Ensure the backup directory exists to avoid FileNotFoundError
        backup_dir.mkdir(parents=True, exist_ok=True)  # Create backup directory if it doesn't exist

        # Check for existing version folders (v1, v2, etc.)
        existing_versions = [d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith('v')]
        if not existing_versions:
            return 1
        # Extract version numbers and find the next one
        existing_versions = [int(d.name[1:]) for d in existing_versions]
        return max(existing_versions) + 1