"""
renderer.py: Produces a visual representation of the game state from data.
"""

from config import constants
from config.config import Config
from mahjong_reviewer.simulation.game_state import GameState
from mahjong_reviewer.simulation.game_state import Player
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from typing import Any, Dict


class Renderer:
    """Class used to create visuals representing game states.

    Attributes:
        tile_imgs (Dict[str, Image.Image]): Images of each tile type.
        config (Config): The configuration data.
        background_img (Image.Image): The image of the background.
        compass_img (Image.Image): The image of the compass.
        riichi_stick_img (Image.Image): The image of a riichi stick.
    """

    def __init__(self, tile_imgs: Dict[str, Image.Image], game_state: GameState):
        self.tile_imgs = tile_imgs
        self.config = Config()
        self.background_img = self.construct_background(game_state)
        self.compass_img = self.construct_compass(game_state)
        self.riichi_stick_img = self.construct_riichi_stick()

    def construct_background(self, game_state: GameState) -> Image.Image:
        """
        Construct the background based on the starting game state.

        Args:
            game_state: The game state at the very beginning of the game.

        Returns:
            Image.Image: An image displaying the frame, mat, and player names.
        """

        frame_length = constants.FRAME_LENGTH
        frame_width = constants.FRAME_WIDTH
        top_info_height = constants.TOP_INFO_HEIGHT
        mat_length = frame_length - 2 * frame_width
        background_img = Image.new(
            "RGBA", (frame_length, frame_length + top_info_height), color=constants.BACKGROUND_COLOR
        )
        frame_img = Image.new("RGBA", (frame_length, frame_length), color=constants.FRAME_COLOR)
        mat_img = Image.new("RGBA", (mat_length, mat_length), color=constants.MAT_COLOR)
        background_img.paste(frame_img, (0, top_info_height))
        background_img.paste(mat_img, (frame_width, top_info_height + frame_width))

        name_font = ImageFont.truetype(self.config.FONT_DIR, constants.NAME_FONT_SIZE)
        draw = ImageDraw.Draw(background_img)
        name_positions = [
            (0, top_info_height + frame_length - frame_width),
            (frame_length - frame_width, top_info_height),
            (0, top_info_height),
            (0, top_info_height),
        ]
        for i in range(constants.NUM_PLAYERS):
            name_img = Image.new("RGBA", (frame_length, frame_width))
            draw = ImageDraw.Draw(name_img)
            name_center = (int(frame_length / 2), int(frame_width / 2))
            draw.text(
                name_center,
                game_state.players[i].name,
                fill=constants.WHITE_COLOR,
                font=name_font,
                anchor="mm",
            )
            table_position = game_state.players[i].table_position
            for _ in range(table_position):
                name_img = name_img.transpose(Image.Transpose.ROTATE_90)
            background_img.paste(name_img, name_positions[table_position], name_img)
        return background_img

    def construct_compass(self, game_state: GameState) -> Image.Image:
        """
        Construct the compass based on the starting game state.

        Args:
            game_state: The game state at the very beginning of the game.

        Returns:
            Image.Image: An image displaying the compass, rotated such that the reviewer is at the bottom.
        """

        compass_length = constants.COMPASS_LENGTH
        tile_width = constants.TILE_WIDTH
        tile_height = constants.TILE_HEIGHT
        compass_img = Image.new(
            "RGBA", (compass_length, compass_length), color=constants.COMPASS_COLOR
        )
        wind_positions = [
            (0, compass_length - tile_height),
            (compass_length - tile_height, compass_length - tile_width),
            (compass_length - tile_width, 0),
            (0, 0),
        ]
        for i in range(constants.NUM_WINDS):
            wind_img = self.tile_imgs[constants.WINDS[i]].copy()
            for _ in range(i):
                wind_img = wind_img.transpose(Image.Transpose.ROTATE_90)
            compass_img.paste(wind_img, wind_positions[i], wind_img)
        for _ in range(game_state.reviewer_idx):
            compass_img = compass_img.transpose(Image.Transpose.ROTATE_270)
        return compass_img

    def construct_riichi_stick(self) -> Image.Image:
        """
        Construct the riichi stick image.

        Returns:
            Image.Image: An image of a riichi stick.
        """

        riichi_stick_size = (constants.RIICHI_STICK_LENGTH, constants.RIICHI_STICK_WIDTH)
        riichi_stick_img = Image.new("RGBA", riichi_stick_size, color=constants.WHITE_COLOR)
        draw = ImageDraw.Draw(riichi_stick_img)
        draw.circle(
            xy=(int(constants.RIICHI_STICK_LENGTH / 2), int(constants.RIICHI_STICK_WIDTH / 2)),
            radius=constants.RIICHI_DOT_RADIUS,
            fill=constants.RIICHI_DOT_COLOR,
            outline=constants.RIICHI_DOT_COLOR,
            width=constants.RIICHI_DOT_RADIUS,
        )
        return riichi_stick_img

    def render_compass(self, game_state: GameState, composite: Image.Image) -> Image.Image:
        """
        Place the compass on the composite image with the correct rotation and position.

        Args:
            game_state: The game state at the start of a round.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        compass_img = self.compass_img.copy()
        for _ in range(game_state.kyoku - 1):
            compass_img = compass_img.transpose(Image.Transpose.ROTATE_270)
        compass_length = constants.COMPASS_LENGTH
        frame_length = constants.FRAME_LENGTH
        top_info_height = constants.TOP_INFO_HEIGHT
        compass_x = int((frame_length - compass_length) / 2)
        composite.paste(compass_img, (compass_x, compass_x + top_info_height), compass_img)
        return composite

    def render_round_name(self, game_state: GameState, composite: Image.Image) -> Image.Image:
        """
        Write the round name on the composite image.

        Args:
            game_state: The game state at the start of a round.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        center_font = ImageFont.truetype(self.config.FONT_DIR, constants.ROUND_NAME_FONT_SIZE)
        round_name_size = (constants.ROUND_NAME_WIDTH, constants.ROUND_NAME_HEIGHT)
        round_name_img = Image.new("RGBA", round_name_size, color=constants.COMPASS_COLOR)
        draw = ImageDraw.Draw(round_name_img)
        round_name_center = (
            int(constants.ROUND_NAME_WIDTH / 2),
            int(constants.ROUND_NAME_HEIGHT / 2),
        )
        draw.text(
            round_name_center,
            f"{constants.WIND_NAMES[game_state.bakaze]} {game_state.kyoku}",
            fill=constants.BLACK_COLOR,
            font=center_font,
            anchor="mm",
        )
        frame_length = constants.FRAME_LENGTH
        top_info_height = constants.TOP_INFO_HEIGHT
        center_offset = constants.CENTER_OFFSET
        round_name_x = int((frame_length - constants.ROUND_NAME_WIDTH) / 2)
        round_name_y = (
            int((frame_length - constants.ROUND_NAME_HEIGHT) / 2) + top_info_height - center_offset
        )
        composite.paste(round_name_img, (round_name_x, round_name_y), round_name_img)
        return composite

    def render_tile_count(self, game_state: GameState, composite: Image.Image) -> Image.Image:
        """
        Write the tile count on the composite image.

        Args:
            game_state: The game state at any point where the tile count changes.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        center_font = ImageFont.truetype(self.config.FONT_DIR, constants.TILE_COUNT_FONT_SIZE)
        tile_count_size = (constants.TILE_COUNT_WIDTH, constants.TILE_COUNT_HEIGHT)
        tile_count_img = Image.new("RGBA", tile_count_size, color=constants.COMPASS_COLOR)
        draw = ImageDraw.Draw(tile_count_img)
        tile_count_center = (
            int(constants.TILE_COUNT_WIDTH / 2),
            int(constants.TILE_COUNT_HEIGHT / 2),
        )
        draw.text(
            tile_count_center,
            f"x{game_state.tile_count}",
            fill=constants.BLACK_COLOR,
            font=center_font,
            anchor="mm",
        )
        frame_length = constants.FRAME_LENGTH
        top_info_height = constants.TOP_INFO_HEIGHT
        center_offset = constants.CENTER_OFFSET
        tile_count_x = int((frame_length - constants.TILE_COUNT_WIDTH) / 2)
        tile_count_y = (
            int((frame_length - constants.TILE_COUNT_HEIGHT) / 2) + top_info_height + center_offset
        )
        composite.paste(tile_count_img, (tile_count_x, tile_count_y), tile_count_img)
        return composite

    def render_scores(self, game_state: GameState, composite: Image.Image) -> Image.Image:
        """
        Write the scores on the composite image.

        Args:
            game_state: The game state at any point where the scores change.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        score_font = ImageFont.truetype(self.config.FONT_DIR, constants.SCORE_FONT_SIZE)
        score_width = constants.SCORE_WIDTH
        score_height = constants.SCORE_HEIGHT
        score_size = (score_width, score_height)
        draw_position = (int(score_width / 2), int(score_height / 2))
        compass_length = constants.COMPASS_LENGTH
        frame_length = constants.FRAME_LENGTH
        score_offset = constants.SCORE_OFFSET
        top_info_height = constants.TOP_INFO_HEIGHT
        score_positions = [
            (
                int(frame_length / 2) - int(score_width / 2),
                top_info_height
                + int((frame_length + compass_length) / 2)
                - score_height
                - score_offset,
            ),
            (
                int((frame_length + compass_length) / 2) - score_height - score_offset,
                int(frame_length / 2) - int(score_width / 2) + top_info_height,
            ),
            (
                int(frame_length / 2) - int(score_width / 2),
                top_info_height + int((frame_length - compass_length) / 2) + score_offset,
            ),
            (
                int((frame_length - compass_length) / 2) + score_offset,
                int(frame_length / 2) - int(score_width / 2) + top_info_height,
            ),
        ]
        for i in range(constants.NUM_PLAYERS):
            player = game_state.players[i]
            score_img = Image.new("RGBA", score_size, color=constants.COMPASS_COLOR)
            draw = ImageDraw.Draw(score_img)
            draw.text(
                draw_position,
                str(player.score),
                fill=constants.WHITE_COLOR,
                font=score_font,
                anchor="mm",
            )
            table_position = player.table_position
            for _ in range(table_position):
                score_img = score_img.transpose(Image.Transpose.ROTATE_90)
            composite.paste(score_img, score_positions[table_position], score_img)
        return composite

    def render_dora_indicators(self, game_state: GameState, composite: Image.Image) -> Image.Image:
        """
        Render the dora indicators at the top of the composite image.

        Args:
            game_state: The game state at any point where dora indicators are revealed.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        top_font = ImageFont.truetype(self.config.FONT_DIR, constants.TOP_FONT_SIZE)
        dora_indicators_size = (constants.DORA_INDICATORS_WIDTH, constants.TOP_INFO_HEIGHT)
        dora_indicators_img = Image.new(
            "RGBA", dora_indicators_size, color=constants.BACKGROUND_COLOR
        )
        draw = ImageDraw.Draw(dora_indicators_img)
        draw_x = constants.DORA_INDICATORS_X_TEXT
        draw_y = int(constants.TOP_INFO_HEIGHT / 2)
        draw.text(
            (draw_x, draw_y),
            "Dora indicators:",
            fill=constants.WHITE_COLOR,
            font=top_font,
            anchor="lm",
        )
        dora_indicators = game_state.dora_indicators
        for i in range(constants.DORA_INDICATORS_MAX):
            dora_indicator_x = constants.DORA_INDICATORS_X_TILES + constants.TILE_WIDTH * i
            dora_indicator_y = int((constants.TOP_INFO_HEIGHT - constants.TILE_HEIGHT) / 2)
            dora_indicator_pos = (dora_indicator_x, dora_indicator_y)
            if i < len(game_state.dora_indicators):
                dora_indicators_img.paste(
                    self.tile_imgs["Front"], dora_indicator_pos, self.tile_imgs["Front"]
                )
                dora_indicators_img.paste(
                    self.tile_imgs[dora_indicators[i]],
                    dora_indicator_pos,
                    self.tile_imgs[dora_indicators[i]],
                )
            else:
                dora_indicators_img.paste(
                    self.tile_imgs["Back"], dora_indicator_pos, self.tile_imgs["Back"]
                )
        composite.paste(dora_indicators_img, (0, 0), dora_indicators_img)
        return composite

    def render_kyotaku(self, game_state: GameState, composite: Image.Image) -> Image.Image:
        """
        Render the number of riichi bets at the top of the composite image.

        Args:
            game_state: The game state at any point where the number of riichi bets changes.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        top_font = ImageFont.truetype(self.config.FONT_DIR, constants.TOP_FONT_SIZE)
        kyotaku_size = (constants.KYOTAKU_WIDTH, constants.TOP_INFO_HEIGHT)
        kyotaku_img = Image.new("RGBA", kyotaku_size, color=constants.BACKGROUND_COLOR)
        draw = ImageDraw.Draw(kyotaku_img)
        draw_pos = (0, int(constants.TOP_INFO_HEIGHT / 2))
        draw.text(
            draw_pos,
            f"Riichi bets: {game_state.kyotaku}",
            fill=constants.WHITE_COLOR,
            font=top_font,
            anchor="lm",
        )
        composite.paste(kyotaku_img, (constants.KYOTAKU_X, 0), kyotaku_img)
        return composite

    def render_honba(self, game_state: GameState, composite: Image.Image) -> Image.Image:
        """
        Render the round repeats at the top of the composite image.

        Args:
            game_state: The game state the beginning of a round.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        top_font = ImageFont.truetype(self.config.FONT_DIR, constants.TOP_FONT_SIZE)
        honba_size = (constants.HONBA_WIDTH, constants.TOP_INFO_HEIGHT)
        honba_img = Image.new("RGBA", honba_size, color=constants.BACKGROUND_COLOR)
        draw = ImageDraw.Draw(honba_img)
        draw_pos = (0, int(constants.TOP_INFO_HEIGHT / 2))
        draw.text(
            draw_pos,
            f"Honba: {game_state.honba}",
            fill=constants.WHITE_COLOR,
            font=top_font,
            anchor="lm",
        )
        composite.paste(honba_img, (constants.HONBA_X, 0), honba_img)
        return composite

    def render_concealed_tiles(
        self, game_state: GameState, hand_img: Image.Image, actor_idx: int
    ) -> Image.Image:
        """
        Render one player's concealed tiles.

        Args:
            game_state: The game state at any point where an actor's hand is updated.
            hand_img: The image of the actor's hand.
            actor: The index of the actor whose hand needs to be updated.

        Returns:
            Image.Image: The updated hand image.
        """

        actor = game_state.players[actor_idx]
        concealed_tiles = actor.concealed_tiles
        hand_height = constants.HAND_HEIGHT
        tile_width = constants.TILE_WIDTH
        tile_height = constants.TILE_HEIGHT
        for i in range(len(concealed_tiles)):
            concealed_tile_pos = (tile_width * i, hand_height - tile_height)
            if actor.table_position == 0:
                hand_img.paste(self.tile_imgs["Front"], concealed_tile_pos, self.tile_imgs["Front"])
                hand_img.paste(
                    self.tile_imgs[concealed_tiles[i]],
                    concealed_tile_pos,
                    self.tile_imgs[concealed_tiles[i]],
                )
            else:
                hand_img.paste(self.tile_imgs["Back"], concealed_tile_pos, self.tile_imgs["Back"])
        return hand_img

    def render_drawn_tile(
        self, game_state: GameState, hand_img: Image.Image, actor_idx: int
    ) -> Image.Image:
        """
        Render one player's drawn tile.

        Args:
            game_state: The game state at any point where an actor's hand is updated.
            hand_img: The image of the actor's hand.
            actor: The index of the actor whose hand needs to be updated.

        Returns:
            Image.Image: The updated hand image.
        """

        actor = game_state.players[actor_idx]
        draw_offset = constants.DRAW_OFFSET
        hand_height = constants.HAND_HEIGHT
        tile_width = constants.TILE_WIDTH
        tile_height = constants.TILE_HEIGHT
        n_concealed = len(actor.concealed_tiles)
        if actor.drawn_tile:
            drawn_tile_pos = (tile_width * n_concealed + draw_offset, hand_height - tile_height)
            if actor.table_position == 0:
                hand_img.paste(self.tile_imgs["Front"], drawn_tile_pos, self.tile_imgs["Front"])
                hand_img.paste(
                    self.tile_imgs[actor.drawn_tile],
                    drawn_tile_pos,
                    self.tile_imgs[actor.drawn_tile],
                )
            else:
                hand_img.paste(self.tile_imgs["Back"], drawn_tile_pos, self.tile_imgs["Back"])
        return hand_img

    def render_revealed_tile(
        self, hand_img: Image.Image, x_curr: int, tile: str, tile_state: str
    ) -> tuple[Image.Image, int]:
        """
        Render an individual revealed tile at the appropriate position.

        Args:
            hand_img: The image of the actor's hand.
            x_curr: The x position of the left edge of the leftmost revealed tile
            tile: The tile that needs to be displayed as revealed
            tile_state: The manner in which the tile needs to be displayed.
                "vertical" if tile should be displayed vertically and face up.
                "horizontal" if the tile should be displayed rotated and face up.
                "back" if the tile should be displayed vertically and face down.
                "added" if the tile shoule be displayed rotated, face up, and on top of the previous tile.

        Returns:
            Image.Image: The updated hand image.
            int: The new left edge of the revealed tiles.
        """

        hand_height = constants.HAND_HEIGHT
        tile_height = constants.TILE_HEIGHT
        tile_width = constants.TILE_WIDTH
        match tile_state:
            case "vertical":
                tile_pos = (x_curr - tile_width, hand_height - tile_height)
                hand_img.paste(self.tile_imgs["Front"], tile_pos, self.tile_imgs["Front"])
                hand_img.paste(self.tile_imgs[tile], tile_pos, self.tile_imgs[tile])
                x_curr -= tile_width
            case "horizontal":
                rotated_face = self.tile_imgs[tile].transpose(Image.Transpose.ROTATE_90)
                rotated_front = self.tile_imgs["Front"].transpose(Image.Transpose.ROTATE_90)
                tile_pos = (x_curr - tile_height, hand_height - tile_width)
                hand_img.paste(rotated_front, tile_pos, rotated_front)
                hand_img.paste(rotated_face, tile_pos, rotated_face)
                x_curr -= tile_height
            case "back":
                tile_pos = (x_curr - tile_width, hand_height - tile_height)
                hand_img.paste(self.tile_imgs["Back"], tile_pos, self.tile_imgs["Back"])
                x_curr -= tile_width
            case "added":
                rotated_face = self.tile_imgs[tile].transpose(Image.Transpose.ROTATE_90)
                rotated_front = self.tile_imgs["Front"].transpose(Image.Transpose.ROTATE_90)
                tile_pos = (x_curr, hand_height - 2 * tile_width)
                hand_img.paste(rotated_front, tile_pos, rotated_front)
                hand_img.paste(rotated_face, tile_pos, rotated_face)
        return hand_img, x_curr

    def render_chi_pon(
        self, hand_img: Image.Image, actor: Player, x_curr: int, call_idx: int
    ) -> tuple[Image.Image, int]:
        """
        Render tiles in a chi or pon call.

        Args:
            hand_img: The image of the actor's hand.
            actor: The index of the actor whose hand needs to be updated.
            x_curr: The x position of the left edge of the leftmost revealed tile
            call_idx: The index of the relevant call among the actor's calls.

        Returns:
            Image.Image: The updated hand image.
            int: The new left edge of the revealed tiles.
        """

        call_tiles = actor.revealed_tiles[call_idx]
        call_taken = actor.taken[call_idx]
        for i in reversed(range(constants.CHI_TILES)):
            tile_state = "horizontal" if call_taken[i] else "vertical"
            hand_img, x_curr = self.render_revealed_tile(
                hand_img, x_curr, call_tiles[i], tile_state
            )
        return hand_img, x_curr

    def render_ankan(
        self, hand_img: Image.Image, actor: Player, x_curr: int, call_idx: int
    ) -> tuple[Image.Image, int]:
        """
        Render tiles in a closed kan call.

        Args:
            hand_img: The image of the actor's hand.
            actor: The index of the actor whose hand needs to be updated.
            x_curr: The x position of the left edge of the leftmost revealed tile
            call_idx: The index of the relevant call among the actor's calls.

        Returns:
            Image.Image: The updated hand image.
            int: The new left edge of the revealed tiles.
        """

        call_tiles = actor.revealed_tiles[call_idx]
        tile_states = ["back", "vertical", "vertical", "back"]
        for i in reversed(range(constants.KAN_TILES)):
            hand_img, x_curr = self.render_revealed_tile(
                hand_img, x_curr, call_tiles[i], tile_states[i]
            )
        return hand_img, x_curr

    def render_daiminkan(
        self, hand_img: Image.Image, actor: Player, x_curr: int, call_idx: int
    ) -> tuple[Image.Image, int]:
        """
        Render tiles in an added kan call.

        Args:
            hand_img: The image of the actor's hand.
            actor: The index of the actor whose hand needs to be updated.
            x_curr: The x position of the left edge of the leftmost revealed tile
            call_idx: The index of the relevant call among the actor's calls.

        Returns:
            Image.Image: The updated hand image.
            int: The new left edge of the revealed tiles.
        """

        call_tiles = actor.revealed_tiles[call_idx]
        call_taken = actor.taken[call_idx]
        for i in reversed(range(constants.KAN_TILES)):
            tile_state = "horizontal" if call_taken[i] else "vertical"
            hand_img, x_curr = self.render_revealed_tile(
                hand_img, x_curr, call_tiles[i], tile_state
            )
        return hand_img, x_curr

    def render_kakan(
        self, hand_img: Image.Image, actor: Player, x_curr: int, call_idx: int
    ) -> tuple[Image.Image, int]:
        """
        Render tiles in an open kan call.

        Args:
            hand_img: The image of the actor's hand.
            actor: The index of the actor whose hand needs to be updated.
            x_curr: The x position of the left edge of the leftmost revealed tile
            call_idx: The index of the relevant call among the actor's calls.

        Returns:
            Image.Image: The updated hand image.
            int: The new left edge of the revealed tiles.
        """

        call_tiles = actor.revealed_tiles[call_idx]
        tile_states = ["vertical"] * constants.KAN_TILES
        taken_idx = actor.taken[call_idx].index(True)
        tile_states[taken_idx] = "horizontal"
        tile_states[taken_idx - 1] = "added"
        for i in reversed(range(constants.KAN_TILES)):
            hand_img, x_curr = self.render_revealed_tile(
                hand_img, x_curr, call_tiles[i], tile_states[i]
            )
        return hand_img, x_curr

    def render_revealed_tiles(
        self, game_state: GameState, hand_img: Image.Image, actor_idx: int
    ) -> Image.Image:
        """
        Render tiles an actor has revealed through making calls.

        Args:
            game_state: The game state at a point where the actor's hand changes.
            hand_img: The image of the actor's hand.
            actor: The index of the actor whose hand needs to be updated.

        Returns:
            Image.Image: The updated hand image.
        """

        actor = game_state.players[actor_idx]
        x_curr = constants.HAND_WIDTH
        for call_idx in range(len(actor.calls)):
            match actor.calls[call_idx]:
                case "chi" | "pon":
                    hand_img, x_curr = self.render_chi_pon(hand_img, actor, x_curr, call_idx)
                case "ankan":
                    hand_img, x_curr = self.render_ankan(hand_img, actor, x_curr, call_idx)
                case "daiminkan":
                    hand_img, x_curr = self.render_daiminkan(hand_img, actor, x_curr, call_idx)
                case "kakan":
                    hand_img, x_curr = self.render_kakan(hand_img, actor, x_curr, call_idx)
        return hand_img

    def render_hand(self, game_state: GameState, composite: Image.Image, actor: int) -> Image.Image:
        """
        Render tiles that are part of an actor's hand.

        Args:
            game_state: The game state at a point where the actor's hand changes.
            composite: The composite image of the entire game.
            actor: The index of the actor whose hand needs to be updated.

        Returns:
            Image.Image: The updated composite image.
        """

        hand_width = constants.HAND_WIDTH
        hand_height = constants.HAND_HEIGHT
        hand_img = Image.new("RGBA", (hand_width, hand_height), color=constants.MAT_COLOR)
        hand_img = self.render_concealed_tiles(game_state, hand_img, actor)
        hand_img = self.render_drawn_tile(game_state, hand_img, actor)
        hand_img = self.render_revealed_tiles(game_state, hand_img, actor)

        table_position = game_state.players[actor].table_position
        for _ in range(table_position):
            hand_img = hand_img.transpose(Image.Transpose.ROTATE_90)
        frame_length = constants.FRAME_LENGTH
        frame_width = constants.FRAME_WIDTH
        hand_offset = constants.HAND_OFFSET
        top_info_height = constants.TOP_INFO_HEIGHT
        hand_positions = [
            (
                frame_width + hand_height + hand_offset,
                top_info_height + frame_length - frame_width - hand_height,
            ),
            (frame_length - frame_width - hand_height, top_info_height + frame_width),
            (frame_width, top_info_height + frame_width),
            (frame_width, top_info_height + frame_width + hand_height + hand_offset),
        ]
        composite.paste(hand_img, hand_positions[table_position], hand_img)
        return composite

    def render_discards(
        self, game_state: GameState, composite: Image.Image, actor_idx: int
    ) -> Image.Image:
        """
        Render an actor's discard pile.

        Args:
            game_state: The game state at a point where the actor's discards change.
            composite: The composite image of the entire game.
            actor: The index of the actor whose discards need to be updated.

        Returns:
            Image.Image: The updated composite image.
        """

        compass_length = constants.COMPASS_LENGTH
        discards_height = constants.DISCARDS_HEIGHT
        discards_img = Image.new(
            "RGBA", (compass_length, discards_height), color=constants.MAT_COLOR
        )

        # Display discarded tiles
        actor = game_state.players[actor_idx]
        discard_pile = actor.discard_pile
        tsumogiri = actor.tsumogiri
        discard_rotate = actor.discard_rotate
        n_discards = len(discard_pile)
        discard_position = (0, 0)
        for i in range(n_discards):
            discard_img = self.tile_imgs["Front"].copy()
            discard_face = self.tile_imgs[discard_pile[i]]
            discard_img.paste(discard_face, (0, 0), discard_face)
            if tsumogiri[i]:
                enhancer = ImageEnhance.Brightness(discard_img)
                discard_img = enhancer.enhance(constants.TSUMOGIRI_BRIGHTNESS)
            if not discard_rotate[i]:
                discards_img.paste(discard_img, discard_position, discard_img)
                discard_position = (discard_position[0] + constants.TILE_WIDTH, discard_position[1])
            else:
                discard_img = discard_img.transpose(Image.Transpose.ROTATE_90)
                offset = int((constants.TILE_HEIGHT - constants.TILE_WIDTH) / 2)
                discards_img.paste(
                    discard_img, (discard_position[0], discard_position[1] + offset), discard_img
                )
                discard_position = (
                    discard_position[0] + constants.TILE_HEIGHT,
                    discard_position[1],
                )
            if discard_position[0] > compass_length - constants.TILE_WIDTH:
                discard_position = (0, discard_position[1] + constants.TILE_HEIGHT)

        # Position the discards on the composite
        frame_length = constants.FRAME_LENGTH
        top_info_height = constants.TOP_INFO_HEIGHT
        table_position = actor.table_position
        for _ in range(table_position):
            discards_img = discards_img.transpose(Image.Transpose.ROTATE_90)
        discards_positions = [
            (
                int((frame_length - compass_length) / 2),
                top_info_height + int((frame_length + compass_length) / 2),
            ),
            (
                int((frame_length + compass_length) / 2),
                top_info_height + int((frame_length - compass_length) / 2),
            ),
            (
                int((frame_length - compass_length) / 2),
                top_info_height + int((frame_length - compass_length) / 2) - discards_height,
            ),
            (
                int((frame_length - compass_length) / 2) - discards_height,
                top_info_height + int((frame_length - compass_length) / 2),
            ),
        ]
        composite.paste(discards_img, discards_positions[table_position], discards_img)
        return composite

    def render_riichi_stick(
        self, game_state: GameState, composite: Image.Image, actor_idx: int
    ) -> Image.Image:
        """
        Render a riichi stick placed on the table.

        Args:
            game_state: The game state at a point where the actor declared riichi.
            composite: The composite image of the entire game.
            actor: The index of the actor whose riichi stick need to be placed.

        Returns:
            Image.Image: The updated composite image.
        """

        actor = game_state.players[actor_idx]
        riichi_stick_img = self.riichi_stick_img.copy()
        compass_length = constants.COMPASS_LENGTH
        frame_length = constants.FRAME_LENGTH
        top_info_height = constants.TOP_INFO_HEIGHT
        riichi_stick_length = constants.RIICHI_STICK_LENGTH
        riichi_stick_offset = constants.RIICHI_STICK_OFFSET
        riichi_stick_width = constants.RIICHI_STICK_WIDTH
        riichi_positions = [
            (
                int((frame_length - riichi_stick_length) / 2),
                top_info_height
                + int((frame_length + compass_length) / 2)
                - riichi_stick_width
                - riichi_stick_offset,
            ),
            (
                int((frame_length + compass_length) / 2) - riichi_stick_width - riichi_stick_offset,
                top_info_height + int((frame_length - riichi_stick_length) / 2),
            ),
            (
                int((frame_length - riichi_stick_length) / 2),
                top_info_height + int((frame_length - compass_length) / 2) + riichi_stick_offset,
            ),
            (
                int((frame_length - compass_length) / 2) + riichi_stick_offset,
                top_info_height + int((frame_length - riichi_stick_length) / 2),
            ),
        ]
        for _ in range(actor.table_position):
            riichi_stick_img = riichi_stick_img.transpose(Image.Transpose.ROTATE_90)
        composite.paste(riichi_stick_img, riichi_positions[actor.table_position], riichi_stick_img)
        return composite

    def start_kyoku(
        self, event: Dict[str, Any], game_state: GameState, composite: Image.Image
    ) -> Image.Image:
        """
        Update the composite to address a "start_kyoku" event.

        Args:
            event: The log line for a "start_kyoku" event.
            game_state: The game state immediately after this event has been simulated.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        composite = self.background_img.copy()
        composite = self.render_compass(game_state, composite)
        composite = self.render_round_name(game_state, composite)
        composite = self.render_tile_count(game_state, composite)
        composite = self.render_scores(game_state, composite)
        composite = self.render_dora_indicators(game_state, composite)
        composite = self.render_kyotaku(game_state, composite)
        composite = self.render_honba(game_state, composite)
        for i in range(constants.NUM_PLAYERS):
            self.render_hand(game_state, composite, i)
        return composite

    def tsumo(
        self, event: Dict[str, Any], game_state: GameState, composite: Image.Image
    ) -> Image.Image:
        """
        Update the composite to address a "tsumo" event.

        Args:
            event: The log line for a "tsumo" event.
            game_state: The game state immediately after this event has been simulated.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        composite = self.render_hand(game_state, composite, event["actor"])
        composite = self.render_tile_count(game_state, composite)
        return composite

    def dahai(
        self, event: Dict[str, Any], game_state: GameState, composite: Image.Image
    ) -> Image.Image:
        """
        Update the composite to address a "dahai" event.

        Args:
            event: The log line for a "dahai" event.
            game_state: The game state immediately after this event has been simulated.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        composite = self.render_hand(game_state, composite, event["actor"])
        composite = self.render_discards(game_state, composite, event["actor"])
        return composite

    def reach(
        self, event: Dict[str, Any], game_state: GameState, composite: Image.Image
    ) -> Image.Image:
        """
        Update the composite to address a "reach" event.

        Args:
            event: The log line for a "reach" event.
            game_state: The game state immediately after this event has been simulated.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        return composite

    def reach_accepted(
        self, event: Dict[str, Any], game_state: GameState, composite: Image.Image
    ) -> Image.Image:
        """
        Update the composite to address a "reach_accepted" event.

        Args:
            event: The log line for a "reach_accepted" event.
            game_state: The game state immediately after this event has been simulated.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        composite = self.render_riichi_stick(game_state, composite, event["actor"])
        composite = self.render_scores(game_state, composite)
        composite = self.render_kyotaku(game_state, composite)
        return composite

    def chi(
        self, event: Dict[str, Any], game_state: GameState, composite: Image.Image
    ) -> Image.Image:
        """
        Update the composite to address a "chi" event.

        Args:
            event: The log line for a "chi" event.
            game_state: The game state immediately after this event has been simulated.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        composite = self.render_discards(game_state, composite, event["target"])
        composite = self.render_hand(game_state, composite, event["actor"])
        return composite

    def pon(
        self, event: Dict[str, Any], game_state: GameState, composite: Image.Image
    ) -> Image.Image:
        """
        Update the composite to address a "pon" event.

        Args:
            event: The log line for a "pon" event.
            game_state: The game state immediately after this event has been simulated.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        composite = self.render_discards(game_state, composite, event["target"])
        composite = self.render_hand(game_state, composite, event["actor"])
        return composite

    def ankan(
        self, event: Dict[str, Any], game_state: GameState, composite: Image.Image
    ) -> Image.Image:
        """
        Update the composite to address an "ankan" event.

        Args:
            event: The log line for an "ankan" event.
            game_state: The game state immediately after this event has been simulated.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        composite = self.render_hand(game_state, composite, event["actor"])
        return composite

    def kakan(
        self, event: Dict[str, Any], game_state: GameState, composite: Image.Image
    ) -> Image.Image:
        """
        Update the composite to address a "kakan" event.

        Args:
            event: The log line for a "kakan" event.
            game_state: The game state immediately after this event has been simulated.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        composite = self.render_hand(game_state, composite, event["actor"])
        return composite

    def daiminkan(
        self, event: Dict[str, Any], game_state: GameState, composite: Image.Image
    ) -> Image.Image:
        """
        Update the composite to address a "daiminkan" event.

        Args:
            event: The log line for a "daiminkan" event.
            game_state: The game state immediately after this event has been simulated.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        composite = self.render_discards(game_state, composite, event["target"])
        composite = self.render_hand(game_state, composite, event["actor"])
        return composite

    def dora(
        self, event: Dict[str, Any], game_state: GameState, composite: Image.Image
    ) -> Image.Image:
        """
        Update the composite to address a "dora" event.

        Args:
            event: The log line for a "dora" event.
            game_state: The game state immediately after this event has been simulated.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        composite = self.render_dora_indicators(game_state, composite)
        return composite

    def hora(
        self, event: Dict[str, Any], game_state: GameState, composite: Image.Image
    ) -> Image.Image:
        """
        Update the composite to address an "hora" event.

        Args:
            event: The log line for an "hora" event.
            game_state: The game state immediately after this event has been simulated.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        return composite

    def ryukyoku(
        self, event: Dict[str, Any], game_state: GameState, composite: Image.Image
    ) -> Image.Image:
        """
        Update the composite to address a "ryukyoku" event.

        Args:
            event: The log line for a "ryukyoku" event.
            game_state: The game state immediately after this event has been simulated.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        return composite

    def end_kyoku(
        self, event: Dict[str, Any], game_state: GameState, composite: Image.Image
    ) -> Image.Image:
        """
        Update the composite to address an "end_kyoku" event.

        Args:
            event: The log line for an "end_kyoku" event.
            game_state: The game state immediately after this event has been simulated.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        return composite

    def end_game(
        self, event: Dict[str, Any], game_state: GameState, composite: Image.Image
    ) -> Image.Image:
        """
        Update the composite to address an "end_game" event.

        Args:
            event: The log line for an "end_game" event.
            game_state: The game state immediately after this event has been simulated.
            composite: The composite image of the entire game.

        Returns:
            Image.Image: The updated composite image.
        """

        return composite


def render_event(
    event: Dict[str, Any],
    game_state: GameState,
    composite: Image.Image,
    renderer_instance: Renderer,
) -> Any:
    """
    Update the composite image to show a new event of any allowable type.

    Args:
        event: The log line of the event to be displayed.
        game_state: The game state immediately after the event has been simulated.
        composite: The composite image immediately prior to the event.
        renderer_instance: The renderer used to updated the composite.

    Returns:
        Image.Image: The updated composite image accounting for the new event.
    """

    event_type = event["type"]
    return getattr(renderer_instance, event_type)(event, game_state, composite)
