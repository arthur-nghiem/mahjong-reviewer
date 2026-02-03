"""
test_simulator.py: Unit tests for game simulation and event processing.
"""

import pytest
from mahjong_reviewer.simulation.simulator import (
    start_game, process_event, Event
)
from mahjong_reviewer.simulation.game_state import Player, GameState

class TestStartGame:
    """Test the start_game function."""
    
    def test_start_game_reviewer_at_position_0(self):
        """Test starting a game with reviewer at position 0."""
        event = {
            "names": ["Alice", "Bob", "Charlie", "Diana"]
        }
        game_state = start_game(event, "Alice")
        
        assert len(game_state.players) == 4
        assert game_state.reviewer_idx == 0
        assert game_state.players[0].name == "Alice"
        assert game_state.players[0].table_position == 0
        assert game_state.players[1].table_position == 1
        assert game_state.players[2].table_position == 2
        assert game_state.players[3].table_position == 3
    
    def test_start_game_reviewer_at_position_1(self):
        """Test starting a game with reviewer at position 1."""
        event = {
            "names": ["Alice", "Bob", "Charlie", "Diana"]
        }
        game_state = start_game(event, "Bob")
        
        assert game_state.reviewer_idx == 1
        assert game_state.players[1].name == "Bob"
        assert game_state.players[1].table_position == 0  # Bob is at position 0 relative to self
        assert game_state.players[2].table_position == 1  # Charlie to the right
        assert game_state.players[3].table_position == 2  # Diana across
        assert game_state.players[0].table_position == 3  # Alice to the left
    
    def test_start_game_reviewer_at_position_3(self):
        """Test starting a game with reviewer at position 3."""
        event = {
            "names": ["Alice", "Bob", "Charlie", "Diana"]
        }
        game_state = start_game(event, "Diana")
        
        assert game_state.reviewer_idx == 3
        assert game_state.players[3].table_position == 0
        assert game_state.players[0].table_position == 1
        assert game_state.players[1].table_position == 2
        assert game_state.players[2].table_position == 3
    
    def test_start_game_player_initialization(self):
        """Test that players are properly initialized."""
        event = {
            "names": ["Player1", "Player2", "Player3", "Player4"]
        }
        game_state = start_game(event, "Player1")
        
        for i, player in enumerate(game_state.players):
            assert player.name == f"Player{i+1}"
            assert player.turn_count == 0
            assert player.concealed_tiles == []
            assert player.discarded_tiles == []
            assert player.discard_pile == []


class TestProcessEvent:
    """Test the process_event function."""
    
    def test_process_event_calls_correct_handler(self):
        """Test that process_event dispatches to the correct event handler."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        game_state = GameState(players=players, reviewer_idx=0)
        
        event = {
            "type": "reach",
            "actor": 0
        }
        
        updated_state = process_event(event, game_state)
        
        # After reach event, player 0 should have reach_status = True
        assert updated_state.players[0].reach_status is True
    
    def test_process_event_returns_gamestate(self):
        """Test that process_event returns a GameState object."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        game_state = GameState(players=players, reviewer_idx=0)
        
        event = {"type": "end_game"}
        result = process_event(event, game_state)
        
        assert isinstance(result, GameState)


class TestEventStartKyoku:
    """Test the Event.start_kyoku method."""
    
    def test_start_kyoku_initializes_round(self):
        """Test that start_kyoku properly initializes a new round."""
        players = [
            Player(name=f"P{i}", table_position=i) 
            for i in range(4)
        ]
        game_state = GameState(players=players, reviewer_idx=0)
        
        event = {
            "scores": [25000, 25000, 25000, 25000],
            "oya": 0,
            "bakaze": "E",
            "dora_marker": "5m",
            "kyoku": 1,
            "honba": 0,
            "kyotaku": 0,
            "tehais": [
                ["1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m", "1p", "2p", "3p", "4p"],
                ["5p", "6p", "7p", "8p", "9p", "1s", "2s", "3s", "4s", "5s", "6s", "7s", "8s"],
                ["9s", "E", "E", "S", "S", "W", "W", "N", "N", "P", "P", "F", "F"],
                ["C", "C", "1m", "1m", "2m", "2m", "3m", "3m", "4m", "4m", "5m", "5m", "6m"]
            ]
        }
        
        event_handler = Event()
        updated_state = event_handler.start_kyoku(event, game_state)
        
        # Check game state
        assert updated_state.bakaze == "E"
        assert updated_state.dora_indicators == ["5m"]
        assert updated_state.kyoku == 1
        assert updated_state.honba == 0
        assert updated_state.kyotaku == 0
        assert updated_state.tile_count == 70
        
        # Check players
        for player in updated_state.players:
            assert player.reach_status is False
            assert player.score == 25000
            assert player.turn_count == 0
            assert len(player.concealed_tiles) == 13
            assert player.calls == []
            assert player.revealed_tiles == []
            assert player.discarded_tiles == []
            assert player.discard_pile == []
            assert player.drawn_tile is None
    
    def test_start_kyoku_seat_winds(self):
        """Test that seat winds are correctly assigned."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        game_state = GameState(players=players, reviewer_idx=0)
        
        event = {
            "scores": [25000, 25000, 25000, 25000],
            "oya": 2,  # Player 2 is dealer
            "bakaze": "S",
            "dora_marker": "1p",
            "kyoku": 3,
            "honba": 1,
            "kyotaku": 1,
            "tehais": [["1m"] * 13 for _ in range(4)]
        }
        
        event_handler = Event()
        updated_state = event_handler.start_kyoku(event, game_state)
        
        # When oya=2, seat winds should be: W, N, E, S
        assert updated_state.players[0].seat_wind == "W"
        assert updated_state.players[1].seat_wind == "N"
        assert updated_state.players[2].seat_wind == "E"  # Dealer
        assert updated_state.players[3].seat_wind == "S"


class TestEventTsumo:
    """Test the Event.tsumo method."""
    
    def test_tsumo_draws_tile(self):
        """Test that tsumo event draws a tile for the actor."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        game_state = GameState(players=players, reviewer_idx=0, tile_count=70)
        
        event = {
            "actor": 0,
            "pai": "3p"
        }
        
        event_handler = Event()
        updated_state = event_handler.tsumo(event, game_state)
        
        assert updated_state.players[0].drawn_tile == "3p"
        assert updated_state.players[0].turn_count == 1
        assert updated_state.tile_count == 69
    
    def test_tsumo_increments_turn_count(self):
        """Test that turn count increments correctly."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        game_state = GameState(players=players, reviewer_idx=0, tile_count=70)
        
        event_handler = Event()
        
        # Player 0 draws twice
        game_state = event_handler.tsumo({"actor": 0, "pai": "1m"}, game_state)
        game_state.players[0].drawn_tile = None  # Clear for next draw
        game_state = event_handler.tsumo({"actor": 0, "pai": "2m"}, game_state)
        
        assert game_state.players[0].turn_count == 2
        assert game_state.tile_count == 68


class TestEventDahai:
    """Test the Event.dahai method."""
    
    def test_dahai_discards_from_hand(self):
        """Test that dahai discards a tile from concealed hand."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        players[0].concealed_tiles = ["1m", "2m", "3m", "4m"]
        players[0].drawn_tile = "5m"
        game_state = GameState(players=players, reviewer_idx=0)
        
        event = {
            "actor": 0,
            "pai": "1m",
            "tsumogiri": False
        }
        
        event_handler = Event()
        updated_state = event_handler.dahai(event, game_state)
        
        assert "1m" not in updated_state.players[0].concealed_tiles
        assert "5m" in updated_state.players[0].concealed_tiles
        assert updated_state.players[0].drawn_tile is None
        assert updated_state.players[0].discarded_tiles == ["1m"]
        assert updated_state.players[0].discard_pile == ["1m"]
        assert updated_state.players[0].tsumogiri == [False]
    
    def test_dahai_tsumogiri(self):
        """Test discarding the just-drawn tile (tsumogiri)."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        players[0].concealed_tiles = ["1m", "2m", "3m"]
        players[0].drawn_tile = "4m"
        game_state = GameState(players=players, reviewer_idx=0)
        
        event = {
            "actor": 0,
            "pai": "4m",
            "tsumogiri": True
        }
        
        event_handler = Event()
        updated_state = event_handler.dahai(event, game_state)
        
        assert updated_state.players[0].discarded_tiles == ["4m"]
        assert updated_state.players[0].discard_pile == ["4m"]
        assert updated_state.players[0].tsumogiri == [True]
    
    def test_dahai_after_riichi_rotates_discard(self):
        """Test that first discard after riichi is rotated."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        players[0].concealed_tiles = ["1m", "2m", "3m"]
        players[0].reach_status = True
        game_state = GameState(players=players, reviewer_idx=0)
        
        event = {
            "actor": 0,
            "pai": "1m",
            "tsumogiri": False
        }
        
        event_handler = Event()
        updated_state = event_handler.dahai(event, game_state)
        
        assert updated_state.players[0].discard_rotate == [True]
        
        # Second discard should not be rotated
        updated_state.players[0].concealed_tiles = ["2m", "3m"]
        event2 = {"actor": 0, "pai": "2m", "tsumogiri": False}
        updated_state = event_handler.dahai(event2, updated_state)
        
        assert updated_state.players[0].discard_rotate == [True, False]


class TestEventReach:
    """Test the Event.reach and reach_accepted methods."""
    
    def test_reach_sets_status(self):
        """Test that reach event sets reach_status."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        game_state = GameState(players=players, reviewer_idx=0)
        
        event = {"actor": 1}
        
        event_handler = Event()
        updated_state = event_handler.reach(event, game_state)
        
        assert updated_state.players[1].reach_status is True
    
    def test_reach_accepted_deducts_bet(self):
        """Test that reach_accepted deducts 1000 points and adds to kyotaku."""
        players = [
            Player(name=f"P{i}", table_position=i, score=25000) 
            for i in range(4)
        ]
        game_state = GameState(players=players, reviewer_idx=0, kyotaku=0)
        
        event = {"actor": 0}
        
        event_handler = Event()
        updated_state = event_handler.reach_accepted(event, game_state)
        
        assert updated_state.players[0].score == 24000
        assert updated_state.kyotaku == 1
    
    def test_multiple_riichi_bets(self):
        """Test multiple players declaring riichi."""
        players = [
            Player(name=f"P{i}", table_position=i, score=25000) 
            for i in range(4)
        ]
        game_state = GameState(players=players, reviewer_idx=0, kyotaku=0)
        
        event_handler = Event()
        
        # Player 0 riichi
        game_state = event_handler.reach_accepted({"actor": 0}, game_state)
        # Player 2 riichi
        game_state = event_handler.reach_accepted({"actor": 2}, game_state)
        
        assert game_state.players[0].score == 24000
        assert game_state.players[2].score == 24000
        assert game_state.kyotaku == 2


class TestEventChi:
    """Test the Event.chi method."""
    
    def test_chi_removes_from_target_discard(self):
        """Test that chi removes tile from target's discards."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        players[0].discarded_tiles = ["4m"]
        players[0].discard_pile = ["4m"]
        players[0].tsumogiri = [False]
        players[0].discard_rotate = [False]
        players[1].concealed_tiles = ["5m", "6m"]
        game_state = GameState(players=players, reviewer_idx=0)
        
        event = {
            "actor": 1,
            "target": 0,
            "pai": "4m",
            "consumed": ["5m", "6m"]
        }
        
        event_handler = Event()
        updated_state = event_handler.chi(event, game_state)
        
        # Target's discard should be removed
        assert updated_state.players[0].discard_pile == []
        assert updated_state.players[0].discarded_tiles == ["4m"]
        
        # Actor should have the chi recorded
        assert updated_state.players[1].calls == ["chi"]
        assert updated_state.players[1].revealed_tiles == [["4m", "5m", "6m"]]
        assert updated_state.players[1].taken == [[True, False, False]]
        assert "5m" not in updated_state.players[1].concealed_tiles
        assert "6m" not in updated_state.players[1].concealed_tiles
        assert updated_state.players[1].turn_count == 1


class TestEventPon:
    """Test the Event.pon method."""
    
    def test_pon_basic(self):
        """Test basic pon functionality."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        players[0].discarded_tiles = ["E"]
        players[0].discard_pile = ["E"]
        players[0].tsumogiri = [False]
        players[0].discard_rotate = [False]
        players[2].concealed_tiles = ["E", "E"]
        game_state = GameState(players=players, reviewer_idx=0)
        
        event = {
            "actor": 2,
            "target": 0,
            "pai": "E",
            "consumed": ["E", "E"]
        }
        
        event_handler = Event()
        updated_state = event_handler.pon(event, game_state)
        
        assert updated_state.players[0].discard_pile == []
        assert updated_state.players[0].discarded_tiles == ["E"]
        assert updated_state.players[2].calls == ["pon"]
        assert len(updated_state.players[2].revealed_tiles[0]) == 3
        assert updated_state.players[2].turn_count == 1
    
    def test_pon_taken_position(self):
        """Test that pon correctly marks which tile was taken."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        players[1].discarded_tiles = ["P"]
        players[1].discard_pile = ["P"]
        players[1].tsumogiri = [False]
        players[1].discard_rotate = [False]
        players[3].concealed_tiles = ["P", "P"]
        game_state = GameState(players=players, reviewer_idx=0)
        
        event = {
            "actor": 3,
            "target": 1,
            "pai": "P",
            "consumed": ["P", "P"]
        }
        
        event_handler = Event()
        updated_state = event_handler.pon(event, game_state)
        
        # Player 3 took from the facing player, so middle tile is taken
        assert updated_state.players[3].taken[0][1] is True


class TestEventDora:
    """Test the Event.dora method."""
    
    def test_dora_adds_indicator(self):
        """Test that dora event adds a new indicator."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        game_state = GameState(
            players=players, 
            reviewer_idx=0, 
            dora_indicators=["5m"]
        )
        
        event = {"dora_marker": "3p"}
        
        event_handler = Event()
        updated_state = event_handler.dora(event, game_state)
        
        assert updated_state.dora_indicators == ["5m", "3p"]
    
    def test_multiple_dora_indicators(self):
        """Test adding multiple dora indicators (from kans)."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        game_state = GameState(
            players=players, 
            reviewer_idx=0, 
            dora_indicators=["1m"]
        )
        
        event_handler = Event()
        
        # Add kan dora
        game_state = event_handler.dora({"dora_marker": "2p"}, game_state)
        game_state = event_handler.dora({"dora_marker": "3s"}, game_state)
        game_state = event_handler.dora({"dora_marker": "E"}, game_state)
        
        assert game_state.dora_indicators == ["1m", "2p", "3s", "E"]
        assert len(game_state.dora_indicators) == 4


class TestEventHora:
    """Test the Event.hora method."""
    
    def test_hora_updates_scores(self):
        """Test that hora updates player scores correctly."""
        players = [
            Player(name=f"P{i}", table_position=i, score=25000) 
            for i in range(4)
        ]
        game_state = GameState(players=players, reviewer_idx=0)
        
        event = {
            "deltas": [8000, -2000, -3000, -3000]
        }
        
        event_handler = Event()
        updated_state = event_handler.hora(event, game_state)
        
        assert updated_state.players[0].score == 33000
        assert updated_state.players[1].score == 23000
        assert updated_state.players[2].score == 22000
        assert updated_state.players[3].score == 22000


class TestEventRyukyoku:
    """Test the Event.ryukyoku method."""
    
    def test_ryukyoku_updates_scores(self):
        """Test that ryukyoku (draw) updates scores."""
        players = [
            Player(name=f"P{i}", table_position=i, score=25000) 
            for i in range(4)
        ]
        game_state = GameState(players=players, reviewer_idx=0)
        
        event = {
            "deltas": [1500, 1500, -1500, -1500]
        }
        
        event_handler = Event()
        updated_state = event_handler.ryukyoku(event, game_state)
        
        assert updated_state.players[0].score == 26500
        assert updated_state.players[1].score == 26500
        assert updated_state.players[2].score == 23500
        assert updated_state.players[3].score == 23500


class TestEventEndKyoku:
    """Test the Event.end_kyoku method."""
    
    def test_end_kyoku_returns_state(self):
        """Test that end_kyoku returns the game state unchanged."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        game_state = GameState(players=players, reviewer_idx=0)
        
        event = {}
        
        event_handler = Event()
        updated_state = event_handler.end_kyoku(event, game_state)
        
        assert updated_state is game_state


class TestEventEndGame:
    """Test the Event.end_game method."""
    
    def test_end_game_returns_state(self):
        """Test that end_game returns the game state unchanged."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        game_state = GameState(players=players, reviewer_idx=0)
        
        event = {}
        
        event_handler = Event()
        updated_state = event_handler.end_game(event, game_state)
        
        assert updated_state is game_state


class TestEventIntegration:
    """Integration tests for event processing."""
    
    def test_full_turn_sequence(self):
        """Test a complete turn: tsumo -> dahai."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        players[0].concealed_tiles = ["1m", "2m", "3m"]
        game_state = GameState(players=players, reviewer_idx=0, tile_count=70)
        
        event_handler = Event()
        
        # Player draws
        game_state = event_handler.tsumo(
            {"actor": 0, "pai": "4m"}, 
            game_state
        )
        assert game_state.players[0].drawn_tile == "4m"
        assert game_state.tile_count == 69
        
        # Player discards
        game_state = event_handler.dahai(
            {"actor": 0, "pai": "1m", "tsumogiri": False}, 
            game_state
        )
        assert game_state.players[0].drawn_tile is None
        assert "4m" in game_state.players[0].concealed_tiles
        assert "1m" not in game_state.players[0].concealed_tiles
        assert game_state.players[0].discard_pile == ["1m"]
        assert game_state.players[0].discarded_tiles == ["1m"]
    
    def test_riichi_sequence(self):
        """Test declaring and accepting riichi."""
        players = [
            Player(name=f"P{i}", table_position=i, score=25000) 
            for i in range(4)
        ]
        players[0].concealed_tiles = ["2m", "3m", "7m"]
        game_state = GameState(players=players, reviewer_idx=0, kyotaku=0)
        
        event_handler = Event()
        
        # Declare riichi
        game_state = event_handler.reach({"actor": 0}, game_state)
        assert game_state.players[0].reach_status is True

        # Discard tile to achieve tenpai
        game_state = event_handler.dahai(
            {"actor": 0, "pai": "7m", "tsumogiri": False}, 
            game_state
        )
        assert "7m" not in game_state.players[0].concealed_tiles
        assert game_state.players[0].discard_pile == ["7m"]
        assert game_state.players[0].discarded_tiles == ["7m"]
        assert game_state.players[0].discard_rotate == [True]
        
        # Riichi accepted
        game_state = event_handler.reach_accepted({"actor": 0}, game_state)
        assert game_state.players[0].score == 24000
        assert game_state.kyotaku == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])