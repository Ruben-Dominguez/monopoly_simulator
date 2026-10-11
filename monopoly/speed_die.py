"""
Monopoly Speed Die System.
Faithfully implements the Hasbro Speed Die rules (00009.pdf, pages 1-2).
"""

import random
from typing import Tuple, Any, Optional, List
from .models import DiceRoll, PropertyState, Player, BoardSpace

# The 6 faces of the Hasbro Speed Die
SPEED_DIE_FACES = [1, 2, 3, "bus", "mr_monopoly", "mr_monopoly"]

class SpeedDieHandler:
    @staticmethod
    def roll_dice(use_speed_die: bool) -> DiceRoll:
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        speed = None
        if use_speed_die:
            speed = random.choice(SPEED_DIE_FACES)
        return DiceRoll(die1=d1, die2=d2, speed_die=speed)

    @staticmethod
    def get_next_bank_property(current_pos: int, properties: List[BoardSpace]) -> Optional[int]:
        """
        Finds the next property clockwise from current_pos that the bank still holds.
        """
        for offset in range(1, 40):
            idx = (current_pos + offset) % 40
            space = properties[idx]
            if space.property_data and space.property_data.owner_id is None:
                return idx
        return None

    @staticmethod
    def get_next_rent_property(current_pos: int, current_player_id: int, properties: List[BoardSpace]) -> Optional[int]:
        """
        Finds the next property clockwise where the current player will owe another player rent.
        """
        for offset in range(1, 40):
            idx = (current_pos + offset) % 40
            space = properties[idx]
            prop = space.property_data
            if prop and prop.owner_id is not None and prop.owner_id != current_player_id and not prop.is_mortgaged:
                return idx
        return None
