# file_scanner.py

import hashlib
from pathlib import Path


def calculate_file_hash(file_path, algorithm='sha256'):
    """Calculates the hash of a file."""
    hash_func = getattr(hashlib, algorithm)()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def scan_directory(directory_path):
    """Scans a directory and returns a list of file paths."""
    return [str(path) for path in Path(directory_path).rglob('*') if path.is_file()]