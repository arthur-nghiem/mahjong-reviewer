# Gameplay related constants
CALL_TYPES = ["chi", "pon", "ankan", "kakan", "daiminkan"]
CALLS_MAX = 4
CHI_TILES = 3
DISCARDS_MAX = 30
DRAWING_WALL_TILES = 70
DORA_INDICATORS_MAX = 5
HONORS_IDXS = {"E": 27, "S": 28, "W": 29, "N": 30, "P": 31, "F": 32, "C": 33}
HONORS_NAMES = {"E": "east wind", "S": "south wind", "W": "west wind", "N": "north wind", 
              "P": "white dragon", "F": "green dragon", "C": "red dragon"}
KAN_TILES = 4
MIN_SCORE_DENOM = 100
NUM_PLAYERS = 4
NUM_WINDS = 4
PON_TILES = 3
RIICHI_BET_VALUE = 1000
SUIT_IDXS = {"m": -1, "p": 8, "s": 17}
SUIT_NAMES = {"m": "characters", "p": "circles", "s": "bamboo"}
TILE_COPIES = 4
TILE_ORDER = ['1m', '2m', '3m', '4m', '5m', '6m', '7m', '8m', '9m', 
              '1p', '2p', '3p', '4p', '5p', '6p', '7p', '8p', '9p', 
              '1s', '2s', '3s', '4s', '5s', '6s', '7s', '8s', '9s', 
              'E', 'S', 'W', 'N', 'P', 'F', 'C']
TILE_ORDER_WITH_REDS = ['1m', '2m', '3m', '4m', '5m', '5mr', '6m', '7m', '8m', '9m', 
                        '1p', '2p', '3p', '4p', '5p', '5pr', '6p', '7p', '8p', '9p', 
                        '1s', '2s', '3s', '4s', '5s', '5sr', '6s', '7s', '8s', '9s', 
                        'E', 'S', 'W', 'N', 'P', 'F', 'C']
TILE_TYPES = 34
WIND_NAMES = {"E": "East", "S": "South", "W": "West", "N": "North"}
WINDS = ["E", "S", "W", "N"]

# Visual rendering constants
BACKGROUND_COLOR = (19, 35, 48)
BLACK_COLOR = (0, 0, 0)
CENTER_OFFSET = 15
COMPASS_COLOR = (101, 169, 212)
COMPASS_LENGTH = 190
DISCARDS_HEIGHT = 160
DORA_INDICATORS_X_TEXT = 10
DORA_INDICATORS_X_TILES = 172
DORA_INDICATORS_WIDTH = 330
DRAW_OFFSET = 10
FRAME_COLOR = (72, 99, 118)
FRAME_LENGTH = 720
FRAME_WIDTH = 42
HAND_HEIGHT = 60
HAND_WIDTH = 566
HAND_OFFSET = 10
HONBA_WIDTH = 100
HONBA_X = 600
KYOTAKU_WIDTH = 130
KYOTAKU_X = 450
MAT_COLOR = (21, 139, 169)
NAME_FONT_SIZE = 24
RIICHI_DOT_COLOR = (164, 1, 32)
RIICHI_DOT_RADIUS = 2
RIICHI_STICK_LENGTH = 70
RIICHI_STICK_OFFSET = 16
RIICHI_STICK_WIDTH = 8
ROUND_NAME_FONT_SIZE = 20
ROUND_NAME_HEIGHT = 36
ROUND_NAME_WIDTH = 80
SCORE_FONT_SIZE = 15
SCORE_HEIGHT = 24
SCORE_OFFSET = 30
SCORE_WIDTH = 100
TILE_COUNT_FONT_SIZE = 24
TILE_COUNT_HEIGHT = 36
TILE_COUNT_WIDTH = 80
TILE_WIDTH = 30
TILE_HEIGHT = 40
TOP_FONT_SIZE = 20
TOP_INFO_HEIGHT = 48
TSUMOGIRI_BRIGHTNESS = 0.8
WHITE_COLOR = (255, 255, 255)

# Encoding constants
CHANNELS_HONBA = 4
CHANNELS_KYOTAKU = 4
CHANNELS_ROUND = 4
CHANNELS_SCORE = 11
