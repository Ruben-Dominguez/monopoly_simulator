"""
Autonomous CPU Decision Making Agent for Monopoly.
Implements strategic gameplay heuristics for buying, bidding, developing, mortgaging, and jail.
"""

from typing import Dict, List, Optional, Tuple
from .models import Player, PropertyState, SpaceType, Bank, BoardSpace
from .rules import RulesEngine
from .board_data import COLOR_GROUPS

class MonopolyAI:
    @staticmethod
    def should_buy_property(
        player: Player,
        prop: PropertyState,
        properties: Dict[int, PropertyState],
        all_players: List[Player]
    ) -> bool:
        """
        AI decides whether to buy a property at face value or send it to auction.
        """
        # Always need to afford it
        if player.cash < prop.price:
            return False

        # If it completes our monopoly, 100% buy!
        group_props = [properties[idx] for idx in COLOR_GROUPS.get(prop.group, [])] if prop.group in COLOR_GROUPS else []
        our_props_in_group = [p for p in group_props if p.owner_id == player.id]
        if len(group_props) > 0 and len(our_props_in_group) == len(group_props) - 1:
            return True

        # If it blocks an opponent's monopoly, 100% buy!
        for opp in all_players:
            if opp.id != player.id and not opp.is_bankrupt:
                opp_props = [p for p in group_props if p.owner_id == opp.id]
                if len(group_props) > 0 and len(opp_props) == len(group_props) - 1:
                    return True

        # Safety cash reserve: keep at least $100 after purchase unless it's early game
        reserve = 100
        if player.cash - prop.price >= reserve:
            return True
        
        # If very low cash, decline to trigger auction (might get it cheaper or conserve cash)
        return False

    @staticmethod
    def evaluate_auction_max_bid(
        player: Player,
        prop: PropertyState,
        properties: Dict[int, PropertyState],
        all_players: List[Player]
    ) -> int:
        """
        Calculates the maximum amount an AI is willing to bid for a property.
        """
        base_value = prop.price
        multiplier = 0.8  # Baseline willingness

        group_props = [properties[idx] for idx in COLOR_GROUPS.get(prop.group, [])] if prop.group in COLOR_GROUPS else []
        our_count = sum(1 for p in group_props if p.owner_id == player.id)
        
        # Completion bonus
        if len(group_props) > 0 and our_count == len(group_props) - 1:
            multiplier = 1.4  # Willing to pay above market to complete monopoly!
        elif our_count > 0:
            multiplier = 1.1

        # Blocking bonus
        for opp in all_players:
            if opp.id != player.id and not opp.is_bankrupt:
                opp_count = sum(1 for p in group_props if p.owner_id == opp.id)
                if len(group_props) > 0 and opp_count == len(group_props) - 1:
                    multiplier = max(multiplier, 1.3)

        max_bid = int(base_value * multiplier)
        
        # Cap bid at current cash minus a safety reserve of $50
        cash_cap = max(0, player.cash - 50)
        return min(max_bid, cash_cap)

    @staticmethod
    def decide_auction_bid(
        player: Player,
        prop: PropertyState,
        current_bid: int,
        properties: Dict[int, PropertyState],
        all_players: List[Player]
    ) -> Optional[int]:
        max_bid = MonopolyAI.evaluate_auction_max_bid(player, prop, properties, all_players)
        if current_bid >= max_bid:
            return None  # Pass
        
        # Minimum increment: +$10 or +$1
        increment = 10 if max_bid - current_bid >= 20 else 5
        next_bid = max(current_bid + increment, current_bid + 1)
        if next_bid <= max_bid and next_bid <= player.cash:
            return next_bid
        if current_bid + 1 <= max_bid and current_bid + 1 <= player.cash:
            return current_bid + 1
        return None

    @staticmethod
    def decide_jail_action(player: Player, properties: Dict[int, PropertyState]) -> str:
        """
        Returns: 'pay_fine', 'use_card', or 'roll_doubles'
        """
        # If has Get Out of Jail Free card, always use it
        if player.get_out_of_jail_cards > 0:
            return "use_card"

        # Check stage of game: unowned properties count
        unowned = sum(1 for p in properties.values() if p.owner_id is None)
        
        # Early/mid game with lots of unowned properties: pay $50 to get moving and buying
        if unowned >= 8 and player.cash >= 250:
            return "pay_fine"
        
        # Late game: high rents on board, safe in jail! Try rolling doubles
        return "roll_doubles"

    @staticmethod
    def decide_income_tax_choice(player: Player, properties: Dict[int, PropertyState]) -> str:
        """
        Decides between flat $200 or 10% of total worth.
        """
        ten_percent = RulesEngine.calculate_income_tax(player, properties, "percent")
        if ten_percent < 200:
            return "percent"
        return "flat"

    @staticmethod
    def get_building_recommendations(
        player: Player,
        properties: Dict[int, PropertyState],
        bank: Bank
    ) -> List[PropertyState]:
        """
        Finds all properties the AI should build houses on right now.
        Maintains a cash buffer of $200.
        """
        to_build: List[PropertyState] = []
        sim_cash = player.cash
        safe_buffer = 200

        # Look through all color groups
        for group in COLOR_GROUPS.keys():
            if RulesEngine.owns_full_color_group(player.id, group, properties):
                group_props = RulesEngine.get_color_group_properties(group, properties)
                # Sort by current houses (lowest first to respect even building)
                group_props.sort(key=lambda p: p.houses)
                for prop in group_props:
                    if sim_cash - prop.house_cost >= safe_buffer:
                        can, _ = RulesEngine.can_build_house(prop, properties, player, bank)
                        if can:
                            to_build.append(prop)
                            sim_cash -= prop.house_cost
        return to_build

    @staticmethod
    def get_mortgage_recommendations_for_debt(
        player: Player,
        debt_amount: int,
        properties: Dict[int, PropertyState],
        bank: Bank
    ) -> Tuple[List[PropertyState], List[PropertyState]]:
        """
        Returns (houses_to_sell, props_to_mortgage) to raise cash for a debt.
        """
        houses_to_sell: List[PropertyState] = []
        props_to_mortgage: List[PropertyState] = []
        cash_needed = debt_amount - player.cash
        if cash_needed <= 0:
            return houses_to_sell, props_to_mortgage

        # 1. First sell houses if needed
        for p_idx in player.properties:
            prop = properties[p_idx]
            while prop.houses > 0 and cash_needed > 0:
                can, _ = RulesEngine.can_sell_house(prop, properties, player, bank)
                if can:
                    houses_to_sell.append(prop)
                    cash_needed -= (prop.house_cost // 2)
                else:
                    break

        # 2. Mortgage unimproved / isolated properties first
        owned_props = [properties[p_idx] for p_idx in player.properties if not properties[p_idx].is_mortgaged]
        # Prioritize properties that do not form a complete monopoly
        owned_props.sort(key=lambda p: (
            1 if RulesEngine.owns_full_color_group(player.id, p.group, properties) else 0,
            p.price
        ))

        for prop in owned_props:
            if cash_needed <= 0:
                break
            can, _ = RulesEngine.can_mortgage(prop, properties, player)
            if can:
                props_to_mortgage.append(prop)
                cash_needed -= prop.mortgage_value

        return houses_to_sell, props_to_mortgage

    @staticmethod
    def pick_bus_move(die1: int, die2: int, current_pos: int, board: List[BoardSpace]) -> int:
        """
        Chooses whether to move die1, die2, or die1 + die2.
        Picks the destination with lowest hazard or highest reward.
        """
        options = [die1, die2, die1 + die2]
        best_opt = options[0]
        best_score = -999999

        for opt in options:
            target_pos = (current_pos + opt) % 40
            space = board[target_pos]
            score = 0
            if target_pos == 0:
                score += 500  # Landing directly on GO is great
            if target_pos == 30:
                score -= 1000 # Avoid Go to Jail!
            if space.property_data:
                prop = space.property_data
                if prop.owner_id is None:
                    score += 300  # Opportunity to buy
                elif not prop.is_mortgaged:
                    score -= 200  # Avoid paying rent
            if score > best_score:
                best_score = score
                best_opt = opt
        return best_opt
