"""
preprocessor.py: Convert a game state into a machine learning ready data point.
"""

from config import constants
from mahjong_reviewer.simulation.game_state import GameState
from mahjong_reviewer.simulation.game_state import Player
from mahjong_reviewer.utils import tile_util
import torch
from torch import Tensor
from typing import Any


def generate_data_point(game_state: GameState, event: dict[str, Any]) -> tuple[Tensor, int]:
    """
    Convert a game state into a machine learning ready data point.

    Args:
        game_state: The game state at a decision point.
        event: An event line log which represents the decision made.

    Returns:
        Tensor: Game data informing a decision.
        int: Representation of the decision made.
    """

    predictors = tensorize_game_state(game_state, event)
    response = tile_util.tiles_to_idxs([event["pai"]])[0]
    return predictors, response


def tensorize_game_state(game_state: GameState, event: dict[str, Any]) -> Tensor:
    """
    Convert the game state into a tensor for machine learning.

    Args:
        game_state: The game state at a decision point.
        event: An event line log which represents the decision made.

    Returns:
        Tensor: A tensor representing the game state with binary elements.
    """

    actor_idx = event["actor"]
    state_tensor = torch.zeros(0, constants.TILE_TYPES)

    for i in range(constants.NUM_PLAYERS):
        player_idx = (actor_idx + i) % 4
        player = game_state.players[player_idx]

        if i == 0:
            drawn_tiles = [player.drawn_tile] if player.drawn_tile else []
            draw_tensor = tile_util.tiles_to_tensor(drawn_tiles, 1)
            state_tensor = torch.concat([state_tensor, draw_tensor], dim=0)

            concealed_tiles = player.concealed_tiles
            concealed_tiles_tensor = tile_util.tiles_to_tensor(concealed_tiles)
            state_tensor = torch.concat([state_tensor, concealed_tiles_tensor], dim=0)

        revealed_tiles_tensor = tensorize_revealed_tiles(player)
        state_tensor = torch.concat([state_tensor, revealed_tiles_tensor], dim=0)

        discarded_tensor = tensorize_discarded_tiles(player)
        state_tensor = torch.concat([state_tensor, discarded_tensor], dim=0)

        riichi_tensor = encode_bool(player.reach_status)
        state_tensor = torch.concat([state_tensor, riichi_tensor], dim=0)

        score_scaled = int(player.score / constants.MIN_SCORE_DENOM)
        score_tensor = encode_scalar(score_scaled, constants.CHANNELS_SCORE)
        state_tensor = torch.concat([state_tensor, score_tensor], dim=0)

    dora_indicators_tensor = tile_util.tiles_to_tensor(game_state.dora_indicators)
    state_tensor = torch.concat([state_tensor, dora_indicators_tensor], dim=0)

    round_number = get_round_number(game_state)
    round_tensor = encode_scalar(round_number, constants.CHANNELS_ROUND)
    state_tensor = torch.concat([state_tensor, round_tensor], dim=0)

    honba_tensor = encode_scalar(game_state.honba, constants.CHANNELS_HONBA)
    state_tensor = torch.concat([state_tensor, honba_tensor], dim=0)

    kyotaku_tensor = encode_scalar(game_state.kyotaku, constants.CHANNELS_KYOTAKU)
    state_tensor = torch.concat([state_tensor, kyotaku_tensor], dim=0)

    actor_wind = [game_state.players[actor_idx].seat_wind]
    actor_wind_tensor = tile_util.tiles_to_tensor(actor_wind, 1)
    state_tensor = torch.concat([state_tensor, actor_wind_tensor], dim=0)
    return state_tensor.unsqueeze(0).unsqueeze(1)


def tensorize_revealed_tiles(player: Player) -> Tensor:
    """
    Convert one player's revealed tiles into a tensor.

    Args:
        player_idx: The player whose revealed tiles are read.

    Returns:
        Tensor: A tensor representing revealed tiles with binary elements.
    """

    revealed_tiles_tensor = torch.zeros(0, constants.TILE_TYPES)
    for i in range(constants.CALLS_MAX):
        call_tiles_tensor = torch.zeros(constants.TILE_COPIES, constants.TILE_TYPES)
        if i < len(player.calls):
            call_tiles = player.revealed_tiles[i]
            call_tiles_tensor = tile_util.tiles_to_tensor(call_tiles)
        revealed_tiles_tensor = torch.concat([revealed_tiles_tensor, call_tiles_tensor], dim=0)
    return revealed_tiles_tensor


def tensorize_discarded_tiles(player: Player) -> Tensor:
    """
    Convert one player's discarded tiles into a tensor.

    Args:
        player: The player whose discarded tiles are read.

    Returns:
        Tensor: A tensor representing discarded tiles with binary elements.
    """

    discarded_tiles_tensor = torch.zeros(0, constants.TILE_TYPES)
    for i in range(constants.DISCARDS_MAX):
        discard_tile_tensor = torch.zeros(1, constants.TILE_TYPES)
        if i < len(player.discarded_tiles):
            discard_tile = player.discarded_tiles[i]
            discard_tile_tensor = tile_util.tiles_to_tensor([discard_tile], 1)
        discarded_tiles_tensor = torch.concat([discarded_tiles_tensor, discard_tile_tensor], dim=0)
    return discarded_tiles_tensor


def encode_scalar(scalar: int, channels: int) -> Tensor:
    """
    Convert a scalar to a 2D tensor.

    Args:
        scalar: The scalar that must be encoded.
        channels: The number of channels used for encoding.

    Returns:
        Tensor: Binary encoding of the original scalar.
    """

    format_string = f"0{channels}b"
    binary_string = format(scalar, format_string)
    encoding_tensor = torch.zeros(channels, constants.TILE_TYPES)
    for i in range(channels):
        if binary_string[i] == "1":
            encoding_tensor[i, :] = 1
    return encoding_tensor


def encode_bool(boolean: bool) -> Tensor:
    """
    Convert a boolean to a 2D row tensor.

    Args:
        boolean: The boolean that must be encoded.

    Returns:
        Tensor: Binary encoding of the original boolean.
    """

    encoding_tensor = torch.zeros(1, constants.TILE_TYPES)
    if boolean:
        encoding_tensor[0, :] = 1
    return encoding_tensor


def get_round_number(game_state: GameState) -> int:
    """
    Find the round number expressed as an integer.

    Args:
        boolean: The current game state.

    Returns:
        Tensor: The round number as an integer (for example, 6 if on South 2)
    """

    round_number = constants.WINDS.index(game_state.bakaze) * constants.NUM_PLAYERS
    round_number += game_state.kyoku
    return round_number
