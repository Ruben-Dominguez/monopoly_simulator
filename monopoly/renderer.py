"""
Monopoly GUI Renderer.
Draws the classic Monopoly game board, properties, tokens, dice, and houses using Pygame.
"""

import pygame
import math
from typing import Dict, List, Tuple, Optional
from .models import BoardSpace, PropertyState, Player, DiceRoll, SpaceType, Bank
from .board_data import COLOR_RGB_MAP

BOARD_SIZE = 720
CORNER_SIZE = 90
TILE_WIDTH = 60  # (720 - 2 * 90) / 9 = 60

# Palette
BG_COLOR = (240, 242, 235)
BOARD_BORDER = (30, 30, 30)
TILE_BG = (248, 249, 246)
TEXT_COLOR = (20, 20, 20)
SUBTEXT_COLOR = (90, 90, 90)
HOUSE_GREEN = (34, 139, 34)
HOTEL_RED = (200, 30, 30)
MORTGAGE_OVERLAY = (180, 180, 180, 190)

class BoardRenderer:
    def __init__(self, surface: pygame.Surface, x_offset: int = 15, y_offset: int = 15):
        self.surface = surface
        self.ox = x_offset
        self.oy = y_offset
        self.tile_rects: Dict[int, pygame.Rect] = {}
        self._calculate_tile_rects()

        # Fonts
        pygame.font.init()
        self.font_title = pygame.font.SysFont("arial", 11, bold=True)
        self.font_sub = pygame.font.SysFont("arial", 9)
        self.font_corner = pygame.font.SysFont("arial", 12, bold=True)
        self.font_token = pygame.font.SysFont("arial", 9, bold=True)
        self.font_dice = pygame.font.SysFont("arial", 22, bold=True)
        self.font_dice_label = pygame.font.SysFont("arial", 12, bold=True)

    def _calculate_tile_rects(self):
        # 0: GO (bottom-right)
        self.tile_rects[0] = pygame.Rect(self.ox + BOARD_SIZE - CORNER_SIZE, self.oy + BOARD_SIZE - CORNER_SIZE, CORNER_SIZE, CORNER_SIZE)

        # 1-9: Bottom row (right to left)
        for i in range(1, 10):
            rx = self.ox + BOARD_SIZE - CORNER_SIZE - i * TILE_WIDTH
            ry = self.oy + BOARD_SIZE - CORNER_SIZE
            self.tile_rects[i] = pygame.Rect(rx, ry, TILE_WIDTH, CORNER_SIZE)

        # 10: Jail (bottom-left)
        self.tile_rects[10] = pygame.Rect(self.ox, self.oy + BOARD_SIZE - CORNER_SIZE, CORNER_SIZE, CORNER_SIZE)

        # 11-19: Left row (bottom to top)
        for i in range(11, 20):
            offset_idx = i - 10
            rx = self.ox
            ry = self.oy + BOARD_SIZE - CORNER_SIZE - offset_idx * TILE_WIDTH
            self.tile_rects[i] = pygame.Rect(rx, ry, CORNER_SIZE, TILE_WIDTH)

        # 20: Free Parking (top-left)
        self.tile_rects[20] = pygame.Rect(self.ox, self.oy, CORNER_SIZE, CORNER_SIZE)

        # 21-29: Top row (left to right)
        for i in range(21, 30):
            offset_idx = i - 20
            rx = self.ox + CORNER_SIZE + (offset_idx - 1) * TILE_WIDTH
            ry = self.oy
            self.tile_rects[i] = pygame.Rect(rx, ry, TILE_WIDTH, CORNER_SIZE)

        # 30: Go to Jail (top-right)
        self.tile_rects[30] = pygame.Rect(self.ox + BOARD_SIZE - CORNER_SIZE, self.oy, CORNER_SIZE, CORNER_SIZE)

        # 31-39: Right row (top to bottom)
        for i in range(31, 40):
            offset_idx = i - 30
            rx = self.ox + BOARD_SIZE - CORNER_SIZE
            ry = self.oy + CORNER_SIZE + (offset_idx - 1) * TILE_WIDTH
            self.tile_rects[i] = pygame.Rect(rx, ry, CORNER_SIZE, TILE_WIDTH)

    def draw_board(self, board: List[BoardSpace], properties: Dict[int, PropertyState]):
        # Background board area
        full_board_rect = pygame.Rect(self.ox, self.oy, BOARD_SIZE, BOARD_SIZE)
        pygame.draw.rect(self.surface, BG_COLOR, full_board_rect)
        pygame.draw.rect(self.surface, BOARD_BORDER, full_board_rect, 3)

        # Center logo / background
        center_rect = pygame.Rect(self.ox + CORNER_SIZE, self.oy + CORNER_SIZE, BOARD_SIZE - 2 * CORNER_SIZE, BOARD_SIZE - 2 * CORNER_SIZE)
        pygame.draw.rect(self.surface, (230, 238, 232), center_rect)

        # Draw each tile
        for space in board:
            rect = self.tile_rects[space.index]
            pygame.draw.rect(self.surface, TILE_BG, rect)
            pygame.draw.rect(self.surface, BOARD_BORDER, rect, 1)

            prop = properties.get(space.index)
            self._draw_space_content(space, prop, rect)

    def _draw_space_content(self, space: BoardSpace, prop: Optional[PropertyState], rect: pygame.Rect):
        idx = space.index
        # Corner spaces
        if space.space_type == SpaceType.CORNER:
            self._draw_corner(space, rect)
            return

        # Properties with color bar
        if prop and prop.space_type == SpaceType.PROPERTY:
            bar_color = COLOR_RGB_MAP.get(prop.group, (100, 100, 100))
            bar_thick = 16

            if 1 <= idx <= 9:  # Bottom: bar at top
                bar_rect = pygame.Rect(rect.x, rect.y, rect.width, bar_thick)
                pygame.draw.rect(self.surface, bar_color, bar_rect)
                pygame.draw.rect(self.surface, BOARD_BORDER, bar_rect, 1)
                self._draw_houses(prop, bar_rect)
            elif 11 <= idx <= 19:  # Left: bar at right
                bar_rect = pygame.Rect(rect.right - bar_thick, rect.y, bar_thick, rect.height)
                pygame.draw.rect(self.surface, bar_color, bar_rect)
                pygame.draw.rect(self.surface, BOARD_BORDER, bar_rect, 1)
                self._draw_houses(prop, bar_rect)
            elif 21 <= idx <= 29:  # Top: bar at bottom
                bar_rect = pygame.Rect(rect.x, rect.bottom - bar_thick, rect.width, bar_thick)
                pygame.draw.rect(self.surface, bar_color, bar_rect)
                pygame.draw.rect(self.surface, BOARD_BORDER, bar_rect, 1)
                self._draw_houses(prop, bar_rect)
            elif 31 <= idx <= 39:  # Right: bar at left
                bar_rect = pygame.Rect(rect.x, rect.y, bar_thick, rect.height)
                pygame.draw.rect(self.surface, bar_color, bar_rect)
                pygame.draw.rect(self.surface, BOARD_BORDER, bar_rect, 1)
                self._draw_houses(prop, bar_rect)

        # Draw Names and Prices
        name_words = space.name.split(" ")
        short_name = name_words[0] if len(name_words) == 1 else f"{name_words[0]} {name_words[1][:4]}."
        if len(name_words) > 1 and name_words[0] in ("St.", "North", "South", "New", "Park"):
            short_name = f"{name_words[0]} {name_words[1]}"

        text_surf = self.font_title.render(short_name, True, TEXT_COLOR)
        # Center text inside tile
        tx = rect.centerx - text_surf.get_width() // 2
        ty = rect.centery - text_surf.get_height() // 2
        self.surface.blit(text_surf, (tx, ty - 6))

        # Price / Rent label
        price_str = ""
        if prop:
            price_str = f"${prop.price}"
        elif space.space_type == SpaceType.TAX:
            price_str = f"${space.tax_amount}" if space.tax_amount > 0 else "10% or $200"
        elif space.space_type == SpaceType.CHANCE:
            price_str = "?"
        elif space.space_type == SpaceType.COMMUNITY_CHEST:
            price_str = "CHEST"

        if price_str:
            sub_surf = self.font_sub.render(price_str, True, SUBTEXT_COLOR)
            self.surface.blit(sub_surf, (rect.centerx - sub_surf.get_width() // 2, ty + 10))

        # Mortgaged overlay
        if prop and prop.is_mortgaged:
            m_surf = self.font_title.render("MORTGAGED", True, (180, 0, 0))
            self.surface.blit(m_surf, (rect.centerx - m_surf.get_width() // 2, rect.centery + 18))

    def _draw_corner(self, space: BoardSpace, rect: pygame.Rect):
        idx = space.index
        c_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        if idx == 0:
            lbl = "COLLECT $200"
            sub = "<- GO"
            color = (200, 240, 200)
        elif idx == 10:
            lbl = "IN JAIL"
            sub = "VISITING"
            color = (250, 200, 160)
        elif idx == 20:
            lbl = "FREE"
            sub = "PARKING"
            color = (255, 240, 180)
        else:
            lbl = "GO TO"
            sub = "JAIL!"
            color = (250, 180, 180)

        pygame.draw.rect(self.surface, color, rect)
        pygame.draw.rect(self.surface, BOARD_BORDER, rect, 1)

        t1 = self.font_corner.render(lbl, True, TEXT_COLOR)
        t2 = self.font_corner.render(sub, True, (160, 20, 20) if idx == 30 else TEXT_COLOR)
        self.surface.blit(t1, (rect.centerx - t1.get_width() // 2, rect.centery - 14))
        self.surface.blit(t2, (rect.centerx - t2.get_width() // 2, rect.centery + 4))

    def _draw_houses(self, prop: PropertyState, bar_rect: pygame.Rect):
        if prop.houses == 0:
            return
        if prop.houses == 5:
            # Hotel: Red rectangle
            h_rect = pygame.Rect(bar_rect.centerx - 10, bar_rect.centery - 5, 20, 10)
            pygame.draw.rect(self.surface, HOTEL_RED, h_rect)
            pygame.draw.rect(self.surface, (255, 255, 255), h_rect, 1)
        else:
            # 1 to 4 houses: small green squares
            h_count = prop.houses
            box_size = 8
            gap = 3
            total_w = h_count * box_size + (h_count - 1) * gap
            start_x = bar_rect.centerx - total_w // 2
            for i in range(h_count):
                bx = start_x + i * (box_size + gap)
                by = bar_rect.centery - box_size // 2
                h_rect = pygame.Rect(bx, by, box_size, box_size)
                pygame.draw.rect(self.surface, HOUSE_GREEN, h_rect)
                pygame.draw.rect(self.surface, (255, 255, 255), h_rect, 1)

    def draw_tokens(self, players: List[Player]):
        # Group players by space
        players_by_pos: Dict[int, List[Player]] = {}
        for p in players:
            if not p.is_bankrupt:
                players_by_pos.setdefault(p.position, []).append(p)

        radius = 11
        for pos, plist in players_by_pos.items():
            rect = self.tile_rects[pos]
            cx, cy = rect.centerx, rect.centery
            n = len(plist)

            for i, p in enumerate(plist):
                if n == 1:
                    px, py = cx, cy
                else:
                    # Arrange in a mini circle
                    angle = (2 * math.pi / n) * i
                    dist = 18
                    px = cx + int(dist * math.cos(angle))
                    py = cy + int(dist * math.sin(angle))

                # Draw token circle
                pygame.draw.circle(self.surface, (30, 30, 30), (px, py), radius + 2)
                pygame.draw.circle(self.surface, p.color, (px, py), radius)
                # Player initial
                init_str = p.name[:2].upper()
                t_surf = self.font_token.render(init_str, True, (255, 255, 255))
                self.surface.blit(t_surf, (px - t_surf.get_width() // 2, py - t_surf.get_height() // 2))

    def draw_center_area(
        self,
        current_player: Player,
        last_roll: Optional[DiceRoll],
        bank: Bank,
        use_speed_die: bool,
        round_num: int,
        turn_num: int
    ):
        cx = self.ox + BOARD_SIZE // 2
        cy = self.oy + BOARD_SIZE // 2

        # Title
        title_font = pygame.font.SysFont("arial", 26, bold=True)
        title_surf = title_font.render("MONOPOLY", True, (180, 20, 20))
        self.surface.blit(title_surf, (cx - title_surf.get_width() // 2, cy - 140))

        mode_font = pygame.font.SysFont("arial", 12, italic=True)
        mode_text = "Speed Die Edition" if use_speed_die else "Official Hasbro Classic"
        mode_surf = mode_font.render(mode_text, True, (80, 80, 80))
        self.surface.blit(mode_surf, (cx - mode_surf.get_width() // 2, cy - 110))

        # Current turn banner
        banner_rect = pygame.Rect(cx - 160, cy - 90, 320, 34)
        pygame.draw.rect(self.surface, (255, 255, 255), banner_rect, border_radius=6)
        pygame.draw.rect(self.surface, current_player.color, banner_rect, 3, border_radius=6)
        
        turn_str = f"Turn: {current_player.name} ({'CPU' if current_player.is_cpu else 'HUMAN'})"
        turn_surf = pygame.font.SysFont("arial", 14, bold=True).render(turn_str, True, (20, 20, 20))
        self.surface.blit(turn_surf, (cx - turn_surf.get_width() // 2, cy - 82))

        # Dice Display
        dice_y = cy - 40
        if last_roll:
            self._draw_die(cx - 65, dice_y, str(last_roll.die1), (255, 255, 255), (0, 0, 0))
            self._draw_die(cx - 10, dice_y, str(last_roll.die2), (255, 255, 255), (0, 0, 0))
            if last_roll.speed_die is not None:
                # Speed die (red die)
                sd_str = str(last_roll.speed_die)
                if last_roll.speed_die == "bus":
                    sd_str = "BUS"
                elif last_roll.speed_die == "mr_monopoly":
                    sd_str = "MR.M"
                self._draw_die(cx + 45, dice_y, sd_str, (210, 40, 40), (255, 255, 255), width=48)
        else:
            # Placeholder dice
            self._draw_die(cx - 45, dice_y, "?", (240, 240, 240), (100, 100, 100))
            self._draw_die(cx + 5, dice_y, "?", (240, 240, 240), (100, 100, 100))

        # Bank Inventory
        bank_font = pygame.font.SysFont("arial", 12)
        bank_text = f"Bank Reserves: Houses {bank.houses}/32  |  Hotels {bank.hotels}/12"
        bank_surf = bank_font.render(bank_text, True, (60, 60, 60))
        self.surface.blit(bank_surf, (cx - bank_surf.get_width() // 2, cy + 25))

        round_text = f"Round {round_num}  |  Total Turns: {turn_num}"
        round_surf = bank_font.render(round_text, True, (100, 100, 100))
        self.surface.blit(round_surf, (cx - round_surf.get_width() // 2, cy + 45))

    def _draw_die(self, x: int, y: int, label: str, bg_color: Tuple[int, int, int], text_color: Tuple[int, int, int], width: int = 40):
        die_rect = pygame.Rect(x, y, width, 40)
        pygame.draw.rect(self.surface, bg_color, die_rect, border_radius=6)
        pygame.draw.rect(self.surface, (40, 40, 40), die_rect, 2, border_radius=6)
        font = self.font_dice_label if len(label) > 1 else self.font_dice
        txt = font.render(label, True, text_color)
        self.surface.blit(txt, (die_rect.centerx - txt.get_width() // 2, die_rect.centery - txt.get_height() // 2))
