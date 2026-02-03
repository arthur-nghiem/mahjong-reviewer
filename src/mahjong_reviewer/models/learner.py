"""
trainer.py: Define a CNN that predicts next discard from the current game state.
"""

from config import constants
from config.config import Config
from torch import nn


class DiscardLearner(nn.Module):
    """
    CNN used to learn next discard based on current game state.
    """

    def __init__(self):
        super(DiscardLearner, self).__init__()
        config = Config()

        self.features = nn.Sequential(
            nn.Conv2d(1, config.OUT_CHANNELS, kernel_size=3, padding=1),
            nn.BatchNorm2d(config.OUT_CHANNELS),
            nn.ReLU(inplace=True),
            nn.Dropout2d(config.DROPOUT_RATE),
        )

        flatten_size = config.OUT_CHANNELS * config.INPUT_ROWS * constants.TILE_TYPES

        self.classifier = nn.Sequential(
            nn.Linear(flatten_size, config.HIDDEN_SIZE),
            nn.ReLU(inplace=True),
            nn.Dropout(config.DROPOUT_RATE),
            nn.Linear(config.HIDDEN_SIZE, constants.TILE_TYPES),
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x
