"""
loader.py: Load .pt game data into memory.
"""

from config import constants
from pathlib import Path
import torch
from torch.utils.data import DataLoader
from torch.utils.data import TensorDataset


def load_data_eager(data_paths: list[Path], batch_size: int = 256, shuffle: bool = True) -> DataLoader:
    """
    Load .pt game data into memory.

    Args:
        data_path: The path to previously generated data.
        batch_size: The desired batch size for training.
        shuffle: Whether or not to shuffle the order of the data.
    """

    X = torch.zeros(0, 1, constants.INPUT_ROWS, constants.TILE_TYPES)
    y = torch.zeros(0)
    for data_path in data_paths:
        data = torch.load(data_paths)
        X = torch.cat((X, data["predictors"].to(dtype=torch.float32)), 0)
        y = torch.cat((y, data["response"].to(dtype=torch.long)), 0)
    dataset = TensorDataset(X, y)
    data_loader = DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)
    return data_loader

class LazyDataLoader:
    """
    Lazy loader for datasets split across multiple .pt files.
    """

    def __init__(self, chunk_paths: list[Path], batch_size: int, shuffle: bool = True):
        """
        Args:
            chunk_paths: The list of paths to .pt files.
            batch_size: The batch size for training.
            shuffle: Whether to shuffle data within each chunk.
        """
        self.chunk_paths = sorted(chunk_paths)
        self.batch_size = batch_size
        self.shuffle = shuffle
        logger.info(f"Initialized ChunkedDataLoader with {len(self.chunk_paths)} chunks")

    def __iter__(self):
        for chunk_path in self.chunk_paths:
            logger.info(f"Loading chunk: {chunk_path.name}")
            chunk_loader = loader.load_data(chunk_path, self.batch_size, self.shuffle)
            for batch in chunk_loader:
                yield batch
            del chunk_loader