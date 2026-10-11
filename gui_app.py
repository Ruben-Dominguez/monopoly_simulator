"""
Monopoly Simulator GUI Application.
Features:
- Game Setup Screen: Configure 1-6 players (Human or CPU), names, tokens, Classic vs Speed Die.
- In-Game Visual Board with Pygame.
- Speed controls with dedicated buttons (Pause, 1x, 2x, 5x, 20x, MAX, Step).
- Interactive modals for Buying, Banker Auctions, Property Management (Build/Mortgage), Taxes, Jail, and Bus die.
- Real-time Activity Log and Player HUD.
"""

import sys
import pygame
import time
from typing import List, Dict, Any, Optional, Tuple
from monopoly.game import MonopolyGame
from monopoly.models import Player, GamePhase, PropertyState, SpaceType
from monopoly.renderer import BoardRenderer, BOARD_SIZE
from monopoly.rules import RulesEngine
from monopoly.board_data import COLOR_GROUPS, COLOR_RGB_MAP

SCREEN_WIDTH = 1260
SCREEN_HEIGHT = 750
SIDEBAR_X = 750
SIDEBAR_WIDTH = SCREEN_WIDTH - SIDEBAR_X - 15

# Color Theme
BG_DARK = (24, 28, 36)
PANEL_BG = (35, 41, 54)
PANEL_BORDER = (55, 65, 81)
TEXT_WHITE = (240, 243, 246)
TEXT_MUTED = (156, 163, 175)
BTN_PRIMARY = (37, 99, 235)
BTN_PRIMARY_HOVER = (59, 130, 246)
BTN_SUCCESS = (16, 185, 129)
BTN_SUCCESS_HOVER = (52, 211, 153)
BTN_DANGER = (239, 68, 68)
BTN_WARNING = (245, 158, 11)
BTN_ACCENT = (139, 92, 246)

SPEED_SETTINGS = [
    ("PAUSE", None),
    ("1x", 1.0),
    ("2x", 0.4),
    ("5x", 0.15),
    ("20x", 0.04),
    ("MAX", 0.001),
]

PLAYER_PALETTES = [
    {"name": "Red Racer", "color": (230, 57, 70), "token": "Car"},
    {"name": "Blue Sailor", "color": (69, 123, 157), "token": "Battleship"},
    {"name": "Green Tycoon", "color": (42, 157, 143), "token": "Top Hat"},
    {"name": "Yellow Banker", "color": (233, 196, 106), "token": "Thimble"},
    {"name": "Purple Baron", "color": (155, 93, 229), "token": "Boot"},
    {"name": "Orange Trader", "color": (244, 162, 97), "token": "Scottie"},
]

class Button:
    def __init__(self, rect: pygame.Rect, text: str, bg_color=BTN_PRIMARY, hover_color=BTN_PRIMARY_HOVER, text_color=TEXT_WHITE, font_size=13):
        self.rect = rect
        self.text = text
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = pygame.font.SysFont("arial", font_size, bold=True)
        self.is_hovered = False

    def draw(self, surface: pygame.Surface):
        color = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (255, 255, 255, 40), self.rect, 1, border_radius=5)
        
        t_surf = self.font.render(self.text, True, self.text_color)
        surface.blit(t_surf, (self.rect.centerx - t_surf.get_width() // 2, self.rect.centery - t_surf.get_height() // 2))

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class MonopolyApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Monopoly Simulator - Hasbro Official Rules")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.renderer = BoardRenderer(self.screen, x_offset=15, y_offset=15)
        self.font_main = pygame.font.SysFont("arial", 13)
        self.font_bold = pygame.font.SysFont("arial", 13, bold=True)
        self.font_title = pygame.font.SysFont("arial", 20, bold=True)
        self.font_log = pygame.font.SysFont("arial", 11)

        # App state
        self.in_setup = True
        self.in_manage_modal = False
        self.selected_manage_prop_idx: Optional[int] = None
        self.game: Optional[MonopolyGame] = None

        # Setup configuration
        self.setup_player_count = 4
        self.setup_players: List[Dict[str, Any]] = []
        self.setup_use_speed_die = False
        self._init_setup_data()

        # Simulation speed controls
        self.current_speed_idx = 1  # Default 1x
        self.last_step_time = time.time()

        # UI Control buttons
        self.speed_buttons: List[Button] = []
        self._create_speed_buttons()

    def _init_setup_data(self):
        self.setup_players = []
        for i in range(6):
            palette = PLAYER_PALETTES[i]
            self.setup_players.append({
                "name": palette["name"],
                "is_cpu": (i > 0),  # Player 1 is Human, rest CPU by default
                "color": palette["color"],
                "token_name": palette["token"]
            })

    def _create_speed_buttons(self):
        self.speed_buttons = []
        btn_y = 695
        bx = 20
        bw = 65
        bh = 28
        for i, (label, _) in enumerate(SPEED_SETTINGS):
            btn = Button(pygame.Rect(bx + i * (bw + 6), btn_y, bw, bh), label, font_size=11)
            self.speed_buttons.append(btn)
        
        # Add Step button
        self.step_btn = Button(pygame.Rect(bx + len(SPEED_SETTINGS) * (bw + 6), btn_y, bw, bh), "STEP", bg_color=BTN_ACCENT, font_size=11)

    def start_game(self):
        configs = self.setup_players[:self.setup_player_count]
        self.game = MonopolyGame(configs, use_speed_die=self.setup_use_speed_die)
        self.in_setup = False

    # ---------------- Main Event & Update Loop ---------------- #

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()

            if not self.in_setup and self.game:
                self.update_simulation()

            self.render()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if self.in_setup:
                self._handle_setup_event(event)
            elif self.in_manage_modal:
                self._handle_manage_modal_event(event)
            else:
                self._handle_game_event(event)

    def update_simulation(self):
        if not self.game or self.game.phase == GamePhase.GAME_OVER:
            return

        now = time.time()
        speed_delay = SPEED_SETTINGS[self.current_speed_idx][1]

        # If Paused, do not auto step
        if speed_delay is None:
            return

        # Check if enough time has passed
        if now - self.last_step_time >= speed_delay:
            self.last_step_time = now
            self._step_game_loop()

    def _step_game_loop(self):
        if not self.game or self.game.phase == GamePhase.GAME_OVER:
            return

        # If auction in progress
        if self.game.phase == GamePhase.AUCTION_IN_PROGRESS:
            bidder = self.game.pending_auction.current_bidder
            if bidder and bidder.is_cpu:
                self.game.step_auction()
            return

        # Current player
        curr = self.game.current_player
        if curr.is_cpu:
            self.game.step_cpu()

    # ---------------- Setup Screen ---------------- #

    def _handle_setup_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Player Count Buttons (1 to 6)
            for cnt in range(1, 7):
                r = pygame.Rect(350 + (cnt - 1) * 70, 160, 55, 35)
                if r.collidepoint(mx, my):
                    self.setup_player_count = cnt

            # Human vs CPU toggle buttons
            for i in range(self.setup_player_count):
                toggle_rect = pygame.Rect(650, 240 + i * 50, 100, 30)
                if toggle_rect.collidepoint(mx, my):
                    self.setup_players[i]["is_cpu"] = not self.setup_players[i]["is_cpu"]

            # Rules Mode Toggle
            mode_rect = pygame.Rect(450, 560, 220, 35)
            if mode_rect.collidepoint(mx, my):
                self.setup_use_speed_die = not self.setup_use_speed_die

            # Start Button
            start_rect = pygame.Rect(500, 630, 220, 50)
            if start_rect.collidepoint(mx, my):
                self.start_game()

    def _render_setup_screen(self):
        self.screen.fill(BG_DARK)

        # Title
        t_surf = pygame.font.SysFont("arial", 32, bold=True).render("MONOPOLY SIMULATOR", True, TEXT_WHITE)
        self.screen.blit(t_surf, (SCREEN_WIDTH // 2 - t_surf.get_width() // 2, 40))

        sub_surf = pygame.font.SysFont("arial", 14).render("Official Hasbro Rules Engine & Speed Die Simulator", True, TEXT_MUTED)
        self.screen.blit(sub_surf, (SCREEN_WIDTH // 2 - sub_surf.get_width() // 2, 85))

        # Box for configuration
        cfg_rect = pygame.Rect(200, 120, 840, 560)
        pygame.draw.rect(self.screen, PANEL_BG, cfg_rect, border_radius=10)
        pygame.draw.rect(self.screen, PANEL_BORDER, cfg_rect, 2, border_radius=10)

        # Player count selector
        lbl = self.font_bold.render("Select Number of Players (1 - 6):", True, TEXT_WHITE)
        self.screen.blit(lbl, (240, 168))
        for cnt in range(1, 7):
            r = pygame.Rect(520 + (cnt - 1) * 60, 160, 50, 35)
            is_sel = (self.setup_player_count == cnt)
            color = BTN_PRIMARY if is_sel else (50, 55, 70)
            pygame.draw.rect(self.screen, color, r, border_radius=6)
            c_text = self.font_bold.render(str(cnt), True, TEXT_WHITE)
            self.screen.blit(c_text, (r.centerx - c_text.get_width() // 2, r.centery - c_text.get_height() // 2))

        # Player Roster table
        headers = ["#", "Name", "Token", "Control Type"]
        hx = [240, 280, 480, 650]
        for h, x in zip(headers, hx):
            self.screen.blit(self.font_bold.render(h, True, TEXT_MUTED), (x, 215))

        for i in range(self.setup_player_count):
            pdata = self.setup_players[i]
            py = 245 + i * 48

            # Circle color
            pygame.draw.circle(self.screen, pdata["color"], (hx[0] + 8, py + 12), 9)

            # Name
            name_surf = self.font_main.render(pdata["name"], True, TEXT_WHITE)
            self.screen.blit(name_surf, (hx[1], py + 5))

            # Token
            token_surf = self.font_main.render(pdata["token_name"], True, TEXT_MUTED)
            self.screen.blit(token_surf, (hx[2], py + 5))

            # Control Toggle
            toggle_rect = pygame.Rect(hx[3], py, 110, 30)
            is_cpu = pdata["is_cpu"]
            color = BTN_WARNING if is_cpu else BTN_SUCCESS
            pygame.draw.rect(self.screen, color, toggle_rect, border_radius=5)
            t_str = "CPU BOT" if is_cpu else "HUMAN"
            t_surf = self.font_bold.render(t_str, True, (0, 0, 0) if is_cpu else TEXT_WHITE)
            self.screen.blit(t_surf, (toggle_rect.centerx - t_surf.get_width() // 2, toggle_rect.centery - t_surf.get_height() // 2))

        # Rules Mode Selector
        mode_rect = pygame.Rect(380, 550, 480, 40)
        pygame.draw.rect(self.screen, (45, 52, 68), mode_rect, border_radius=6)
        mode_title = f"Game Mode: {'⚡ Speed Die Rules ($2500 Cash, Triples, Bus, Mr. Monopoly)' if self.setup_use_speed_die else '📜 Classic Hasbro Rules ($1500 Starting Cash)'}"
        m_surf = self.font_bold.render(mode_title, True, (255, 215, 0) if self.setup_use_speed_die else TEXT_WHITE)
        self.screen.blit(m_surf, (mode_rect.centerx - m_surf.get_width() // 2, mode_rect.centery - m_surf.get_height() // 2))

        # Start Button
        start_rect = pygame.Rect(510, 615, 220, 48)
        pygame.draw.rect(self.screen, BTN_SUCCESS, start_rect, border_radius=8)
        s_surf = pygame.font.SysFont("arial", 18, bold=True).render("START GAME", True, TEXT_WHITE)
        self.screen.blit(s_surf, (start_rect.centerx - s_surf.get_width() // 2, start_rect.centery - s_surf.get_height() // 2))

    # ---------------- In-Game Events & HUD ---------------- #

    def _handle_game_event(self, event: pygame.event.Event):
        # Handle speed buttons
        for i, btn in enumerate(self.speed_buttons):
            if btn.handle_event(event):
                self.current_speed_idx = i
                return

        # Handle Step button
        if self.step_btn.handle_event(event):
            self.game.step_cpu()
            return

        if not self.game:
            return

        p = self.game.current_player

        # Interaction buttons on sidebar
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Manage Properties Button (always available for human)
            manage_rect = pygame.Rect(SIDEBAR_X + 240, 410, 190, 36)
            if manage_rect.collidepoint(mx, my):
                self.in_manage_modal = True
                self.selected_manage_prop_idx = p.properties[0] if p.properties else None
                return

            # Human turn actions
            if not p.is_cpu:
                # 1. Roll Dice Button
                if self.game.phase == GamePhase.WAITING_FOR_ROLL:
                    roll_rect = pygame.Rect(SIDEBAR_X + 20, 410, 200, 36)
                    if roll_rect.collidepoint(mx, my):
                        self.game.execute_roll()
                        return

                # 2. Buy vs Auction buttons
                elif self.game.phase == GamePhase.BUY_OR_AUCTION_DECISION:
                    buy_rect = pygame.Rect(SIDEBAR_X + 20, 410, 190, 36)
                    auction_rect = pygame.Rect(SIDEBAR_X + 230, 410, 190, 36)
                    prop = self.game.board[p.position].property_data
                    if prop:
                        if buy_rect.collidepoint(mx, my):
                            self.game.buy_property(p, prop)
                            return
                        elif auction_rect.collidepoint(mx, my):
                            self.game.start_auction(prop)
                            return

                # 3. Income Tax Buttons
                elif self.game.phase == GamePhase.INCOME_TAX_CHOICE:
                    tax_200_rect = pygame.Rect(SIDEBAR_X + 20, 410, 190, 36)
                    tax_10_rect = pygame.Rect(SIDEBAR_X + 230, 410, 190, 36)
                    if tax_200_rect.collidepoint(mx, my):
                        self.game.handle_income_tax_choice("flat")
                        return
                    elif tax_10_rect.collidepoint(mx, my):
                        self.game.handle_income_tax_choice("percent")
                        return

                # 4. Speed Die Bus Choices
                elif self.game.phase == GamePhase.SPEED_BUS_CHOICE:
                    roll = self.game.last_dice_roll
                    if roll:
                        b1 = pygame.Rect(SIDEBAR_X + 20, 410, 120, 36)
                        b2 = pygame.Rect(SIDEBAR_X + 160, 410, 120, 36)
                        b3 = pygame.Rect(SIDEBAR_X + 300, 410, 120, 36)
                        if b1.collidepoint(mx, my):
                            self.game.handle_bus_choice(roll.die1)
                            return
                        elif b2.collidepoint(mx, my):
                            self.game.handle_bus_choice(roll.die2)
                            return
                        elif b3.collidepoint(mx, my):
                            self.game.handle_bus_choice(roll.white_total)
                            return

                # 5. End Turn Button
                elif self.game.phase == GamePhase.MANAGING_PROPERTIES:
                    end_rect = pygame.Rect(SIDEBAR_X + 20, 410, 200, 36)
                    if end_rect.collidepoint(mx, my):
                        self.game.end_turn()
                        return

            # Auction Controls (if human is current bidder)
            if self.game.phase == GamePhase.AUCTION_IN_PROGRESS and self.game.pending_auction:
                bidder = self.game.pending_auction.current_bidder
                if bidder and not bidder.is_cpu:
                    bid_10 = pygame.Rect(SIDEBAR_X + 20, 410, 120, 36)
                    bid_50 = pygame.Rect(SIDEBAR_X + 160, 410, 120, 36)
                    pass_btn = pygame.Rect(SIDEBAR_X + 300, 410, 120, 36)
                    cbid = self.game.pending_auction.current_bid
                    if bid_10.collidepoint(mx, my):
                        self.game.pending_auction.place_bid(bidder.id, cbid + 10)
                        return
                    elif bid_50.collidepoint(mx, my):
                        self.game.pending_auction.place_bid(bidder.id, cbid + 50)
                        return
                    elif pass_btn.collidepoint(mx, my):
                        self.game.pending_auction.pass_bid(bidder.id)
                        return

            # Jail Buttons for Human
            if p.in_jail and not p.is_cpu and self.game.phase == GamePhase.WAITING_FOR_ROLL:
                fine_rect = pygame.Rect(SIDEBAR_X + 20, 410, 130, 36)
                card_rect = pygame.Rect(SIDEBAR_X + 160, 410, 130, 36)
                roll_jail_rect = pygame.Rect(SIDEBAR_X + 300, 410, 130, 36)
                if fine_rect.collidepoint(mx, my):
                    self.game.pay_jail_fine(p)
                    return
                elif card_rect.collidepoint(mx, my):
                    self.game.use_jail_card(p)
                    return
                elif roll_jail_rect.collidepoint(mx, my):
                    self.game.execute_roll()
                    return

    # ---------------- Property Management Modal ---------------- #

    def _handle_manage_modal_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            p = self.game.current_player

            # Close button
            close_rect = pygame.Rect(870, 130, 80, 32)
            if close_rect.collidepoint(mx, my):
                self.in_manage_modal = False
                return

            # Property selection list
            for idx, p_idx in enumerate(p.properties):
                item_rect = pygame.Rect(320, 180 + idx * 28, 260, 26)
                if item_rect.collidepoint(mx, my):
                    self.selected_manage_prop_idx = p_idx
                    return

            # Action buttons for selected property
            if self.selected_manage_prop_idx is not None:
                prop = self.game.properties[self.selected_manage_prop_idx]
                build_rect = pygame.Rect(620, 340, 140, 34)
                sell_rect = pygame.Rect(780, 340, 140, 34)
                mort_rect = pygame.Rect(620, 390, 140, 34)
                unmort_rect = pygame.Rect(780, 390, 140, 34)

                if build_rect.collidepoint(mx, my):
                    success = RulesEngine.build_house(prop, self.game.properties, p, self.game.bank)
                    if success:
                        self.game.log(f"{p.name} built on {prop.name}!")
                    return
                elif sell_rect.collidepoint(mx, my):
                    success = RulesEngine.sell_house(prop, self.game.properties, p, self.game.bank)
                    if success:
                        self.game.log(f"{p.name} sold a building on {prop.name}!")
                    return
                elif mort_rect.collidepoint(mx, my):
                    success = RulesEngine.mortgage_property(prop, self.game.properties, p)
                    if success:
                        self.game.log(f"{p.name} mortgaged {prop.name}!")
                    return
                elif unmort_rect.collidepoint(mx, my):
                    success = RulesEngine.unmortgage_property(prop, p)
                    if success:
                        self.game.log(f"{p.name} unmortgaged {prop.name}!")
                    return

    def _render_manage_modal(self):
        # Darkened overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Modal box
        modal_rect = pygame.Rect(280, 110, 700, 500)
        pygame.draw.rect(self.screen, PANEL_BG, modal_rect, border_radius=10)
        pygame.draw.rect(self.screen, PANEL_BORDER, modal_rect, 2, border_radius=10)

        # Header
        p = self.game.current_player
        title_surf = self.font_title.render(f"Property Portfolio: {p.name}", True, TEXT_WHITE)
        self.screen.blit(title_surf, (310, 130))

        close_btn = Button(pygame.Rect(870, 130, 80, 32), "Close", bg_color=BTN_DANGER, font_size=12)
        close_btn.draw(self.screen)

        # Left list: Properties
        pygame.draw.rect(self.screen, (25, 30, 40), pygame.Rect(310, 175, 280, 410), border_radius=6)
        if not p.properties:
            empty_surf = self.font_main.render("No properties owned yet.", True, TEXT_MUTED)
            self.screen.blit(empty_surf, (325, 200))
        else:
            for idx, p_idx in enumerate(p.properties):
                prop = self.game.properties[p_idx]
                r = pygame.Rect(315, 180 + idx * 28, 270, 26)
                is_sel = (self.selected_manage_prop_idx == p_idx)
                color = (50, 60, 80) if is_sel else (30, 36, 48)
                pygame.draw.rect(self.screen, color, r, border_radius=4)

                # Color indicator
                bar_col = COLOR_RGB_MAP.get(prop.group, (150, 150, 150))
                pygame.draw.rect(self.screen, bar_col, pygame.Rect(318, 184, 8, 18), border_radius=2)

                status_str = "M" if prop.is_mortgaged else (f"{prop.houses}H" if prop.houses > 0 else "")
                p_text = f"{prop.name[:18]}  {status_str}"
                t_surf = self.font_main.render(p_text, True, TEXT_WHITE if is_sel else TEXT_MUTED)
                self.screen.blit(t_surf, (332, 185))

        # Right pane: Deed details & Actions
        if self.selected_manage_prop_idx is not None:
            prop = self.game.properties[self.selected_manage_prop_idx]
            deed_rect = pygame.Rect(610, 175, 345, 150)
            pygame.draw.rect(self.screen, (245, 246, 240), deed_rect, border_radius=6)

            # Deed Title Bar
            bar_color = COLOR_RGB_MAP.get(prop.group, (80, 80, 80))
            pygame.draw.rect(self.screen, bar_color, pygame.Rect(610, 175, 345, 30), border_top_left_radius=6, border_top_right_radius=6)
            dn_surf = pygame.font.SysFont("arial", 13, bold=True).render(prop.name.upper(), True, (255, 255, 255))
            self.screen.blit(dn_surf, (deed_rect.centerx - dn_surf.get_width() // 2, 182))

            # Deed stats
            stats = [
                f"Group: {prop.group}  |  Price: ${prop.price}",
                f"Status: {'MORTGAGED' if prop.is_mortgaged else ('Hotel' if prop.houses == 5 else f'{prop.houses} Houses')}",
                f"House Cost: ${prop.house_cost} each  |  Mortgage: ${prop.mortgage_value}",
            ]
            if prop.space_type == SpaceType.PROPERTY:
                rent_str = f"Base Rent: ${prop.rents[0]} | With Hotel: ${prop.rents[5]}"
                stats.append(rent_str)

            for s_idx, st in enumerate(stats):
                s_surf = pygame.font.SysFont("arial", 11).render(st, True, (20, 20, 20))
                self.screen.blit(s_surf, (620, 215 + s_idx * 22))

            # Action Buttons
            can_b, _ = RulesEngine.can_build_house(prop, self.game.properties, p, self.game.bank)
            can_s, _ = RulesEngine.can_sell_house(prop, self.game.properties, p, self.game.bank)
            can_m, _ = RulesEngine.can_mortgage(prop, self.game.properties, p)
            can_u, _ = RulesEngine.can_unmortgage(prop, p)

            b_btn = Button(pygame.Rect(620, 340, 140, 34), "Build House", bg_color=BTN_SUCCESS if can_b else (60, 70, 80), font_size=11)
            s_btn = Button(pygame.Rect(780, 340, 140, 34), "Sell House (50%)", bg_color=BTN_WARNING if can_s else (60, 70, 80), font_size=11)
            m_btn = Button(pygame.Rect(620, 390, 140, 34), "Mortgage (50%)", bg_color=BTN_DANGER if can_m else (60, 70, 80), font_size=11)
            u_btn = Button(pygame.Rect(780, 390, 140, 34), "Lift (+10%)", bg_color=BTN_PRIMARY if can_u else (60, 70, 80), font_size=11)

            b_btn.draw(self.screen)
            s_btn.draw(self.screen)
            m_btn.draw(self.screen)
            u_btn.draw(self.screen)

            # Bank shortage info
            info_text = f"Bank Reserves Available: {self.game.bank.houses} Houses, {self.game.bank.hotels} Hotels"
            i_surf = self.font_main.render(info_text, True, TEXT_MUTED)
            self.screen.blit(i_surf, (620, 440))

    # ---------------- Game Over / Winner Modal ---------------- #

    def _render_game_over_modal(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))

        box = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 160, 500, 320)
        pygame.draw.rect(self.screen, PANEL_BG, box, border_radius=12)
        pygame.draw.rect(self.screen, (255, 215, 0), box, 3, border_radius=12)

        win_title = pygame.font.SysFont("arial", 28, bold=True).render("VICTORY!", True, (255, 215, 0))
        self.screen.blit(win_title, (box.centerx - win_title.get_width() // 2, box.y + 30))

        winner_name = self.game.winner.name if self.game.winner else "Winner"
        w_surf = pygame.font.SysFont("arial", 18, bold=True).render(f"{winner_name} HAS WON MONOPOLY!", True, TEXT_WHITE)
        self.screen.blit(w_surf, (box.centerx - w_surf.get_width() // 2, box.y + 80))

        stats = [
            f"Total Rounds Completed: {self.game.round_count}",
            f"Total Turns Played: {self.game.turn_count}",
            f"Final Cash: ${self.game.winner.cash if self.game.winner else 0}",
            f"Properties Owned: {len(self.game.winner.properties) if self.game.winner else 0}"
        ]
        for idx, s in enumerate(stats):
            st_surf = self.font_main.render(s, True, TEXT_MUTED)
            self.screen.blit(st_surf, (box.centerx - st_surf.get_width() // 2, box.y + 130 + idx * 24))

        # Restart Button
        restart_btn = Button(pygame.Rect(box.centerx - 90, box.y + 245, 180, 42), "PLAY AGAIN", bg_color=BTN_SUCCESS, font_size=14)
        restart_btn.draw(self.screen)

    # ---------------- In-Game Rendering ---------------- #

    def render(self):
        if self.in_setup:
            self._render_setup_screen()
            return

        self.screen.fill(BG_DARK)

        # 1. Draw Left Board
        self.renderer.draw_board(self.game.board, self.game.properties)
        self.renderer.draw_tokens(self.game.players)
        self.renderer.draw_center_area(
            self.game.current_player,
            self.game.last_dice_roll,
            self.game.bank,
            self.game.use_speed_die,
            self.game.round_count,
            self.game.turn_count
        )

        # 2. Draw Speed Bar under Board
        speed_bar_rect = pygame.Rect(15, 685, BOARD_SIZE, 45)
        pygame.draw.rect(self.screen, PANEL_BG, speed_bar_rect, border_radius=6)
        lbl_speed = self.font_bold.render("SIMULATION SPEED:", True, TEXT_MUTED)
        self.screen.blit(lbl_speed, (25, 690))

        for i, btn in enumerate(self.speed_buttons):
            # Highlight current speed
            if i == self.current_speed_idx:
                btn.bg_color = BTN_SUCCESS
            else:
                btn.bg_color = (45, 55, 72)
            btn.draw(self.screen)

        self.step_btn.draw(self.screen)

        # 3. Draw Right Sidebar (Player HUD, Controls, Logs)
        self._render_sidebar()

        # 4. Modals
        if self.in_manage_modal:
            self._render_manage_modal()

        if self.game.phase == GamePhase.GAME_OVER:
            self._render_game_over_modal()

    def _render_sidebar(self):
        # Container
        sb_rect = pygame.Rect(SIDEBAR_X, 15, SIDEBAR_WIDTH, 715)
        pygame.draw.rect(self.screen, PANEL_BG, sb_rect, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, sb_rect, 1, border_radius=8)

        # Section 1: Player Roster & Net Worth (Top 360px)
        title_surf = self.font_bold.render("PLAYERS & ASSETS", True, TEXT_WHITE)
        self.screen.blit(title_surf, (SIDEBAR_X + 15, 25))

        card_h = 52
        for idx, p in enumerate(self.game.players):
            cy = 50 + idx * card_h
            card_rect = pygame.Rect(SIDEBAR_X + 12, cy, SIDEBAR_WIDTH - 24, card_h - 4)
            is_active_turn = (self.game.current_player_idx == idx) and not p.is_bankrupt

            bg_col = (45, 54, 72) if is_active_turn else (28, 33, 44)
            pygame.draw.rect(self.screen, bg_col, card_rect, border_radius=6)
            if is_active_turn:
                pygame.draw.rect(self.screen, p.color, card_rect, 2, border_radius=6)

            # Player circle & name
            pygame.draw.circle(self.screen, p.color, (card_rect.x + 16, card_rect.centery), 9)
            
            status_tag = " (CPU)" if p.is_cpu else " (YOU)"
            if p.is_bankrupt:
                status_tag = " [BANKRUPT]"
            elif p.in_jail:
                status_tag += f" [JAIL {p.jail_turns}]"

            p_surf = self.font_bold.render(f"{p.name}{status_tag}", True, (160, 160, 160) if p.is_bankrupt else TEXT_WHITE)
            self.screen.blit(p_surf, (card_rect.x + 32, card_rect.y + 6))

            # Cash & Worth
            worth = p.total_worth(self.game.properties)
            cash_str = f"Cash: ${p.cash}  |  Worth: ${worth}  |  Props: {len(p.properties)}"
            cash_surf = self.font_main.render(cash_str, True, BTN_SUCCESS if not p.is_bankrupt else TEXT_MUTED)
            self.screen.blit(cash_surf, (card_rect.x + 32, card_rect.y + 26))

        # Section 2: Action Controls Panel (Middle: y ~ 370 to 465)
        ctrl_rect = pygame.Rect(SIDEBAR_X + 12, 365, SIDEBAR_WIDTH - 24, 95)
        pygame.draw.rect(self.screen, (28, 33, 44), ctrl_rect, border_radius=6)
        
        c_title = self.font_bold.render(f"ACTIONS: {self.game.phase.name}", True, (255, 215, 0))
        self.screen.blit(c_title, (SIDEBAR_X + 20, 375))

        self._render_action_buttons()

        # Section 3: Live Event Log (Bottom: y ~ 470 to 715)
        log_container = pygame.Rect(SIDEBAR_X + 12, 470, SIDEBAR_WIDTH - 24, 245)
        pygame.draw.rect(self.screen, (20, 24, 32), log_container, border_radius=6)
        pygame.draw.rect(self.screen, PANEL_BORDER, log_container, 1, border_radius=6)

        log_head = self.font_bold.render("GAME ACTIVITY LOG", True, TEXT_MUTED)
        self.screen.blit(log_head, (SIDEBAR_X + 20, 478))

        # Show last 10 log messages
        visible_logs = self.game.logs[-10:]
        for l_idx, log_msg in enumerate(visible_logs):
            ly = 502 + l_idx * 21
            msg_surf = self.font_log.render(f"• {log_msg[:68]}", True, TEXT_WHITE)
            self.screen.blit(msg_surf, (SIDEBAR_X + 20, ly))

    def _render_action_buttons(self):
        p = self.game.current_player
        phase = self.game.phase

        # Always show Manage Properties button
        manage_btn = Button(pygame.Rect(SIDEBAR_X + 240, 405, 190, 36), "Portfolio / Deeds", bg_color=BTN_ACCENT, font_size=11)
        manage_btn.draw(self.screen)

        if p.is_cpu and phase != GamePhase.AUCTION_IN_PROGRESS:
            cpu_status = self.font_main.render("CPU is thinking / executing turn...", True, TEXT_MUTED)
            self.screen.blit(cpu_status, (SIDEBAR_X + 20, 415))
            return

        if phase == GamePhase.WAITING_FOR_ROLL:
            if p.in_jail:
                # Jail options
                fine_btn = Button(pygame.Rect(SIDEBAR_X + 20, 405, 65, 36), "Pay $50", bg_color=BTN_WARNING, font_size=10)
                card_btn = Button(pygame.Rect(SIDEBAR_X + 90, 405, 65, 36), "Card", bg_color=BTN_SUCCESS, font_size=10)
                roll_btn = Button(pygame.Rect(SIDEBAR_X + 160, 405, 70, 36), "Roll 2x", bg_color=BTN_PRIMARY, font_size=10)
                fine_btn.draw(self.screen)
                card_btn.draw(self.screen)
                roll_btn.draw(self.screen)
            else:
                roll_btn = Button(pygame.Rect(SIDEBAR_X + 20, 405, 200, 36), "🎲 ROLL DICE", bg_color=BTN_PRIMARY, font_size=13)
                roll_btn.draw(self.screen)

        elif phase == GamePhase.BUY_OR_AUCTION_DECISION:
            prop = self.game.board[p.position].property_data
            price = prop.price if prop else 0
            buy_btn = Button(pygame.Rect(SIDEBAR_X + 20, 405, 100, 36), f"BUY (${price})", bg_color=BTN_SUCCESS, font_size=11)
            auc_btn = Button(pygame.Rect(SIDEBAR_X + 125, 405, 105, 36), "AUCTION", bg_color=BTN_WARNING, font_size=11)
            buy_btn.draw(self.screen)
            auc_btn.draw(self.screen)

        elif phase == GamePhase.AUCTION_IN_PROGRESS and self.game.pending_auction:
            bidder = self.game.pending_auction.current_bidder
            auc = self.game.pending_auction
            if bidder and not bidder.is_cpu:
                b10 = Button(pygame.Rect(SIDEBAR_X + 20, 405, 65, 36), "+$10", bg_color=BTN_SUCCESS, font_size=11)
                b50 = Button(pygame.Rect(SIDEBAR_X + 90, 405, 65, 36), "+$50", bg_color=BTN_PRIMARY, font_size=11)
                p_btn = Button(pygame.Rect(SIDEBAR_X + 160, 405, 65, 36), "PASS", bg_color=BTN_DANGER, font_size=11)
                b10.draw(self.screen)
                b50.draw(self.screen)
                p_btn.draw(self.screen)
            else:
                bidder_name = bidder.name if bidder else "Ending..."
                info = self.font_main.render(f"Bidding: {bidder_name} | Top: ${auc.current_bid}", True, TEXT_WHITE)
                self.screen.blit(info, (SIDEBAR_X + 20, 415))

        elif phase == GamePhase.INCOME_TAX_CHOICE:
            flat_btn = Button(pygame.Rect(SIDEBAR_X + 20, 405, 100, 36), "Pay $200", bg_color=BTN_WARNING, font_size=11)
            pct_btn = Button(pygame.Rect(SIDEBAR_X + 125, 405, 105, 36), "Pay 10%", bg_color=BTN_PRIMARY, font_size=11)
            flat_btn.draw(self.screen)
            pct_btn.draw(self.screen)

        elif phase == GamePhase.SPEED_BUS_CHOICE:
            roll = self.game.last_dice_roll
            if roll:
                b1 = Button(pygame.Rect(SIDEBAR_X + 20, 405, 65, 36), f"{roll.die1}", bg_color=BTN_PRIMARY, font_size=11)
                b2 = Button(pygame.Rect(SIDEBAR_X + 90, 405, 65, 36), f"{roll.die2}", bg_color=BTN_PRIMARY, font_size=11)
                b3 = Button(pygame.Rect(SIDEBAR_X + 160, 405, 70, 36), f"{roll.white_total}", bg_color=BTN_SUCCESS, font_size=11)
                b1.draw(self.screen)
                b2.draw(self.screen)
                b3.draw(self.screen)

        elif phase == GamePhase.MANAGING_PROPERTIES:
            end_btn = Button(pygame.Rect(SIDEBAR_X + 20, 405, 200, 36), "END TURN", bg_color=BTN_SUCCESS, font_size=13)
            end_btn.draw(self.screen)
