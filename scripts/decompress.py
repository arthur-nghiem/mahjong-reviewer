"""
decompress.py: converts all .mjson files in archive directory to .jsonl files in data directory
"""

from config.config import Config
import gzip
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def decompress_mjson_files(source_dir: Path, destination_dir: Path) -> None:
    """
    Decompresses all .mjson files in a given directory

    Args:
        source_dir: The path to the directory containing the .mjson files
        destination_dir: The directory to save the decompressed .jsonl files
    """
    destination_dir.mkdir(parents=True, exist_ok=True)
    for filepath in source_dir.glob("*.mjson"):
        output_path = destination_dir / f"{filepath.stem}.jsonl"

        with gzip.open(filepath, "rb") as f_in:
            output_path.write_bytes(f_in.read())
        
        logger.info(f"Decompressed '{filepath.name}' to '{output_path.name}'")

if __name__ == "__main__":
    config = Config()
    for year in config.YEARS:
        source_dir = Path(f"{config.ARCHIVE_DIR}/{year}/{year}")
        destination_dir = Path(f"{config.DATA_DIR}/raw/{year}")
        decompress_mjson_files(source_dir, destination_dir)
