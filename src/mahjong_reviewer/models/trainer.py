"""
trainer.py: Train a machine learning model on historical game data.
"""

from config.config import Config
import logging
from mahjong_reviewer.data import loader
from mahjong_reviewer.models import learner
import torch
from torch import nn
from torch import optim

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


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

    def train_model(self) -> None:
        """
        Trains a machine learning model and saves the state dictionary to data/models.
        """
        device = torch.device("cpu")
        if torch.backends.mps.is_available():
            device = torch.device("mps")
        elif torch.cuda.is_available():
            device = torch.device("cuda")

        train_loader = loader.load_data(self.input_dir / "cnn_train.pt", self.batch_size, True)
        test_loader = loader.load_data(self.input_dir / "cnn_test.pt", self.batch_size, False)
        model = learner.DiscardLearner().to(device)

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.AdamW(model.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        num_epochs = self.num_epochs

        for epoch in range(num_epochs):
            model.train()
            correct_train = 0
            total_train = 0
            for inputs, labels in train_loader:
                inputs, labels = inputs.to(device), labels.to(device)
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
                    inputs, labels = inputs.to(device), labels.to(device)
                    outputs = model(inputs)
                    _, predicted_test = torch.max(outputs.data, 1)
                    total_test += labels.size(0)
                    correct_test += (predicted_test == labels).sum().item()
            test_accuracy = 100 * correct_test / total_test
            logger.info(f"Epoch {epoch} Train Acc: {train_accuracy}, Test Acc: {test_accuracy}")

            if test_accuracy > self.best_test_accuracy:
                self.best_test_accuracy = test_accuracy
                model = model.to("cpu")
                torch.save(model.state_dict(), self.output_dir)
                model = model.to(device)


if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train_model()
