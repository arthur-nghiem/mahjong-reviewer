"""
explanations.py: Generate text explanations identifying ideal discards.
"""

from config.config import Config
from mahjong_reviewer.analysis import tile_efficiency
from mahjong_reviewer.data import preprocessor
from mahjong_reviewer.models.learner import DiscardLearner
from mahjong_reviewer.simulation.game_state import GameState
from mahjong_reviewer.utils import tile_util
import torch
from typing import Any


def generate_explanation_classical(
    game_state: GameState, discard_event: dict[str, Any]
) -> tuple[str, bool]:
    """
    Identify which discard is ideal solely based on a hard-coded algorithm to maximize tile efficiency.

    Args:
        game_state: The game state at a point where a player can choose a discard.
        discard_event: The event in which the player chooses the next discard.

    Returns:
        str: Text identifying the player's choice and the most tile efficient choice.
        bool: Whether or not the model agrees with the player's discard choice.
    """

    # Find the discard(s) which achieve highest tile acceptance among those with the minimum shanten
    reviewer = game_state.players[game_state.reviewer_idx]
    reviewer_hand = (
        reviewer.concealed_tiles + [reviewer.drawn_tile]
        if reviewer.drawn_tile
        else reviewer.concealed_tiles
    )
    shanten, acceptance = tile_efficiency.calculate_tile_efficiency(
        game_state, game_state.reviewer_idx
    )
    min_shanten = min(shanten)
    min_shanten_indices = [i for i, v in enumerate(shanten) if v == min_shanten]
    masked_acceptance = [
        acceptance[i] if i in min_shanten_indices else 0 for i in range(len(reviewer_hand))
    ]
    max_acceptance = max(masked_acceptance)
    max_acceptance_indices = [i for i, v in enumerate(masked_acceptance) if v == max_acceptance]
    max_acceptance_tiles = [reviewer_hand[max_index] for max_index in max_acceptance_indices]
    unique_tiles = list(dict.fromkeys(max_acceptance_tiles))
    unique_names = [tile_util.name_tile(unique_tiles[i]) for i in range(len(unique_tiles))]

    player_statement = f"You discarded the {tile_util.name_tile(discard_event["pai"])}."
    model_explanation = (
        f"From a tile efficiency perspective, the best discards were: {", ".join(unique_names)}."
    )
    explanation = player_statement + "\n" + model_explanation
    agree = discard_event["pai"] in unique_tiles
    return explanation, agree


def generate_explanation_ml(
    game_state: GameState, discard_event: dict[str, Any], trained_model: DiscardLearner
) -> tuple[str, bool]:
    """
    Identify which discard is ideal solely based on a machine learning algorithm.

    Args:
        game_state: The game state at a point where a player can choose a discard.
        discard_event: The event in which the player chooses the next discard.
        trained_model: A discard learned with weights already loaded.

    Returns:
        str: Text identifying the player's choice and the most tile efficient choice.
        bool: whether or not the model agrees with the player's discard choice.
    """

    predictors, _ = preprocessor.generate_data_point(game_state, discard_event)
    with torch.no_grad():
        output = trained_model(predictors)
        _, idx_predicted = torch.max(output.data, 1)
    discard_predicted = tile_util.idxs_to_tiles([int(idx_predicted.item())])[0]

    player_statement = f"You discarded the {tile_util.name_tile(discard_event["pai"])}."
    model_explanation = f"The model selects a discard of {tile_util.name_tile(discard_predicted)}."
    explanation = player_statement + "\n" + model_explanation
    agree = discard_predicted == discard_event["pai"]
    return explanation, agree
