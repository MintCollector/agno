"""Utility functions for JSON database operations."""

import fcntl
import json as json_module
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator

from agno.utils.log import log_debug, log_error


# TODO: this needs proper tests
@contextmanager
def file_lock(file_path: Path, timeout: float = 10.0) -> Generator[None, None, None]:
    """
    Context manager for file locking to prevent concurrent access issues.

    Args:
        file_path: Path to the file to lock
        timeout: Maximum time to wait for lock acquisition
    """
    lock_file = file_path.with_suffix(f"{file_path.suffix}.lock")

    try:
        # Create lock file
        with open(lock_file, "w") as f:
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    log_debug(f"Acquired lock for {file_path}")
                    yield
                    return
                except IOError:
                    time.sleep(0.1)

            raise TimeoutError(f"Could not acquire lock for {file_path} within {timeout} seconds")

    except Exception as e:
        log_error(f"Error with file lock for {file_path}: {e}")
        # Fallback to no locking
        yield

    finally:
        # Clean up lock file
        try:
            if lock_file.exists():
                lock_file.unlink()
        except Exception as e:
            log_debug(f"Could not remove lock file {lock_file}: {e}")


def safe_json_load(file_path: Path) -> Dict[str, Any]:
    """
    Safely load JSON data from a file with proper error handling.

    Args:
        file_path: Path to the JSON file

    Returns:
        Dictionary containing the JSON data, or empty dict if file doesn't exist or is invalid
    """
    if not file_path.exists():
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json_module.loads(content)
    except (json_module.JSONDecodeError, FileNotFoundError, PermissionError) as e:
        log_error(f"Error loading JSON from {file_path}: {e}")
        return {}


def safe_json_save(file_path: Path, data: Dict[str, Any]) -> bool:
    """
    Safely save JSON data to a file with proper error handling.

    Args:
        file_path: Path to the JSON file
        data: Dictionary to save as JSON

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file first, then rename for atomic operation
        temp_file = file_path.with_suffix(f"{file_path.suffix}.tmp")

        with open(temp_file, "w", encoding="utf-8") as f:
            json_module.dump(data, f, indent=2, ensure_ascii=False)

        # Atomic rename
        temp_file.replace(file_path)
        return True

    except Exception as e:
        log_error(f"Error saving JSON to {file_path}: {e}")
        # Clean up temp file if it exists
        try:
            if temp_file.exists():
                temp_file.unlink()
        except:
            pass
        return False


def validate_json_structure(data: Any, expected_type: type = dict) -> bool:
    """
    Validate that the loaded JSON data has the expected structure.

    Args:
        data: The data to validate
        expected_type: The expected type of the data

    Returns:
        True if valid, False otherwise
    """
    return isinstance(data, expected_type)


def backup_json_file(file_path: Path, backup_dir: Path = None) -> bool:
    """
    Create a backup of a JSON file.

    Args:
        file_path: Path to the JSON file to backup
        backup_dir: Directory to store backups (defaults to same directory as file)

    Returns:
        True if backup was created successfully, False otherwise
    """
    if not file_path.exists():
        return False

    try:
        if backup_dir is None:
            backup_dir = file_path.parent

        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create backup filename with timestamp
        timestamp = int(time.time())
        backup_name = f"{file_path.stem}_{timestamp}.backup{file_path.suffix}"
        backup_path = backup_dir / backup_name

        # Copy file
        with open(file_path, "rb") as src, open(backup_path, "wb") as dst:
            dst.write(src.read())

        log_debug(f"Created backup: {backup_path}")
        return True

    except Exception as e:
        log_error(f"Error creating backup for {file_path}: {e}")
        return False
