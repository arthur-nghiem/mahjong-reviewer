"""
file_util.py: Utilities for file input and output.
"""

import jsonlines
import logging
from pathlib import Path
from PIL import Image
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_tiles(folder_path: Path) -> Dict[str, Image.Image]:
    """
    Load all tile images from a folder.

    Args:
        folder_path: Path to the folder containing tile images.

    Returns:
        Dictionary mapping tile names to PIL Image objects.

    Raises:
        FileNotFoundError: If folder_path doesn't exist.
        ValueError: If no valid images are found.
    """

    if not folder_path.exists():
        raise FileNotFoundError(f"Tile folder not found: {folder_path}")

    tiles = {}
    for file_path in folder_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".png":
            try:
                img = Image.open(file_path).convert("RGBA")
                tiles[file_path.stem] = img.resize((30, 40), Image.Resampling.LANCZOS)
            except Exception as e:
                logger.warning(f"Warning: Failed to load {file_path.name}: {e}")

    if not tiles:
        raise ValueError(f"No valid images found in {folder_path}")

    return tiles


def read_jsonl_jsonlines(log_path: Path) -> List[Dict]:
    """
    Read in a .jsonl file.

    Args:
        log_path: The path to the .jsonl file.

    Returns:
        List with each element representing a line in the specified log file.

    Raises:
        FileNotFoundError: If log_path doesn't exist.
        ValueError: If log contains invalid data.
    """

    try:
        data = []
        with jsonlines.open(log_path, "r") as reader:
            for obj in reader:
                data.append(obj)
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"Log file not found: {log_path}")
    except jsonlines.InvalidLineError as e:
        raise ValueError(f"Invalid JSONL format in {log_path}: {e}")
