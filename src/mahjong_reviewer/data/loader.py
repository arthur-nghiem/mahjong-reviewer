"""
loader.py: Load .pt game data into memory.
"""

from pathlib import Path
import torch
from torch.utils.data import DataLoader
from torch.utils.data import TensorDataset


def load_data(data_path: Path, batch_size: int = 256, shuffle: bool = True) -> DataLoader:
    """
    Load .pt game data into memory.

    Args:
        data_path: The path to previously generated data.
        batch_size: The desired batch size for training.
        shuffle: Whether or not to shuffle the order of the data.
    """

    data = torch.load(data_path)
    X = data["predictors"].to(dtype=torch.float32)
    y = data["response"].to(dtype=torch.long)
    dataset = TensorDataset(X, y)
    data_loader = DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)
    return data_loader
