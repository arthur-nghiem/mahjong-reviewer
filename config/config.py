from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).parent.parent
    INPUT_DIR = BASE_DIR / "input"
    DATA_DIR = BASE_DIR / "data"
    ARCHIVE_DIR = BASE_DIR / "archive"
    TILES_DIR = BASE_DIR / "assets" / "tiles"
    FONT_DIR = BASE_DIR / "assets" / "NotoSerifCJKjp-VF.ttf"
    OUTPUT_DIR = BASE_DIR / "output"

    LOG_DIR = INPUT_DIR / "sample-game.jsonl"
    REVIEWER_NAME = "ampy"
    YEARS = range(2020, 2025)

    BASE_LR = 0.0001
    BATCH_SIZE = 256
    DROPOUT_RATE = 0.25 
    INPUT_ROWS = 254
    HIDDEN_SIZE = 128
    NUM_EPOCHS = 100
    NUM_WORKERS = 4
    OUT_CHANNELS = 16
    SAMPLE_SIZE = 10000
    TRAIN_TEST_SPLIT = 0.8
    WEIGHT_DECAY = 0.01

    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self):
        """Validate that all required files and directories exist."""
        if not self.TILES_DIR.exists():
            print(f"Warning: Tiles directory not found: {self.TILES_DIR}")
        if self.LOG_DIR and not self.LOG_DIR.exists():
            print(f"Warning: Game log not found: {self.LOG_DIR}")
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        if self.BATCH_SIZE <= 0:
            raise ValueError(f"BATCH_SIZE must be positive, got {self.BATCH_SIZE}")
        if not 0 < self.TRAIN_TEST_SPLIT < 1:
            raise ValueError(f"TRAIN_TEST_SPLIT must be between 0 and 1")