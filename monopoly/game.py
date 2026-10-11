"""
Monopoly Game Engine Orchestrator.
Maintains the complete game state machine, card decks, turn flow, and rules enforcement.
"""

import random
from typing import List, Dict, Optional, Tuple, Any, Callable
from .models import (
    Player, BoardSpace, PropertyState, SpaceType, Bank, DiceRoll, Card, GamePhase
)
from .board_data import (
    BOARD_SPACES_DATA, CHANCE_CARDS, COMMUNITY_CHEST_CARDS,
    RAILROAD_INDICES, UTILITY_INDICES, COLOR_GROUPS
)
from .rules import RulesEngine
from .speed_die import SpeedDieHandler
from .auction import AuctionState
from .ai import MonopolyAI

class MonopolyGame:
    def __init__(
        self,
        player_configs: List[Dict[str, Any]],
        use_speed_die: bool = False
    ):
        self.use_speed_die = use_speed_die
        starting_cash = 2500 if use_speed_die else 1500
        
        # Initialize Players
        self.players: List[Player] = []
        for i, cfg in enumerate(player_configs):
            p = Player(
                id=i,
                name=cfg["name"],
                is_cpu=cfg.get("is_cpu", False),
                color=cfg.get("color", (255, 255, 255)),
                token_name=cfg.get("token_name", "Token"),
                cash=starting_cash,
                position=0
            )
            self.players.append(p)

        self.bank = Bank()
        self.properties: Dict[int, PropertyState] = {}
        self.board: List[BoardSpace] = []
        self._init_board()

        # Initialize Decks
        self.chance_deck: List[Card] = [Card(is_chance=True, **c) for c in CHANCE_CARDS]
        self.community_chest_deck: List[Card] = [Card(is_chance=False, **c) for c in COMMUNITY_CHEST_CARDS]
        random.shuffle(self.chance_deck)
        random.shuffle(self.community_chest_deck)

        # Game State
        self.current_player_idx: int = 0
        self.phase: GamePhase = GamePhase.WAITING_FOR_ROLL
        self.last_dice_roll: Optional[DiceRoll] = None
        self.pending_auction: Optional[AuctionState] = None
        self.pending_card: Optional[Card] = None
        self.pending_tax_space: Optional[BoardSpace] = None
        self.pending_mr_monopoly: bool = False
        self.winner: Optional[Player] = None
        self.turn_count: int = 0
        self.round_count: int = 1

        # Activity log
        self.logs: List[str] = [
            f"Game started with {len(self.players)} players! Mode: {'Speed Die' if use_speed_die else 'Classic Monopoly'}."
        ]

    def _init_board(self):
        for data in BOARD_SPACES_DATA:
            stype = SpaceType(data["type"])
            prop_state = None
            if stype in (SpaceType.PROPERTY, SpaceType.RAILROAD, SpaceType.UTILITY):
                prop_state = PropertyState(
                    index=data["index"],
                    name=data["name"],
                    space_type=stype,
                    group=data.get("color", data["type"].title()),
                    price=data["price"],
                    mortgage_value=data["mortgage"],
                    house_cost=data.get("house_cost", 0),
                    rents=data.get("rents", []),
                    multipliers=data.get("multipliers", [])
                )
                self.properties[data["index"]] = prop_state

            space = BoardSpace(
                index=data["index"],
                name=data["name"],
                space_type=stype,
                sub_type=data.get("sub_type"),
                tax_amount=data.get("amount", 0),
                tax_percent=data.get("percent", 0.0),
                property_data=prop_state
            )
            self.board.append(space)

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_idx]

    @property
    def active_players(self) -> List[Player]:
        return [p for p in self.players if not p.is_bankrupt]

    def log(self, message: str):
        self.logs.append(message)
        if len(self.logs) > 200:
            self.logs.pop(0)

    # ---------------- Turn Management ---------------- #

    def roll_dice(self) -> DiceRoll:
        p = self.current_player
        should_use_speed = self.use_speed_die and p.has_passed_go_once
        roll = SpeedDieHandler.roll_dice(should_use_speed)
        self.last_dice_roll = roll
        return roll

    def execute_roll(self):
        p = self.current_player
        if p.is_bankrupt:
            self.end_turn()
            return

        # Check Jail Status
        if p.in_jail:
            self._handle_jail_turn()
            return

        roll = self.roll_dice()
        speed_desc = f" + Speed Die [{roll.speed_die}]" if roll.speed_die is not None else ""
        self.log(f"{p.name} rolled {roll.die1} and {roll.die2}{speed_desc} (Total: {roll.effective_total}).")

        # Doubles handling
        if roll.is_doubles:
            p.consecutive_doubles += 1
            if p.consecutive_doubles == 3:
                self.log(f"ALERT: {p.name} rolled doubles 3 times in a row! Sent directly to Jail!")
                self.send_to_jail(p)
                self.end_turn()
                return
        else:
            p.consecutive_doubles = 0

        # Speed Die Triples: "move anywhere you want on the board!"
        if roll.is_triples:
            self.log(f"TRIPLES! {p.name} rolled three-of-a-kind ({roll.die1})! Can move to any space!")
            self.phase = GamePhase.SPEED_TRIPLES_CHOICE
            if p.is_cpu:
                self.handle_triples_choice(p, 0) # CPU chooses GO or unowned property
            return

        # Speed Die Bus: choice of die1, die2, or sum
        if roll.speed_die == "bus":
            self.phase = GamePhase.SPEED_BUS_CHOICE
            if p.is_cpu:
                chosen = MonopolyAI.pick_bus_move(roll.die1, roll.die2, p.position, self.board)
                self.handle_bus_choice(chosen)
            return

        # Speed Die Mr. Monopoly: flags extra move after resolving current space
        if roll.speed_die == "mr_monopoly":
            self.pending_mr_monopoly = True

        # Normal move
        self.move_player(p, roll.effective_total)

    def handle_bus_choice(self, chosen_spaces: int):
        p = self.current_player
        self.log(f"{p.name} chooses the Bus move of {chosen_spaces} spaces.")
        self.move_player(p, chosen_spaces)

    def handle_triples_choice(self, player: Player, target_space_idx: int):
        self.log(f"{player.name} teleports to {self.board[target_space_idx].name} via Triples!")
        if target_space_idx < player.position:
            # Passed GO
            player.cash += 200
            player.has_passed_go_once = True
            self.log(f"{player.name} passed GO and collected $200 salary.")
        player.position = target_space_idx
        self.resolve_space(player)

    def move_player(self, player: Player, spaces: int):
        old_pos = player.position
        new_pos = (old_pos + spaces) % 40
        
        # Check passing GO (Hasbro rules: salary paid on landing or passing)
        if new_pos < old_pos or (old_pos + spaces >= 40):
            player.cash += 200
            player.has_passed_go_once = True
            self.log(f"{player.name} passed GO and collected $200 salary.")

        player.position = new_pos
        self.resolve_space(player)

    def resolve_space(self, player: Player):
        space = self.board[player.position]
        self.log(f"{player.name} landed on {space.name}.")

        if space.space_type == SpaceType.CORNER:
            if space.sub_type == "go_to_jail":
                self.log(f"{player.name} landed on Go To Jail!")
                self.send_to_jail(player)
                self.end_turn()
            elif space.sub_type == "go":
                self.log(f"{player.name} landed on GO and collected $200 salary.")
                player.cash += 200
                player.has_passed_go_once = True
                self._after_space_resolved()
            else: # Just visiting or Free Parking
                self._after_space_resolved()

        elif space.space_type in (SpaceType.PROPERTY, SpaceType.RAILROAD, SpaceType.UTILITY):
            prop = space.property_data
            if prop.owner_id is None:
                # Unowned property: Prompt buy or auction
                self.phase = GamePhase.BUY_OR_AUCTION_DECISION
                if player.is_cpu:
                    should_buy = MonopolyAI.should_buy_property(player, prop, self.properties, self.players)
                    if should_buy:
                        self.buy_property(player, prop)
                    else:
                        self.start_auction(prop)
            elif prop.owner_id == player.id:
                self.log(f"{player.name} already owns {prop.name}.")
                self._after_space_resolved()
            else:
                # Pay Rent
                owner = self.players[prop.owner_id]
                rent = RulesEngine.calculate_rent(prop, self.properties, self.last_dice_roll.utility_total if self.last_dice_roll else 7)
                if rent > 0:
                    self.log(f"{player.name} owes ${rent} rent to {owner.name} for {prop.name}.")
                    self.pay_rent(player, owner, rent)
                else:
                    self.log(f"{prop.name} is mortgaged; no rent owed.")
                    self._after_space_resolved()

        elif space.space_type == SpaceType.TAX:
            if space.tax_percent > 0:
                # Income tax: Hasbro rules give option of $200 or 10%
                self.phase = GamePhase.INCOME_TAX_CHOICE
                self.pending_tax_space = space
                if player.is_cpu:
                    choice = MonopolyAI.decide_income_tax_choice(player, self.properties)
                    self.handle_income_tax_choice(choice)
            else:
                # Flat Luxury Tax
                self.log(f"{player.name} paid ${space.tax_amount} Luxury Tax.")
                self.pay_bank(player, space.tax_amount)
                self._after_space_resolved()

        elif space.space_type in (SpaceType.CHANCE, SpaceType.COMMUNITY_CHEST):
            self.draw_card(player, is_chance=(space.space_type == SpaceType.CHANCE))

    def _after_space_resolved(self):
        p = self.current_player
        if p.is_bankrupt:
            self.end_turn()
            return

        # Check Mr. Monopoly Speed Die action
        if self.pending_mr_monopoly:
            self.pending_mr_monopoly = False
            self._handle_mr_monopoly(p)
            return

        # If doubles were rolled, player gets another turn!
        if self.last_dice_roll and self.last_dice_roll.is_doubles and not p.in_jail:
            self.log(f"{p.name} rolled doubles and gets to roll again!")
            self.phase = GamePhase.WAITING_FOR_ROLL
            if p.is_cpu:
                self.step_cpu()
        else:
            self.phase = GamePhase.MANAGING_PROPERTIES
            if p.is_cpu:
                self._cpu_manage_and_end_turn(p)

    def _handle_mr_monopoly(self, player: Player):
        self.log(f"SPEED DIE: Mr. Monopoly activates for {player.name}!")
        next_bank_idx = SpeedDieHandler.get_next_bank_property(player.position, self.board)
        if next_bank_idx is not None:
            self.log(f"Mr. Monopoly: Advancing to next unowned bank property: {self.board[next_bank_idx].name}.")
            # Note: Do we collect $200 if passing GO on Mr. Monopoly? Official rules: Yes, moving advances around board.
            if next_bank_idx < player.position:
                player.cash += 200
                player.has_passed_go_once = True
                self.log(f"{player.name} passed GO and collected $200.")
            player.position = next_bank_idx
            self.resolve_space(player)
        else:
            # No properties left in bank -> advance to next space owing rent!
            next_rent_idx = SpeedDieHandler.get_next_rent_property(player.position, player.id, self.board)
            if next_rent_idx is not None:
                self.log(f"Mr. Monopoly: Bank has no properties. Advancing to rent property: {self.board[next_rent_idx].name}.")
                if next_rent_idx < player.position:
                    player.cash += 200
                    player.has_passed_go_once = True
                    self.log(f"{player.name} passed GO and collected $200.")
                player.position = next_rent_idx
                self.resolve_space(player)
            else:
                self.log("Mr. Monopoly: No properties available to advance to.")
                self._after_space_resolved()

    # ---------------- Jail Logic ---------------- #

    def send_to_jail(self, player: Player):
        player.position = 10
        player.in_jail = True
        player.jail_turns = 0
        player.consecutive_doubles = 0
        self.log(f"{player.name} is now locked IN JAIL.")

    def _handle_jail_turn(self):
        p = self.current_player
        p.jail_turns += 1
        self.log(f"{p.name} is in Jail (Turn {p.jail_turns}/3).")

        # If CPU, decide action
        if p.is_cpu:
            decision = MonopolyAI.decide_jail_action(p, self.properties)
            if decision == "use_card":
                self.use_jail_card(p)
                return
            elif decision == "pay_fine" and p.jail_turns < 3 and p.cash >= 50:
                self.pay_jail_fine(p)
                return

        # Attempt to roll doubles
        roll = self.roll_dice()
        self.log(f"{p.name} rolled {roll.die1} and {roll.die2} to try for doubles to escape Jail.")

        if roll.is_doubles:
            self.log(f"{p.name} rolled DOUBLES and is released from Jail!")
            p.in_jail = False
            p.jail_turns = 0
            p.consecutive_doubles = 0
            # Hasbro rules: move the doubles spaces, but DO NOT take another turn
            self.move_player(p, roll.white_total)
            return

        if p.jail_turns >= 3:
            self.log(f"{p.name} failed to roll doubles for 3 turns. Must pay $50 fine to be released.")
            if p.cash >= 50:
                p.cash -= 50
                p.in_jail = False
                p.jail_turns = 0
                self.move_player(p, roll.white_total)
            else:
                self.resolve_bankruptcy(p, None, 50)
        else:
            self.log(f"{p.name} stays in Jail.")
            self.end_turn()

    def pay_jail_fine(self, player: Player):
        if player.cash >= 50:
            player.cash -= 50
            player.in_jail = False
            player.jail_turns = 0
            self.log(f"{player.name} paid $50 fine and is released from Jail.")
            self.execute_roll()
        else:
            self.log(f"{player.name} cannot afford the $50 jail fine.")

    def use_jail_card(self, player: Player):
        if player.get_out_of_jail_cards > 0:
            player.get_out_of_jail_cards -= 1
            player.in_jail = False
            player.jail_turns = 0
            # Return card to deck
            self.community_chest_deck.append(Card(id="cc5", text="Get Out of Jail Free card", action="jail_free", is_chance=False))
            self.log(f"{player.name} used a Get Out of Jail Free card and is released!")
            self.execute_roll()

    # ---------------- Buying & Auctions ---------------- #

    def buy_property(self, player: Player, prop: PropertyState):
        if player.cash >= prop.price:
            player.cash -= prop.price
            prop.owner_id = player.id
            player.properties.append(prop.index)
            self.log(f"{player.name} purchased {prop.name} for ${prop.price}.")
            self._after_space_resolved()
        else:
            self.log(f"{player.name} cannot afford {prop.name} (${prop.price}). Starting auction.")
            self.start_auction(prop)

    def start_auction(self, prop: PropertyState):
        self.log(f"Starting Banker Auction for {prop.name}!")
        self.pending_auction = AuctionState(prop, self.players)
        self.phase = GamePhase.AUCTION_IN_PROGRESS

    def step_auction(self):
        if not self.pending_auction or self.pending_auction.is_completed:
            self._conclude_auction()
            return

        bidder = self.pending_auction.current_bidder
        if not bidder:
            self._conclude_auction()
            return

        if bidder.is_cpu:
            bid = MonopolyAI.decide_auction_bid(
                bidder, self.pending_auction.property, self.pending_auction.current_bid,
                self.properties, self.players
            )
            if bid is not None:
                self.pending_auction.place_bid(bidder.id, bid)
            else:
                self.pending_auction.pass_bid(bidder.id)

            if self.pending_auction.is_completed:
                self._conclude_auction()

    def _conclude_auction(self):
        if not self.pending_auction:
            return
        winner, amount = self.pending_auction.conclude()
        prop = self.pending_auction.property
        if winner and amount > 0:
            winner.cash -= amount
            prop.owner_id = winner.id
            winner.properties.append(prop.index)
            self.log(f"AUCTION WON: {winner.name} won {prop.name} for ${amount}!")
        else:
            self.log(f"AUCTION ENDED: No bids placed for {prop.name}. Retained by Bank.")
        
        self.pending_auction = None
        self._after_space_resolved()

    # ---------------- Cards & Taxes ---------------- #

    def handle_income_tax_choice(self, choice: str):
        p = self.current_player
        tax = RulesEngine.calculate_income_tax(p, self.properties, choice)
        desc = "flat $200" if choice == "flat" else f"10% of total worth (${tax})"
        self.log(f"{p.name} chose {desc} for Income Tax.")
        self.pay_bank(p, tax)
        self.pending_tax_space = None
        self._after_space_resolved()

    def draw_card(self, player: Player, is_chance: bool):
        deck = self.chance_deck if is_chance else self.community_chest_deck
        card = deck.pop(0)
        self.pending_card = card
        deck_name = "Chance" if is_chance else "Community Chest"
        self.log(f"{player.name} drew {deck_name}: \"{card.text}\"")

        # Resolve card
        if card.action == "advance_to":
            if card.target is not None:
                if card.target < player.position or card.target == 0:
                    player.cash += 200
                    player.has_passed_go_once = True
                    self.log(f"{player.name} passed GO and collected $200.")
                player.position = card.target
                self.resolve_space(player)
                deck.append(card)
                return

        elif card.action == "advance_nearest_railroad":
            # Find nearest railroad
            rr_dists = [(rr_idx - player.position) % 40 for rr_idx in RAILROAD_INDICES]
            target_rr = RAILROAD_INDICES[rr_dists.index(min(rr_dists))]
            if target_rr < player.position:
                player.cash += 200
                player.has_passed_go_once = True
                self.log(f"{player.name} passed GO and collected $200.")
            player.position = target_rr
            # Check owner and charge double rent if owned
            prop = self.properties[target_rr]
            if prop.owner_id is not None and prop.owner_id != player.id and not prop.is_mortgaged:
                owner = self.players[prop.owner_id]
                rent = RulesEngine.calculate_rent(prop, self.properties, 0, double_railroad_rent=True)
                self.log(f"{player.name} owes double railroad rent (${rent}) to {owner.name}.")
                self.pay_rent(player, owner, rent)
            else:
                self.resolve_space(player)
            deck.append(card)
            return

        elif card.action == "advance_nearest_utility":
            util_dists = [(u_idx - player.position) % 40 for u_idx in UTILITY_INDICES]
            target_u = UTILITY_INDICES[util_dists.index(min(util_dists))]
            if target_u < player.position:
                player.cash += 200
                player.has_passed_go_once = True
                self.log(f"{player.name} passed GO and collected $200.")
            player.position = target_u
            prop = self.properties[target_u]
            if prop.owner_id is not None and prop.owner_id != player.id and not prop.is_mortgaged:
                owner = self.players[prop.owner_id]
                # Roll new dice to determine 10x multiplier
                temp_roll = random.randint(1, 6) + random.randint(1, 6)
                rent = RulesEngine.calculate_rent(prop, self.properties, temp_roll, forced_utility_multiplier=10)
                self.log(f"{player.name} owes 10x dice roll (${rent}) to {owner.name}.")
                self.pay_rent(player, owner, rent)
            else:
                self.resolve_space(player)
            deck.append(card)
            return

        elif card.action == "move_relative":
            player.position = (player.position + card.spaces) % 40
            self.resolve_space(player)
            deck.append(card)
            return

        elif card.action == "go_to_jail":
            self.send_to_jail(player)
            deck.append(card)
            self.end_turn()
            return

        elif card.action == "jail_free":
            player.get_out_of_jail_cards += 1
            self.log(f"{player.name} keeps the Get Out of Jail Free card.")
            # Card not returned to deck until played
            self._after_space_resolved()
            return

        elif card.action == "collect_money":
            player.cash += card.amount
            self.log(f"{player.name} collected ${card.amount}.")

        elif card.action == "pay_money":
            self.pay_bank(player, card.amount)

        elif card.action == "collect_from_each":
            total_collected = 0
            for opp in self.active_players:
                if opp.id != player.id:
                    amt = min(opp.cash, card.amount)
                    opp.cash -= amt
                    total_collected += amt
            player.cash += total_collected
            self.log(f"{player.name} collected a total of ${total_collected} from players.")

        elif card.action == "pay_each_player":
            for opp in self.active_players:
                if opp.id != player.id:
                    self.pay_rent(player, opp, card.amount)

        elif card.action == "repairs":
            total_fee = 0
            for p_idx in player.properties:
                p = self.properties[p_idx]
                if p.houses == 5:
                    total_fee += card.hotel_cost
                else:
                    total_fee += p.houses * card.house_cost
            self.log(f"{player.name} assessed ${total_fee} for repairs.")
            self.pay_bank(player, total_fee)

        deck.append(card)
        self._after_space_resolved()

    # ---------------- Payments & Bankruptcy ---------------- #

    def pay_bank(self, player: Player, amount: int):
        if player.cash >= amount:
            player.cash -= amount
        else:
            self.resolve_bankruptcy(player, None, amount)

    def pay_rent(self, debtor: Player, creditor: Player, amount: int):
        if debtor.cash >= amount:
            debtor.cash -= amount
            creditor.cash += amount
            self.log(f"{debtor.name} paid ${amount} to {creditor.name}.")
            self._after_space_resolved()
        else:
            self.resolve_bankruptcy(debtor, creditor, amount)

    def resolve_bankruptcy(self, debtor: Player, creditor: Optional[Player], debt_amount: int):
        self.log(f"ALERT: {debtor.name} is in debt for ${debt_amount} (Current Cash: ${debtor.cash})!")
        
        # CPU attempts to raise cash
        if debtor.is_cpu:
            h_sell, p_mort = MonopolyAI.get_mortgage_recommendations_for_debt(
                debtor, debt_amount, self.properties, self.bank
            )
            for h in h_sell:
                RulesEngine.sell_house(h, self.properties, debtor, self.bank)
                self.log(f"{debtor.name} sold a building on {h.name} for ${h.house_cost // 2}.")
            for p in p_mort:
                RulesEngine.mortgage_property(p, self.properties, debtor)
                self.log(f"{debtor.name} mortgaged {p.name} for ${p.mortgage_value}.")

        # Check if now able to pay
        if debtor.cash >= debt_amount:
            debtor.cash -= debt_amount
            if creditor:
                creditor.cash += debt_amount
            self.log(f"{debtor.name} raised enough funds and settled debt of ${debt_amount}.")
            self._after_space_resolved()
            return

        # Player is BANKRUPT!
        debtor.is_bankrupt = True
        self.log(f"BANKRUPTCY: {debtor.name} has gone BANKRUPT and is eliminated from the game!")

        if creditor:
            # Transfer all remaining cash to creditor
            creditor.cash += debtor.cash
            debtor.cash = 0
            # Liquidate any remaining houses back to bank for 50%
            for p_idx in list(debtor.properties):
                prop = self.properties[p_idx]
                if prop.houses > 0:
                    sold_val = (prop.houses * prop.house_cost) // 2
                    creditor.cash += sold_val
                    if prop.houses == 5:
                        self.bank.return_hotel(1)
                    else:
                        self.bank.return_house(prop.houses)
                    prop.houses = 0
                # Transfer deed to creditor
                prop.owner_id = creditor.id
                creditor.properties.append(p_idx)
                # If mortgaged, creditor pays 10% interest immediately per Hasbro rules!
                if prop.is_mortgaged:
                    interest = int(prop.mortgage_value * 0.10)
                    if creditor.cash >= interest:
                        creditor.cash -= interest
                        self.log(f"{creditor.name} paid ${interest} (10% interest) on mortgaged {prop.name}.")
            debtor.properties.clear()
        else:
            # Owed Bank: bank puts all properties up for auction
            self.log("Bank reclaims properties and puts them up for auction.")
            for p_idx in list(debtor.properties):
                prop = self.properties[p_idx]
                prop.owner_id = None
                prop.houses = 0
                prop.is_mortgaged = False
            debtor.properties.clear()

        # Check game end condition: 1 player left
        remaining = self.active_players
        if len(remaining) == 1:
            self.winner = remaining[0]
            self.phase = GamePhase.GAME_OVER
            self.log(f"GAME OVER! {self.winner.name} HAS WON MONOPOLY!")
        else:
            self.end_turn()

    # ---------------- Managing & Ending Turn ---------------- #

    def _cpu_manage_and_end_turn(self, player: Player):
        # AI builds houses if viable
        to_build = MonopolyAI.get_building_recommendations(player, self.properties, self.bank)
        for prop in to_build:
            success = RulesEngine.build_house(prop, self.properties, player, self.bank)
            if success:
                label = "Hotel" if prop.houses == 5 else f"House #{prop.houses}"
                self.log(f"{player.name} erected a {label} on {prop.name} for ${prop.house_cost}.")
        self.end_turn()

    def end_turn(self):
        if self.phase == GamePhase.GAME_OVER:
            return

        self.last_dice_roll = None
        self.pending_auction = None
        self.pending_card = None
        self.pending_mr_monopoly = False

        # Next player
        active = self.active_players
        if len(active) <= 1:
            if active:
                self.winner = active[0]
            self.phase = GamePhase.GAME_OVER
            return

        while True:
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            if not self.players[self.current_player_idx].is_bankrupt:
                break

        if self.current_player_idx == 0:
            self.round_count += 1

        self.turn_count += 1
        self.phase = GamePhase.WAITING_FOR_ROLL

    def step_cpu(self):
        """Advances one atomic action if the current player or state requires CPU action."""
        if self.phase == GamePhase.GAME_OVER:
            return

        if self.phase == GamePhase.AUCTION_IN_PROGRESS:
            self.step_auction()
            return

        p = self.current_player
        if not p.is_cpu:
            return

        if self.phase == GamePhase.WAITING_FOR_ROLL:
            self.execute_roll()
        elif self.phase == GamePhase.MANAGING_PROPERTIES:
            self._cpu_manage_and_end_turn(p)
