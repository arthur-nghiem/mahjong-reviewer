"""
game_state.py: Represents all relevant information at a point in a game.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Player:
    """Class containing information pertaining to a specific player.

    Attributes:
        name: The in-game username of player.
        table_position: The table position of the player relative to the reviewer.
            0 if the player is the reviewer.
            1 if the player is to the right of the reviewer.
            2 if the player is facing the reviewer.
            3 if the player if to the left of the reviewer.
        reach_status: Whether or not the player has declared riichi.
        score: The player's current score.
        turn_count: The number of turns the player has had.
        seat_wind: The player's seat wind.
        concealed_tiles: The player's concealed tiles, not including the drawn tile if present.
        revealed_tiles: Tiles which the player has revealed due to calls.
        taken: For each of the player's revealed tiles, whether or not it was taken from another player.
        discarded_tiles: Tiles the player has discarded.
        discard_pile: Tiles in the player's discard pile, different discarded_tiles if their discards are called.
        tsumogiri: For each of the player's discarded tiles, whether or not it was drawn that turn.
        discard_rotate: For each tile in the player's discard pile, whether or not it needs to be rotated.
        drawn_tile: If present, the tile the player just drew.
    """

    name: str
    table_position: int
    reach_status: bool = False
    score: int = 0
    turn_count: int = 0
    seat_wind: str = "E"
    concealed_tiles: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)
    revealed_tiles: List[List[str]] = field(default_factory=list)
    taken: List[List[bool]] = field(default_factory=list)
    discarded_tiles: List[str] = field(default_factory=list)
    discard_pile: List[str] = field(default_factory=list)
    tsumogiri: List[bool] = field(default_factory=list)
    discard_rotate: List[bool] = field(default_factory=list)
    drawn_tile: Optional[str] = None


@dataclass
class GameState:
    """Class containing information pertaining to the game as a whole.

    Attributes:
        players: The four players in the game.
        reviewer_idx: The index of the reviewer in the player list.
        bakaze: The round wind.
        dora_indicators: The revealed dora indicators.
        kyoku: The round number.
        honba: The number of repeats on the round number.
        kyotaku: The number of riichi bets on the table.
        tile_count: The number of tiles left in the drawing wall.
    """

    players: List[Player]
    reviewer_idx: int
    bakaze: str = "E"
    dora_indicators: List[str] = field(default_factory=list)
    kyoku: int = 1
    honba: int = 0
    kyotaku: int = 0
    tile_count: int = 70
