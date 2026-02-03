"""
tile_efficiency.py: Calculate the tile efficiency metrics of hands.
"""

from config import constants
from mahjong.shanten import Shanten
from mahjong_reviewer.simulation.game_state import GameState
from mahjong_reviewer.utils import tile_util
from typing import List


def calculate_tile_acceptance(
    game_state: GameState, next_counts: List[int], curr_shanten: int
) -> int:
    """
    Determine the number of tiles which could reduce the shanten of the reviewer's hand.

    Args:
        game_state: The game state immediately before the reviewer discards a tile.
        next_counts: Counts of each tile type among the reviewer's concealed tiles after they discard.
        curr_shanten: How many tile draws the reviewer currently is away from a ready hand.

    Returns:
        int: The number of tiles remaining which could advance the reviewer's hand.
    """

    # Determine the number of copies of each tile type remaining from reviewer's perspective
    seen_counts = tile_util.tiles_to_counts(game_state.dora_indicators)
    for actor in range(constants.NUM_PLAYERS):
        player = game_state.players[actor]
        discarded_counts = tile_util.tiles_to_counts(player.discard_pile)
        revealed_counts = [0] * constants.TILE_TYPES
        for i in range(len(player.calls)):
            revealed_counts = tile_util.tiles_to_counts(player.revealed_tiles[i])
        self_counts = [0] * constants.TILE_TYPES
        if actor == game_state.reviewer_idx:
            reviewer_hand = (
                player.concealed_tiles + [player.drawn_tile]
                if player.drawn_tile
                else player.concealed_tiles
            )
            self_counts = tile_util.tiles_to_counts(reviewer_hand)
        for tile_idx in range(constants.TILE_TYPES):
            seen_counts[tile_idx] += (
                discarded_counts[tile_idx] + revealed_counts[tile_idx] + self_counts[tile_idx]
            )
    unseen_counts = [constants.TILE_COPIES - seen_counts[i] for i in range(constants.TILE_TYPES)]

    # For each tile type, add the number of them remaining if it advances the hand
    tile_acceptance = 0
    shanten = Shanten()
    for draw_idx in range(constants.TILE_TYPES):
        next_counts[draw_idx] += 1
        next_shanten = shanten.calculate_shanten(next_counts)
        if next_shanten < curr_shanten:
            tile_acceptance += unseen_counts[draw_idx]
        next_counts[draw_idx] -= 1
    return tile_acceptance


def calculate_tile_efficiency(
    game_state: GameState, player_idx: int
) -> tuple[List[int], List[int]]:
    """
    Calculate tile efficiency statistics for each of the player's possible discards.

    Args:
        game_state: A game state at which the player chooses a tile to discard.
        player_idx: The index of the player in the game.

    Returns:
        list[int]: The shanten of the resulting hand for each possible discard.
        list[int]: The tile acceptance of the resulting hand for each possible discard.
    """

    player = game_state.players[player_idx]
    player_hand = (
        player.concealed_tiles + [player.drawn_tile]
        if player.drawn_tile
        else player.concealed_tiles
    )
    n_concealed = len(player_hand)
    shanten_eval = Shanten()
    shanten = [0] * n_concealed
    acceptance = [0] * n_concealed
    for i in range(n_concealed):
        next_tiles = [player_hand[j] for j in range(n_concealed) if j != i]
        next_counts = tile_util.tiles_to_counts(next_tiles)
        shanten[i] = shanten_eval.calculate_shanten(next_counts)
        acceptance[i] = calculate_tile_acceptance(game_state, next_counts, shanten[i])
    return shanten, acceptance
