"""
simulator.py: Processes game events and updates the game state accordingly.
"""

from config import constants
from config.config import Config
import json
from mahjong_reviewer.analysis import explanations
from mahjong_reviewer.data import preprocessor
from mahjong_reviewer.models.learner import DiscardLearner
from mahjong_reviewer.simulation.game_state import GameState
from mahjong_reviewer.simulation.game_state import Player
from mahjong_reviewer.simulation import renderer
from mahjong_reviewer.utils import file_util
from mahjong_reviewer.utils import tile_util
from pathlib import Path
from PIL import Image
import shutil
import torch
from torch import Tensor
from typing import Any
from typing import Dict
from typing import List


def start_game(event: Dict[str, Any], reviewer_name: str) -> GameState:
    """
    Initalize the game state based on the first line of a log file.

    Args:
        event: The log line for a "start_game" event.
        reviewer_name: The in-game username of the reviewer.

    Returns:
        GameState: The game state at the very beginning of the game.
    """

    names = event["names"]
    reviewer_idx = names.index(reviewer_name)
    table_positions = [
        (i - reviewer_idx) % constants.NUM_PLAYERS for i in range(constants.NUM_PLAYERS)
    ]
    players = [Player(names[i], table_positions[i]) for i in range(constants.NUM_PLAYERS)]
    return GameState(players, reviewer_idx)


def process_event(event: Dict[str, Any], game_state: GameState) -> Any:
    """
    Update the game state to account for a new event of any allowable type.

    Args:
        event: The log line of the event to be displayed.
        game_state: The prior game state.

    Returns:
        GameState: The updated game state.
    """

    e = Event()
    event_type = event["type"]
    return getattr(e, event_type)(event, game_state)


def simulate_game(
    log_dir: Path, reviewer_name: str, create_review: bool
) -> tuple[Tensor, List[int]]:
    """
    Fully simulate a game of riichi mahjong.

    Args:
        log_dir: Path to the game log.
        reviewer_name: The in-game username of the reviewer.
        create_review: True if simulation is to create a review, False if intended for data generation

    Returns:
        Tensor: Predictors of a decision for machine learning.
        List[int]: Response variable for machine learning.
    """

    events = file_util.read_jsonl_jsonlines(log_dir)
    config = Config()
    predictors = torch.zeros(0, 1, config.INPUT_ROWS, constants.TILE_TYPES)
    response = []
    if reviewer_name not in events[0]["names"]:
        raise ValueError(f"Player {reviewer_name} was not found in {log_dir}.")

    game_state = start_game(events[0], reviewer_name)
    if create_review:
        composite = Image.new("RGB", (100, 100))
        explanation_list = []
        review_path = Path(config.OUTPUT_DIR / log_dir.stem)
        if review_path.exists():
            shutil.rmtree(review_path)
        review_path.mkdir(parents=True)
        img_path = Path(review_path / "img")
        img_path.mkdir()
        tile_imgs = file_util.load_tiles(config.TILES_DIR)
        renderer_instance = renderer.Renderer(tile_imgs, game_state)
        trained_model = DiscardLearner()
        state_dict_dir = config.DATA_DIR / "models" / "cnn_weights.pt"
        trained_model.load_state_dict(torch.load(state_dict_dir))
        trained_model.eval()

    for i in range(1, len(events)):
        game_state = process_event(events[i], game_state)
        if create_review:
            composite = renderer.render_event(events[i], game_state, composite, renderer_instance)
        if events[i]["type"] in ["tsumo", "pon", "chi"] and events[i + 1]["type"] == "dahai":
            if create_review and events[i]["actor"] == game_state.reviewer_idx:
                explanation, agree = explanations.generate_explanation_ml(
                    game_state, events[i + 1], trained_model
                )
                explanation_list.append(explanation)
                round_name = f"{constants.WIND_NAMES[game_state.bakaze]}{game_state.kyoku}"
                turn = game_state.players[game_state.reviewer_idx].turn_count
                composite.save(
                    Path(
                        review_path
                        / "img"
                        / f"{round_name}-Repeat{game_state.honba}-Turn{turn:02d}-{agree}.png"
                    )
                )
            elif not create_review:
                predictors_next, response_next = preprocessor.generate_data_point(
                    game_state, events[i + 1]
                )
                predictors = torch.cat([predictors, predictors_next], dim=0)
                response.append(response_next)

    if create_review:
        explanation_path = Path(review_path / "explanations.jsonl")
        with explanation_path.open("w", encoding="utf-8") as outfile:
            for explanation in explanation_list:
                json_line = json.dumps(explanation) + "\n"
                outfile.write(json_line)
        return predictors, response
    else:
        return predictors, response


class Event:
    """
    Class containing methods for handling every event type.
    """

    def start_kyoku(self, event: Dict[str, Any], game_state: GameState) -> GameState:
        """
        Update the game state to account for a "start_kyoku" event.

        Args:
            event: The log line of the "start_kyoku" event.
            game_state: The prior game state.

        Returns:
            GameState: The updated game state.
        """

        for i in range(constants.NUM_PLAYERS):
            player = game_state.players[i]
            player.reach_status = False
            player.score = event["scores"][i]
            player.turn_count = 0
            player.seat_wind = constants.WINDS[(i - event["oya"]) % constants.NUM_PLAYERS]
            player.concealed_tiles = tile_util.sort_tiles(event["tehais"][i])
            player.calls = []
            player.revealed_tiles = []
            player.taken = []
            player.discarded_tiles = []
            player.discard_pile = []
            player.tsumogiri = []
            player.discard_rotate = []
            player.drawn_tile = None
        game_state.bakaze = event["bakaze"]
        game_state.dora_indicators = [event["dora_marker"]]
        game_state.kyoku = event["kyoku"]
        game_state.honba = event["honba"]
        game_state.kyotaku = event["kyotaku"]
        game_state.tile_count = constants.DRAWING_WALL_TILES
        return game_state

    def tsumo(self, event: Dict[str, Any], game_state: GameState) -> GameState:
        """
        Update the game state to account for a "tsumo" event.

        Args:
            event: The log line of the "tsumo" event.
            game_state: The prior game state.

        Returns:
            GameState: The updated game state.
        """

        actor = game_state.players[event["actor"]]
        actor.drawn_tile = event["pai"]
        actor.turn_count += 1
        game_state.tile_count -= 1
        return game_state

    def dahai(self, event: Dict[str, Any], game_state: GameState) -> GameState:
        """
        Update the game state to account for a "dahai" event.

        Args:
            event: The log line of the "dahai" event.
            game_state: The prior game state.

        Returns:
            GameState: The updated game state.
        """

        actor = game_state.players[event["actor"]]
        if actor.drawn_tile:
            actor.concealed_tiles.append(actor.drawn_tile)
            actor.drawn_tile = None
        actor.concealed_tiles.remove(event["pai"])
        actor.concealed_tiles = tile_util.sort_tiles(actor.concealed_tiles)
        actor.discarded_tiles.append(event["pai"])
        actor.discard_pile.append(event["pai"])
        actor.tsumogiri.append(event["tsumogiri"])
        if actor.reach_status and not any(actor.discard_rotate):
            actor.discard_rotate.append(True)
        else:
            actor.discard_rotate.append(False)
        return game_state

    def reach(self, event: Dict[str, Any], game_state: GameState) -> GameState:
        """
        Update the game state to account for a "reach" event.

        Args:
            event: The log line of the "reach" event.
            game_state: The prior game state.

        Returns:
            GameState: The updated game state.
        """

        actor = game_state.players[event["actor"]]
        actor.reach_status = True
        return game_state

    def reach_accepted(self, event: Dict[str, Any], game_state: GameState) -> GameState:
        """
        Update the game state to account for a "reach_accepted" event.

        Args:
            event: The log line of the "reach_accepted" event.
            game_state: The prior game state.

        Returns:
            GameState: The updated game state.
        """

        actor = game_state.players[event["actor"]]
        actor.score -= constants.RIICHI_BET_VALUE
        game_state.kyotaku += 1
        return game_state

    def chi(self, event: Dict[str, Any], game_state: GameState) -> GameState:
        """
        Update the game state to account for a "chi" event.

        Args:
            event: The log line of the "chi" event.
            game_state: The prior game state.

        Returns:
            GameState: The updated game state.
        """

        target = game_state.players[event["target"]]
        target.discard_pile.pop()
        target.tsumogiri.pop()
        target.discard_rotate.pop()

        actor = game_state.players[event["actor"]]
        chi_tiles = event["consumed"]
        for tile in chi_tiles:
            actor.concealed_tiles.remove(tile)
        actor.turn_count += 1

        actor.calls.append("chi")
        chi_tiles.insert(0, event["pai"])
        actor.revealed_tiles.append(chi_tiles)
        chi_taken = [False] * constants.CHI_TILES
        chi_taken[0] = True
        actor.taken.append(chi_taken)
        return game_state

    def pon(self, event: Dict[str, Any], game_state: GameState) -> GameState:
        """
        Update the game state to account for a "pon" event.

        Args:
            event: The log line of the "pon" event.
            game_state: The prior game state.

        Returns:
            GameState: The updated game state.
        """

        target = game_state.players[event["target"]]
        target.discard_pile.pop()
        target.tsumogiri.pop()
        target.discard_rotate.pop()

        actor = game_state.players[event["actor"]]
        pon_tiles = event["consumed"]
        for tile in pon_tiles:
            actor.concealed_tiles.remove(tile)
        actor.turn_count += 1

        actor.calls.append("pon")
        taken_idx = (event["actor"] - event["target"]) % constants.NUM_PLAYERS - 1
        pon_tiles.insert(taken_idx, event["pai"])
        actor.revealed_tiles.append(pon_tiles)
        pon_taken = [False] * constants.PON_TILES
        pon_taken[taken_idx] = True
        actor.taken.append(pon_taken)
        return game_state

    def ankan(self, event: Dict[str, Any], game_state: GameState) -> GameState:
        """
        Update the game state to account for an "ankan" event.

        Args:
            event: The log line of the "ankan" event.
            game_state: The prior game state.

        Returns:
            GameState: The updated game state.
        """

        actor = game_state.players[event["actor"]]
        if actor.drawn_tile:
            actor.concealed_tiles.append(actor.drawn_tile)
            actor.drawn_tile = None

        kan_tiles = event["consumed"]
        for tile in kan_tiles:
            actor.concealed_tiles.remove(tile)

        actor.calls.append("ankan")
        actor.revealed_tiles.append(kan_tiles)
        actor.taken.append([False] * constants.KAN_TILES)
        return game_state

    def kakan(self, event: Dict[str, Any], game_state: GameState) -> GameState:
        """
        Update the game state to account for a "kakan" event.

        Args:
            event: The log line of the "kakan" event.
            game_state: The prior game state.

        Returns:
            GameState: The updated game state.
        """

        actor = game_state.players[event["actor"]]
        if actor.drawn_tile:
            actor.concealed_tiles.append(actor.drawn_tile)
            actor.drawn_tile = None

        added_tile = event["pai"]
        if added_tile in actor.concealed_tiles:
            actor.concealed_tiles.remove(added_tile)

        pon_idx = None
        for i in range(len(actor.calls)):
            call_tiles = actor.revealed_tiles[i]
            if call_tiles.count(added_tile[:2]) >= constants.PON_TILES - 1:
                pon_idx = i
        actor.calls[pon_idx] = "kakan"
        insert_idx = actor.taken[pon_idx].index(True)
        actor.revealed_tiles[pon_idx].insert(insert_idx, added_tile)
        actor.taken[pon_idx].insert(insert_idx, False)
        return game_state

    def daiminkan(self, event: Dict[str, Any], game_state: GameState) -> GameState:
        """
        Update the game state to account for a "daiminkan" event.

        Args:
            event: The log line of the "daiminkan" event.
            game_state: The prior game state.

        Returns:
            GameState: The updated game state.
        """

        target = game_state.players[event["target"]]
        target.discard_pile.pop()
        target.tsumogiri.pop()
        target.discard_rotate.pop()

        actor = game_state.players[event["actor"]]
        kan_tiles = event["consumed"]
        for tile in kan_tiles:
            actor.concealed_tiles.remove(tile)

        actor.calls.append("daiminkan")
        taken_idx = (event["actor"] - event["target"]) % constants.NUM_PLAYERS - 1
        if taken_idx == constants.NUM_PLAYERS - 2:
            taken_idx += 1
        kan_tiles.insert(taken_idx, event["pai"])
        actor.revealed_tiles.append(kan_tiles)
        kan_taken = [False] * constants.KAN_TILES
        kan_taken[taken_idx] = True
        actor.taken.append(kan_taken)
        return game_state

    def dora(self, event: Dict[str, Any], game_state: GameState) -> GameState:
        """
        Update the game state to account for a "dora" event.

        Args:
            event: The log line of the "dora" event.
            game_state: The prior game state.

        Returns:
            GameState: The updated game state.
        """

        game_state.dora_indicators.append(event["dora_marker"])
        return game_state

    def hora(self, event: Dict[str, Any], game_state: GameState) -> GameState:
        """
        Update the game state to account for an "hora" event.

        Args:
            event: The log line of the "hora" event.
            game_state: The prior game state.

        Returns:
            GameState: The updated game state.
        """

        deltas = event["deltas"]
        for i in range(constants.NUM_PLAYERS):
            game_state.players[i].score += deltas[i]
        return game_state

    def ryukyoku(self, event: Dict[str, Any], game_state: GameState) -> GameState:
        """
        Update the game state to account for a "ryukyoku" event.

        Args:
            event: The log line of the "ryukyoku" event.
            game_state: The prior game state.

        Returns:
            GameState: The updated game state.
        """

        deltas = event["deltas"]
        for i in range(constants.NUM_PLAYERS):
            game_state.players[i].score += deltas[i]
        return game_state

    def end_kyoku(self, event: Dict[str, Any], game_state: GameState) -> GameState:
        """
        Update the game state to account for an "end_kyoku" event.

        Args:
            event: The log line of the "end_kyoku" event.
            game_state: The prior game state.

        Returns:
            GameState: The updated game state.
        """

        return game_state

    def end_game(self, event: Dict[str, Any], game_state: GameState) -> GameState:
        """
        Update the game state to account for an "end_game" event.

        Args:
            event: The log line of the "end_game" event.
            game_state: The prior game state.

        Returns:
            GameState: The updated game state.
        """

        return game_state
