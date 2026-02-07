"""
trainer.py: Train a machine learning model on historical game data.
"""

from config.config import Config
import logging
from mahjong_reviewer.data import loader
from mahjong_reviewer.models import learner
from pathlib import Path
import torch
from torch import nn
from torch import optim
from torch.utils.data import DataLoader
from typing import Union

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class ChunkedDataLoader:
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


class ModelTrainer:
    def __init__(self):
        self.best_test_accuracy = 0.0
        config = Config()
        self.input_dir = config.DATA_DIR / "processed"
        self.output_dir = config.DATA_DIR / "models" / "cnn_weights.pt"
        self.batch_size = config.BATCH_SIZE
        self.lr = config.BASE_LR
        self.num_epochs = config.NUM_EPOCHS
        self.weight_decay = config.WEIGHT_DECAY
        self.lazy_loading = config.LAZY_LOADING

    def get_chunk_paths(self, prefix: str) -> list[Path]:
        """
        Find all chunk files with given prefix.

        Args:
            prefix: The file prefix (for example, "cnn_train").

        Returns:
            The sorted list of chunk paths.
        """
        chunk_paths = list(self.input_dir.glob(f"{prefix}*.pt"))
        if not chunk_paths:
            raise FileNotFoundError(f"No chunks found with prefix '{prefix}' in {self.input_dir}")
        chunk_paths.sort(key=lambda p: int(p.stem.replace(prefix, "") or "0"))
        logger.info(f"Found {len(chunk_paths)} chunks for {prefix}")
        return chunk_paths

    def train_model(self) -> None:
        """
        Trains a machine learning model and saves the state dictionary to data/models.
        """
        device = torch.device("cpu")
        if torch.backends.mps.is_available():
            device = torch.device("mps")
        elif torch.cuda.is_available():
            device = torch.device("cuda")
        logger.info(f"Using device: {device}")

        if self.lazy_loading:
            train_chunks = self.get_chunk_paths("cnn_train")
            test_chunks = self.get_chunk_paths("cnn_test")
            train_loader: Union[ChunkedDataLoader, DataLoader] = ChunkedDataLoader(
                train_chunks, self.batch_size, shuffle=True
            )
            test_loader: Union[ChunkedDataLoader, DataLoader] = ChunkedDataLoader(
                test_chunks, self.batch_size, shuffle=False
            )
        else:
            train_loader = loader.load_data(self.input_dir / "cnn_train.pt", self.batch_size, True)
            test_loader = loader.load_data(self.input_dir / "cnn_test.pt", self.batch_size, False)

        model = learner.DiscardLearner().to(device)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.AdamW(model.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        logger.info(f"Starting training for {self.num_epochs} epochs...")

        for epoch in range(self.num_epochs):
            model.train()
            correct_train = 0
            total_train = 0

            for inputs, labels in train_loader:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

                _, predicted = torch.max(outputs.data, 1)
                total_train += labels.size(0)
                correct_train += (predicted == labels).sum().item()
            train_accuracy = 100 * correct_train / total_train

            model.eval()
            correct_test = 0
            total_test = 0

            with torch.no_grad():
                for inputs, labels in test_loader:
                    inputs = inputs.to(device)
                    labels = labels.to(device)

                    outputs = model(inputs)
                    _, predicted_test = torch.max(outputs.data, 1)
                    total_test += labels.size(0)
                    correct_test += (predicted_test == labels).sum().item()
            test_accuracy = 100 * correct_test / total_test
            logger.info(
                f"Epoch {epoch+1}/{self.num_epochs} - "
                f"Train Accuracy: {train_accuracy:.2f}, "
                f"Test Accuracy: {test_accuracy:.2f}"
            )

            if test_accuracy > self.best_test_accuracy:
                self.best_test_accuracy = test_accuracy
                model = model.to("cpu")
                torch.save(model.state_dict(), self.output_dir)
                logger.info(f"Saved new best model.")
                model = model.to(device)

        logger.info(f"Training complete! Best test accuracy: {self.best_test_accuracy:.2f}%")


if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train_model()
