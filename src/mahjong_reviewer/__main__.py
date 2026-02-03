"""
__main__.py: Create the interpretable game review.
"""

import argparse
from config.config import Config
from dominate import document
from dominate import tags
import logging
from mahjong_reviewer.simulation import simulator
from mahjong_reviewer.utils import file_util
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def cli() -> Config:
    """
    Command line interface that reads in log file path, reviewer username, and output directory.

    Returns:
        config: The configuration file updated by the user.
    """
    config = Config()
    parser = argparse.ArgumentParser(description="AI-powered Riichi Mahjong game analyzer")
    parser.add_argument(
        "log_file",
        type=Path,
        nargs="?",
        default=config.LOG_DIR,
        help="Name of game log file in the input directory (.jsonl)",
    )
    parser.add_argument(
        "--username", "-u", default=config.REVIEWER_NAME, help="Your in-game username"
    )

    args = parser.parse_args()
    config.LOG_DIR = config.INPUT_DIR / args.log_file
    config.REVIEWER_NAME = args.username
    return config


def main(config: Config) -> None:
    """
    Main entry point for creating game reviews.

    Args:
        config: The configuration file updated by the user.
    """
    try:
        log_dir = config.LOG_DIR
        reviewer_name = config.REVIEWER_NAME
        if not log_dir.exists():
            logger.error(f"Game log not found: {log_dir}")
            return

        logger.info(f"Starting review for {log_dir.name}...")
        simulator.simulate_game(log_dir, reviewer_name, True)
        game_dir = config.OUTPUT_DIR / f"{log_dir.stem}"
        explanation_path = game_dir / "explanations.jsonl"
        if not explanation_path.exists():
            logger.error(f"Explanations file not found: {explanation_path}")
            return
        explanation_list = file_util.read_jsonl_jsonlines(explanation_path)

        doc = document(title="Riichi Mahjong Game Review")
        with doc.head:
            tags.style("body { color: black; }")
            tags.meta(charset="utf-8")

        with doc.body:
            tags.h1("Riichi Mahjong Game Review")
            img_path = Path(game_dir / "img")
            if not img_path.exists():
                logger.error(f"Image directory not found: {img_path}")
                return
            png_files = sorted(img_path.glob("*.png"))
            if not png_files:
                logger.warning("No game images found")

            for idx, filename in enumerate(png_files):
                data = filename.stem.split("-")
                round_counter = f"{data[0][:-1]} {data[0][-1]}"
                repeat_counter = f"Repeat {data[1][-1]}"
                turn_counter = f"Turn {int(data[2][-2:])}"
                agree_symbol = "\U00002705" if data[3] == "True" else "\U0000274c"
                readable = f"{round_counter} {repeat_counter}: {turn_counter} {agree_symbol}"
                with tags.details():
                    tags.summary(readable)
                    tags.img(src=f"img/{filename.name}", alt=readable)
                    tags.p(explanation_list[idx])

        review_path = Path(game_dir / "game_review.html")
        review_path.write_text(doc.render(), encoding="utf-8")
        logger.info(f"Review generated successfully: {review_path}")

    except Exception as e:
        logger.error(f"Error generating review: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    updated_config = cli()
    main(updated_config)
