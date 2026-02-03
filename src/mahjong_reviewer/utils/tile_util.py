"""
tile_util.py: Utilities for handling mahjong tiles.
"""

from config import constants
from typing import List
import torch
from torch import Tensor


def idxs_to_tiles(idxs: List[int]) -> List[str]:
    """
    Converts a list of tile indexes to tiles in string format.

    Args:
        idxs: A list in which each element is a tile index 0 through 33.

    Returns:
        List[str]: A list with each element being a string representation of a tile (for example "4s").
    """

    tile_list = []
    for idx in idxs:
        tile_list.append(constants.TILE_ORDER[idx])
    return tile_list


def name_tile(tile: str) -> str:
    """
    Provide the human readable name of a tile.

    Args:
        tile: A tile represented as a shorthand string.

    Returns:
        str: The full name of a tile (for example, red 5 of circles).
    """

    if tile in constants.HONORS_NAMES:
        return constants.HONORS_NAMES[tile]
    num = tile[0]
    suit_name = constants.SUIT_NAMES[tile[1]]
    red_indicator = "red " if tile[-1] == "r" else ""
    return f"{red_indicator}{num} of {suit_name}"


def sort_tiles(tiles: List[str]) -> List[str]:
    """
    Sort a collection of tiles represented as strings.

    Args:
        tiles: An unsorted list of tiles.

    Returns:
        List[str]: A sorted list of tiles (characters, pins, bamboo, then honors).
    """

    tile_order = constants.TILE_ORDER_WITH_REDS
    tiles.sort(key=lambda item: tile_order.index(item))
    return tiles


def tiles_to_counts(tiles: List[str]) -> List[int]:
    """
    Converts tiles in string format to the counts of each tile type.

    Args:
        tiles: A list with each element being a string representation of a tile (for example "4s").

    Returns:
        List[int]: A list in which each element represents the number of a tile type present.
    """

    counts = [0] * constants.TILE_TYPES
    honors = constants.HONORS_IDXS
    suit_idxs = constants.SUIT_IDXS
    for tile in tiles:
        if len(tile) == 1:
            tile_idx = honors[tile]
        else:
            tile_idx = int(tile[0]) + suit_idxs[tile[1]]
        counts[tile_idx] += 1
    return counts


def tiles_to_idxs(tiles: List[str]) -> List[int]:
    """
    Converts tiles in string format to a list of tile indexes.

    Args:
        tiles: A list with each element being a string representation of a tile (for example "4s").

    Returns:
        List[int]: A list in which each element is a tile index 0 through 33.
    """

    idx_list = []
    honors = constants.HONORS_IDXS
    suit_idxs = constants.SUIT_IDXS
    for tile in tiles:
        if len(tile) == 1:
            tile_idx = honors[tile]
        else:
            tile_idx = int(tile[0]) + suit_idxs[tile[1]]
        idx_list.append(tile_idx)
    return idx_list


def tiles_to_tensor(tiles: List[str], tile_max: int = constants.TILE_COPIES) -> Tensor:
    """
    Converts tiles in string format to a pytorch tensor.

    Args:
        tiles: A list with each element being a string representation of a tile (for example "4s").
        tile_max: The maximum number of copies of a single tile type possible.

    Returns:
        Tensor: A tensor in which 1 represents presence of a tile and 0 represents absence.
    """

    tiles_tensor = torch.zeros(tile_max, constants.TILE_TYPES)
    tiles_idxs = tiles_to_idxs(tiles)
    copies = [0] * constants.TILE_TYPES
    for i in tiles_idxs:
        tiles_tensor[copies[i], i] = 1
        copies[i] += 1
    return tiles_tensor
