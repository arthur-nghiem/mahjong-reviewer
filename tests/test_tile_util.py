"""
test_tile_util.py: Unit tests for tile utility functions.
"""

import pytest
from src.mahjong_reviewer.utils import tile_util

class TestTileConversion:
    """Test tile conversion functions."""
    
    def test_tiles_to_counts_empty(self):
        """Test conversion of empty tile list."""
        result = tile_util.tiles_to_counts([])
        assert len(result) == 34
        assert sum(result) == 0
    
    def test_tiles_to_counts_basic(self):
        """Test conversion of basic tile list."""
        tiles = ['1m', '1m', 'E', 'P']
        result = tile_util.tiles_to_counts(tiles)
        assert result[0] == 2
        assert result[27] == 1
        assert result[31] == 1
    
    def test_tiles_to_idxs_roundtrip(self):
        """Test that conversion is reversible."""
        tiles = ['2p', '3s', 'W', 'F']
        idxs = tile_util.tiles_to_idxs(tiles)
        reconstructed = tile_util.idxs_to_tiles(idxs)
        assert tiles == reconstructed
    
    def test_tiles_to_counts_all_same(self):
        """Test four of the same tile."""
        tiles = ['5s', '5s', '5s', '5s']
        result = tile_util.tiles_to_counts(tiles)
        assert result[22] == 4
        assert sum(result) == 4

class TestOtherUtils:
    """Test other tile utilities."""

    def test_name_tile_honors(self):
        """Test naming of honor tiles."""
        assert tile_util.name_tile('E') == 'east wind'
        assert tile_util.name_tile('P') == 'white dragon'
    
    def test_name_tile_suits(self):
        """Test naming of suited tiles."""
        assert tile_util.name_tile('5p') == '5 of circles'
        assert tile_util.name_tile('5pr') == 'red 5 of circles'
        assert tile_util.name_tile('2s') == '2 of bamboo'
        assert tile_util.name_tile('9m') == '9 of characters'

    def test_sort_tiles_basic(self):
        """Test tile sorting."""
        tiles = ['E', '1p', '9m', '1m']
        sorted_tiles = tile_util.sort_tiles(tiles)
        assert sorted_tiles == ['1m', '9m', '1p', 'E']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])