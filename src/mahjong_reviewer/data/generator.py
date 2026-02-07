"""
generator.py: Generate datasets for machine learning.
"""

from config import constants
from config.config import Config
from pathlib import Path
import random
from mahjong_reviewer.simulation import simulator
from mahjong_reviewer.utils import file_util
import torch
from typing import List
from multiprocessing import Pool, cpu_count
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def process_single_game(log_path: Path) -> tuple[torch.Tensor, List[int]]:
    """
    Process a single game log file.

    Args:
        log_path: The path to a game log.

    Returns:
        Tensor: The predictors of a decision at each game states.
        List[int]: The decisions made at each game state.
    """
    try:
        events = file_util.read_jsonl_jsonlines(log_path)
        player_name = events[0]["names"][0]
        predictors, response = simulator.simulate_game(log_path, player_name, False)
        return predictors, response
    except Exception as e:
        logger.warning(f"Error processing {log_path}: {e}")
        return torch.zeros(0, constants.TILE_TYPES), []


def generate_dataset(logs: List[Path], dataset_name: str, num_workers: int = -1) -> None:
    """
    Generate a dataset from a collection of game logs.

    Args:
        logs: The paths to games which will be simulated for data generation.
        dataset_name: The desired name for the generated dataset.
        num_workers: The number of parallel workers.
    """
    if num_workers == -1:
        num_workers = max(1, cpu_count() - 1)
    logger.info(f"Processing {len(logs)} games using {num_workers} workers...")

    with Pool(num_workers) as pool:
        results = []
        for i, result in enumerate(pool.imap_unordered(process_single_game, logs)):
            results.append(result)
            total_states = sum(len(r[1]) for r in results)
            logger.info(f"Processed {i+1}/{len(logs)} games ({total_states} states)")

    logger.info("Combining results...")
    all_predictors = []
    all_responses = []
    for predictors, response in results:
        if len(response) > 0:
            all_predictors.append(predictors)
            all_responses.extend(response)

    combined_predictors = (
        torch.cat(all_predictors, dim=0) if all_predictors else torch.zeros(0, constants.TILE_TYPES)
    )
    combined_response = torch.tensor(all_responses) if all_responses else torch.tensor([])
    dataset = {
        "predictors": combined_predictors,
        "response": combined_response,
    }
    config = Config()
    output_path = config.DATA_DIR / "processed" / dataset_name
    torch.save(dataset, output_path)
    logger.info(f"Saved dataset with {len(all_responses)} states to {output_path}")


if __name__ == "__main__":
    config = Config()
    data_dir = config.DATA_DIR / "raw"
    logger.info("Finding log files...")
    all_logs = [log for log in data_dir.glob("*/*") if log.is_file()]
    logger.info(f"Found {len(all_logs)} total games")

    sample_logs = random.sample(all_logs, config.SAMPLE_SIZE)

    if config.LAZY_LOADING:
        assert config.SAMPLE_SIZE % config.DATASET_SIZE == 0
        num_datasets = int(config.SAMPLE_SIZE / config.DATASET_SIZE)
        split_idxs = [i * config.DATASET_SIZE for i in range(num_datasets + 1)]
        num_train_datasets = round(num_datasets * config.TRAIN_TEST_SPLIT)
        num_test_datasets = num_datasets - num_train_datasets

        for i in range(num_train_datasets):
            logger.info(f"Generating training dataset {i}...")
            generate_dataset(
                sample_logs[split_idxs[i] : split_idxs[i + 1]],
                f"cnn_train{i}.pt",
                config.NUM_WORKERS,
            )
        for i in range(num_test_datasets):
            logger.info(f"Generating test dataset {i}...")
            j = i + num_train_datasets
            generate_dataset(
                sample_logs[split_idxs[j] : split_idxs[j + 1]],
                f"cnn_test{i}.pt",
                config.NUM_WORKERS,
            )

    else:
        split_idx = round(config.SAMPLE_SIZE * config.TRAIN_TEST_SPLIT)
        logger.info("Generating training dataset...")
        generate_dataset(sample_logs[:split_idx], "cnn_train.pt", config.NUM_WORKERS)
        logger.info("Generating test dataset...")
        generate_dataset(sample_logs[split_idx:], "cnn_test.pt", config.NUM_WORKERS)

    logger.info("Data generation complete!")
