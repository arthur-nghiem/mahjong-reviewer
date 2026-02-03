"""
test_game_state.py: Unit tests for game state management classes.
"""

import pytest
from mahjong_reviewer.simulation.game_state import Player, GameState

class TestPlayer:
    """Test the Player dataclass."""
    
    def test_player_initialization_minimal(self):
        """Test creating a player with minimal required fields."""
        player = Player(name="TestPlayer", table_position=0)
        
        assert player.name == "TestPlayer"
        assert player.table_position == 0
        assert player.reach_status is False
        assert player.score is 0
        assert player.turn_count == 0
        assert player.seat_wind is "E"
        assert player.concealed_tiles == []
        assert player.calls == []
        assert player.revealed_tiles == []
        assert player.taken == []
        assert player.discarded_tiles == []
        assert player.discard_pile == []
        assert player.tsumogiri == []
        assert player.discard_rotate == []
        assert player.drawn_tile is None
    
    def test_player_initialization_full(self):
        """Test creating a player with all fields specified."""
        player = Player(
            name="FullPlayer",
            table_position=1,
            reach_status=False,
            score=25000,
            turn_count=5,
            seat_wind="E",
            concealed_tiles=["1m", "2m", "3m"],
            calls=["chi"],
            revealed_tiles=[["4m", "5m", "6m"]],
            taken=[[True, False, False]],
            discarded_tiles=["7m", "8m"],
            discard_pile=["7m", "8m"],
            tsumogiri=[True, False],
            discard_rotate=[False, False],
            drawn_tile="9m"
        )
        
        assert player.name == "FullPlayer"
        assert player.table_position == 1
        assert player.reach_status is False
        assert player.score == 25000
        assert player.turn_count == 5
        assert player.seat_wind == "E"
        assert player.concealed_tiles == ["1m", "2m", "3m"]
        assert player.calls == ["chi"]
        assert player.revealed_tiles == [["4m", "5m", "6m"]]
        assert player.taken == [[True, False, False]]
        assert player.discarded_tiles == ["7m", "8m"]
        assert player.discard_pile == ["7m", "8m"]
        assert player.tsumogiri == [True, False]
        assert player.discard_rotate == [False, False]
        assert player.drawn_tile == "9m"
    
    def test_player_concealed_tiles_mutation(self):
        """Test that concealed tiles can be modified."""
        player = Player(name="Test", table_position=0)
        
        # Add tiles
        player.concealed_tiles.append("1m")
        player.concealed_tiles.append("2m")
        assert len(player.concealed_tiles) == 2
        
        # Remove tiles
        player.concealed_tiles.remove("1m")
        assert player.concealed_tiles == ["2m"]
    
    def test_player_discard_tracking(self):
        """Test tracking discarded tiles with metadata."""
        player = Player(name="Test", table_position=0)
        
        # Discard a tile (tsumogiri)
        player.discarded_tiles.append("5p")
        player.discard_pile.append("5p")
        player.tsumogiri.append(True)
        player.discard_rotate.append(False)
        
        # Discard another tile (not tsumogiri)
        player.discarded_tiles.append("6p")
        player.discard_pile.append("6p")
        player.tsumogiri.append(False)
        player.discard_rotate.append(False)

        assert len(player.discarded_tiles) == 2
        assert len(player.discard_pile) == 2
        assert player.tsumogiri == [True, False]
        assert all(not rotate for rotate in player.discard_rotate)
    
    def test_player_calls_and_revealed_tiles(self):
        """Test managing called tiles."""
        player = Player(name="Test", table_position=0)
        
        # Make a chi call
        player.calls.append("chi")
        player.revealed_tiles.append(["4s", "5s", "6s"])
        player.taken.append([True, False, False])
        
        # Make a pon call
        player.calls.append("pon")
        player.revealed_tiles.append(["E", "E", "E"])
        player.taken.append([False, True, False])
        
        assert len(player.calls) == 2
        assert player.calls == ["chi", "pon"]
        assert len(player.revealed_tiles) == 2
        assert player.revealed_tiles[0] == ["4s", "5s", "6s"]
        assert player.revealed_tiles[1] == ["E", "E", "E"]
    
    def test_player_riichi_state(self):
        """Test riichi status tracking."""
        player = Player(name="Test", table_position=0, score=30000)
        
        assert player.reach_status is False
        
        # Declare riichi
        player.reach_status = True
        assert player.reach_status is True
        
        # Pay riichi bet
        player.score -= 1000
        assert player.score == 29000
    
    def test_player_drawn_tile(self):
        """Test drawn tile tracking."""
        player = Player(name="Test", table_position=0)
        
        assert player.drawn_tile is None
        
        # Draw a tile
        player.drawn_tile = "3p"
        assert player.drawn_tile == "3p"
        
        # Clear drawn tile (after discarding)
        player.drawn_tile = None
        assert player.drawn_tile is None


class TestGameState:
    """Test the GameState dataclass."""
    
    def test_gamestate_initialization_minimal(self):
        """Test creating a game state with minimal fields."""
        players = [
            Player(name="Player1", table_position=0),
            Player(name="Player2", table_position=1),
            Player(name="Player3", table_position=2),
            Player(name="Player4", table_position=3),
        ]
        game_state = GameState(players=players, reviewer_idx=0)
        
        assert len(game_state.players) == 4
        assert game_state.reviewer_idx == 0
        assert game_state.bakaze is "E"
        assert game_state.dora_indicators == []
        assert game_state.kyoku is 1
        assert game_state.honba is 0
        assert game_state.kyotaku is 0
        assert game_state.tile_count is 70
    
    def test_gamestate_initialization_full(self):
        """Test creating a game state with all fields."""
        players = [
            Player(name=f"Player{i}", table_position=i, score=25000)
            for i in range(4)
        ]
        game_state = GameState(
            players=players,
            reviewer_idx=1,
            bakaze="E",
            dora_indicators=["5m"],
            kyoku=1,
            honba=0,
            kyotaku=0,
            tile_count=70
        )
        
        assert len(game_state.players) == 4
        assert game_state.reviewer_idx == 1
        assert game_state.bakaze == "E"
        assert game_state.dora_indicators == ["5m"]
        assert game_state.kyoku == 1
        assert game_state.honba == 0
        assert game_state.kyotaku == 0
        assert game_state.tile_count == 70
    
    def test_gamestate_reviewer_index(self):
        """Test that reviewer_idx correctly identifies the reviewing player."""
        players = [
            Player(name="Alice", table_position=2),
            Player(name="Bob", table_position=3),
            Player(name="Charlie", table_position=0),
            Player(name="Diana", table_position=1),
        ]
        reviewer_idx = 2
        
        # Test different reviewer positions
        game_state = GameState(players=players, reviewer_idx=reviewer_idx)
        assert game_state.players[reviewer_idx].table_position == 0
    
    def test_gamestate_dora_indicators_accumulation(self):
        """Test accumulating dora indicators throughout the game."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        game_state = GameState(players=players, reviewer_idx=0)
        
        # Start with initial dora
        game_state.dora_indicators = ["1m"]
        assert len(game_state.dora_indicators) == 1
        
        # Add kan dora
        game_state.dora_indicators.append("2p")
        assert len(game_state.dora_indicators) == 2
        
        # Add more kan dora
        game_state.dora_indicators.append("3s")
        assert len(game_state.dora_indicators) == 3
        assert game_state.dora_indicators == ["1m", "2p", "3s"]
    
    def test_gamestate_tile_count_decreases(self):
        """Test tile count decreasing as game progresses."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        game_state = GameState(players=players, reviewer_idx=0, tile_count=70)
        
        # Simulate draws
        for _ in range(10):
            game_state.tile_count -= 1
        
        assert game_state.tile_count == 60
    
    def test_gamestate_riichi_bets(self):
        """Test tracking riichi bets on the table."""
        players = [
            Player(name=f"P{i}", table_position=i, score=25000) 
            for i in range(4)
        ]
        game_state = GameState(players=players, reviewer_idx=0, kyotaku=0)
        
        # Player 0 declares riichi
        players[0].score -= 1000
        game_state.kyotaku += 1
        assert game_state.kyotaku == 1
        assert players[0].score == 24000
        
        # Player 2 declares riichi
        players[2].score -= 1000
        game_state.kyotaku += 1
        assert game_state.kyotaku == 2
        assert players[2].score == 24000
    
    def test_gamestate_round_progression(self):
        """Test round wind and kyoku progression."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        
        # East 1
        game_state = GameState(
            players=players, 
            reviewer_idx=0, 
            bakaze="E", 
            kyoku=1, 
            honba=0
        )
        assert game_state.bakaze == "E"
        assert game_state.kyoku == 1
        assert game_state.honba == 0
        
        # East 1 repeat
        game_state.honba = 1
        assert game_state.honba == 1
        
        # East 2
        game_state.kyoku = 2
        game_state.honba = 0
        assert game_state.kyoku == 2
        assert game_state.honba == 0
        
        # South round
        game_state.bakaze = "S"
        game_state.kyoku = 1
        assert game_state.bakaze == "S"
        assert game_state.kyoku == 1
    
    def test_gamestate_player_seats(self):
        """Test player seat wind assignments."""
        players = [
            Player(name=f"P{i}", table_position=i, seat_wind=None) 
            for i in range(4)
        ]
        
        # Assign seat winds
        winds = ["E", "S", "W", "N"]
        oya_idx = 2
        
        for i in range(4):
            players[i].seat_wind = winds[(i - oya_idx) % 4]
        
        assert players[0].seat_wind == "W"
        assert players[1].seat_wind == "N"
        assert players[2].seat_wind == "E"
        assert players[3].seat_wind == "S"
    
    def test_gamestate_multiple_rounds(self):
        """Test game state across multiple rounds."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        game_state = GameState(players=players, reviewer_idx=0)
        
        # Round 1
        game_state.bakaze = "E"
        game_state.kyoku = 1
        game_state.honba = 0
        game_state.tile_count = 70
        game_state.dora_indicators = ["1m"]
        
        assert game_state.tile_count == 70
        
        # Round 2 - reset tile count and dora
        game_state.kyoku = 2
        game_state.tile_count = 70
        game_state.dora_indicators = ["2p"]
        
        assert game_state.tile_count == 70
        assert len(game_state.dora_indicators) == 1
        assert game_state.dora_indicators[0] == "2p"
    
    def test_gamestate_immutability_of_player_list(self):
        """Test that the player list reference is maintained."""
        players = [Player(name=f"P{i}", table_position=i) for i in range(4)]
        game_state = GameState(players=players, reviewer_idx=0)
        
        # Modify a player through game_state
        game_state.players[0].score = 30000
        
        # Original players list should also be modified (same reference)
        assert players[0].score == 30000

class TestGameStateIntegration:
    """Integration tests for GameState and Player working together."""
    
    def test_full_game_scenario(self):
        """Test a realistic game scenario with multiple actions."""
        # Setup game
        players = [
            Player(name="Alice", table_position=0, score=25000),
            Player(name="Bob", table_position=1, score=25000),
            Player(name="Charlie", table_position=2, score=25000),
            Player(name="Diana", table_position=3, score=25000),
        ]
        game_state = GameState(
            players=players,
            reviewer_idx=0,
            bakaze="E",
            kyoku=1,
            honba=0,
            kyotaku=0,
            tile_count=70,
            dora_indicators=["5m"]
        )
        
        # Alice draws
        alice = game_state.players[0]
        alice.drawn_tile = "3p"
        alice.turn_count += 1
        game_state.tile_count -= 1
        
        assert alice.drawn_tile == "3p"
        assert alice.turn_count == 1
        assert game_state.tile_count == 69
        
        # Alice discards
        alice.concealed_tiles.append(alice.drawn_tile)
        alice.drawn_tile = None
        discard = "3p"
        alice.concealed_tiles.remove(discard)
        alice.discarded_tiles.append(discard)
        alice.discard_pile.append(discard)
        alice.tsumogiri.append(False)
        alice.discard_rotate.append(False)
        
        assert alice.drawn_tile is None
        assert len(alice.discarded_tiles) == 1
        assert len(alice.discard_pile) == 1
        assert alice.discarded_tiles[0] == "3p"
        assert alice.discard_pile[0] == "3p"
        
        # Bob declares riichi
        bob = game_state.players[1]
        bob.reach_status = True
        bob.score -= 1000
        game_state.kyotaku += 1
        
        assert bob.reach_status is True
        assert bob.score == 24000
        assert game_state.kyotaku == 1
        
        # Verify game state integrity
        assert len(game_state.players) == 4
        assert game_state.tile_count == 69
        assert game_state.kyotaku == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])