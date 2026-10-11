"""
Monopoly Official Rules Engine.
Implements the exact logic and rule specifications from Hasbro 00009.pdf.
"""

from typing import Dict, List, Optional, Tuple, Set
from .models import PropertyState, Player, Bank, SpaceType, BoardSpace
from .board_data import COLOR_GROUPS, RAILROAD_INDICES, UTILITY_INDICES

class RulesEngine:
    @staticmethod
    def owns_full_color_group(player_id: int, group: str, properties: Dict[int, PropertyState]) -> bool:
        """Returns True if the player owns all properties in the specified color group."""
        group_indices = COLOR_GROUPS.get(group, [])
        if not group_indices:
            return False
        return all(properties[idx].owner_id == player_id for idx in group_indices)

    @staticmethod
    def get_color_group_properties(group: str, properties: Dict[int, PropertyState]) -> List[PropertyState]:
        return [properties[idx] for idx in COLOR_GROUPS.get(group, [])]

    @staticmethod
    def calculate_rent(
        prop: PropertyState,
        properties: Dict[int, PropertyState],
        dice_total: int,
        forced_utility_multiplier: Optional[int] = None,
        double_railroad_rent: bool = False
    ) -> int:
        """
        Calculates rent strictly according to Hasbro rules.
        - Mortgaged properties collect $0.
        - Unimproved monopolies charge 2x base rent (even if another in group is mortgaged).
        - Railroads scale with number owned (25, 50, 100, 200).
        - Utilities scale with dice roll (4x or 10x).
        """
        if prop.is_mortgaged:
            return 0

        owner_id = prop.owner_id
        if owner_id is None:
            return 0

        # Property with houses / hotels or base
        if prop.space_type == SpaceType.PROPERTY:
            if prop.houses == 0:
                base = prop.rents[0]
                # Check complete color group
                if RulesEngine.owns_full_color_group(owner_id, prop.group, properties):
                    return base * 2
                return base
            else:
                # houses: 1, 2, 3, 4, 5 (hotel)
                idx = min(prop.houses, 5)
                return prop.rents[idx]

        # Railroads
        elif prop.space_type == SpaceType.RAILROAD:
            owned_rr = sum(1 for idx in RAILROAD_INDICES if properties[idx].owner_id == owner_id)
            # Rents: 1=25, 2=50, 3=100, 4=200
            rent_idx = max(0, min(owned_rr - 1, 3))
            base_rent = prop.rents[rent_idx]
            if double_railroad_rent:
                return base_rent * 2
            return base_rent

        # Utilities
        elif prop.space_type == SpaceType.UTILITY:
            if forced_utility_multiplier is not None:
                return forced_utility_multiplier * dice_total
            owned_util = sum(1 for idx in UTILITY_INDICES if properties[idx].owner_id == owner_id)
            multiplier = 10 if owned_util == 2 else 4
            return multiplier * dice_total

        return 0

    @staticmethod
    def can_build_house(
        prop: PropertyState,
        properties: Dict[int, PropertyState],
        player: Player,
        bank: Bank
    ) -> Tuple[bool, str]:
        """
        Enforces Hasbro even building rule and bank house supply.
        """
        if prop.space_type != SpaceType.PROPERTY:
            return False, "Not a developable property."
        if prop.owner_id != player.id:
            return False, "You do not own this property."
        if not RulesEngine.owns_full_color_group(player.id, prop.group, properties):
            return False, "You must own all properties in the color group to build."
        
        # Check if any property in group is mortgaged
        group_props = RulesEngine.get_color_group_properties(prop.group, properties)
        if any(p.is_mortgaged for p in group_props):
            return False, "Cannot build if any property in the color group is mortgaged."

        if prop.houses >= 5:
            return False, "Already has a hotel."

        if prop.houses == 4:
            # Building hotel
            if not bank.has_hotel():
                return False, "Bank has no hotels available (Housing shortage!)."
            if not player.can_afford(prop.house_cost):
                return False, f"Cannot afford hotel cost of ${prop.house_cost}."
            # Even building: all others in group must have at least 4 houses
            if any(p.houses < 4 for p in group_props):
                return False, "Must build evenly: all properties in group must have 4 houses before erecting a hotel."
            return True, "Ready to build hotel."

        # Building house (0-3)
        if not bank.has_house():
            return False, "Bank has no houses available (Housing shortage!)."
        if not player.can_afford(prop.house_cost):
            return False, f"Cannot afford house cost of ${prop.house_cost}."

        # Even building: cannot have > 1 more house than minimum in group
        min_houses = min(p.houses for p in group_props)
        if prop.houses > min_houses:
            return False, "Must build evenly across the color group."

        return True, "Ready to build house."

    @staticmethod
    def build_house(prop: PropertyState, properties: Dict[int, PropertyState], player: Player, bank: Bank) -> bool:
        can, reason = RulesEngine.can_build_house(prop, properties, player, bank)
        if not can:
            return False
        
        player.cash -= prop.house_cost
        if prop.houses == 4:
            # Upgrade to hotel: return 4 houses to bank, take 1 hotel
            bank.return_house(4)
            bank.take_hotel(1)
            prop.houses = 5
        else:
            bank.take_house(1)
            prop.houses += 1
        return True

    @staticmethod
    def can_sell_house(prop: PropertyState, properties: Dict[int, PropertyState], player: Player, bank: Bank) -> Tuple[bool, str]:
        """
        Enforces Hasbro rule: sell houses back to Bank at half price evenly.
        If selling a hotel, Bank must have 4 houses to replace it (or entire hotel sold at once).
        """
        if prop.space_type != SpaceType.PROPERTY:
            return False, "Not a developable property."
        if prop.owner_id != player.id:
            return False, "You do not own this property."
        if prop.houses == 0:
            return False, "No houses or hotels to sell."

        group_props = RulesEngine.get_color_group_properties(prop.group, properties)
        max_houses = max(p.houses for p in group_props)
        if prop.houses < max_houses:
            return False, "Must sell houses evenly in reverse of building order."

        if prop.houses == 5:
            # Selling hotel: replace with 4 houses if bank has them, otherwise must sell down to bank limit
            if bank.houses < 4:
                return False, f"Bank does not have 4 houses to break down hotel. Must sell multiple buildings if needed."
            return True, "Ready to sell hotel."

        return True, "Ready to sell house."

    @staticmethod
    def sell_house(prop: PropertyState, properties: Dict[int, PropertyState], player: Player, bank: Bank) -> bool:
        can, _ = RulesEngine.can_sell_house(prop, properties, player, bank)
        if not can:
            return False

        sell_price = prop.house_cost // 2
        player.cash += sell_price

        if prop.houses == 5:
            bank.return_hotel(1)
            bank.take_house(4)
            prop.houses = 4
        else:
            bank.return_house(1)
            prop.houses -= 1
        return True

    @staticmethod
    def can_mortgage(prop: PropertyState, properties: Dict[int, PropertyState], player: Player) -> Tuple[bool, str]:
        if prop.owner_id != player.id:
            return False, "You do not own this property."
        if prop.is_mortgaged:
            return False, "Property is already mortgaged."
        if prop.space_type == SpaceType.PROPERTY:
            group_props = RulesEngine.get_color_group_properties(prop.group, properties)
            if any(p.houses > 0 for p in group_props):
                return False, "All buildings on all properties in this color group must be sold before mortgaging."
        return True, "Can mortgage."

    @staticmethod
    def mortgage_property(prop: PropertyState, properties: Dict[int, PropertyState], player: Player) -> bool:
        can, _ = RulesEngine.can_mortgage(prop, properties, player)
        if not can:
            return False
        prop.is_mortgaged = True
        player.cash += prop.mortgage_value
        return True

    @staticmethod
    def can_unmortgage(prop: PropertyState, player: Player) -> Tuple[bool, str]:
        if prop.owner_id != player.id:
            return False, "You do not own this property."
        if not prop.is_mortgaged:
            return False, "Property is not mortgaged."
        lift_cost = prop.mortgage_value + int(prop.mortgage_value * 0.10)
        if not player.can_afford(lift_cost):
            return False, f"Cannot afford unmortgage cost of ${lift_cost} (includes 10% interest)."
        return True, "Can unmortgage."

    @staticmethod
    def unmortgage_property(prop: PropertyState, player: Player) -> bool:
        can, _ = RulesEngine.can_unmortgage(prop, player)
        if not can:
            return False
        lift_cost = prop.mortgage_value + int(prop.mortgage_value * 0.10)
        player.cash -= lift_cost
        prop.is_mortgaged = False
        return True

    @staticmethod
    def calculate_income_tax(player: Player, property_map: Dict[int, PropertyState], choice: str) -> int:
        """
        Hasbro Income Tax: Choose between $200 flat or 10% of total worth.
        Total worth = cash + printed property prices + building cost price.
        """
        if choice == "flat":
            return 200
        else:
            worth = player.total_worth(property_map)
            return int(worth * 0.10)
