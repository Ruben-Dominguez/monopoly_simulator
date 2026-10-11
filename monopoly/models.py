"""
Domain Models for the Monopoly Simulator.
Strictly captures all properties, players, bank assets, cards, and dice rolls.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple, Dict, Any
from .board_data import (
    BOARD_SPACES_DATA, COLOR_GROUPS, RAILROAD_INDICES, UTILITY_INDICES,
    GROUP_RAILROAD, GROUP_UTILITY, GROUP_SPECIAL
)

class SpaceType(Enum):
    PROPERTY = "property"
    RAILROAD = "railroad"
    UTILITY = "utility"
    TAX = "tax"
    CHANCE = "chance"
    COMMUNITY_CHEST = "community_chest"
    CORNER = "corner"

class GamePhase(Enum):
    WAITING_FOR_ROLL = auto()
    MOVING = auto()
    RESOLVING_SPACE = auto()
    BUY_OR_AUCTION_DECISION = auto()
    AUCTION_IN_PROGRESS = auto()
    INCOME_TAX_CHOICE = auto()
    SPEED_BUS_CHOICE = auto()
    SPEED_MR_MONOPOLY_MOVE = auto()
    SPEED_TRIPLES_CHOICE = auto()
    MANAGING_PROPERTIES = auto()
    RESOLVING_BANKRUPTCY = auto()
    GAME_OVER = auto()

@dataclass
class PropertyState:
    index: int
    name: str
    space_type: SpaceType
    group: str
    price: int
    mortgage_value: int
    house_cost: int
    rents: List[int] = field(default_factory=list)
    multipliers: List[int] = field(default_factory=list)
    owner_id: Optional[int] = None
    houses: int = 0  # 0-4 = houses, 5 = hotel
    is_mortgaged: bool = False

    @property
    def is_hotel(self) -> bool:
        return self.houses == 5

    @property
    def display_houses(self) -> int:
        return 0 if self.houses == 5 else self.houses

@dataclass
class BoardSpace:
    index: int
    name: str
    space_type: SpaceType
    sub_type: Optional[str] = None
    tax_amount: int = 0
    tax_percent: float = 0.0
    property_data: Optional[PropertyState] = None

@dataclass
class Player:
    id: int
    name: str
    is_cpu: bool
    color: Tuple[int, int, int]
    token_name: str
    cash: int = 1500
    position: int = 0
    in_jail: bool = False
    jail_turns: int = 0
    get_out_of_jail_cards: int = 0
    is_bankrupt: bool = False
    has_passed_go_once: bool = False
    consecutive_doubles: int = 0
    properties: List[int] = field(default_factory=list)

    def total_worth(self, property_map: Dict[int, PropertyState]) -> int:
        """
        Total worth calculation as specified in official rules:
        All cash on hand + printed prices of mortgaged and unmortgaged properties
        + cost price of all buildings owned.
        """
        worth = self.cash
        for p_idx in self.properties:
            prop = property_map.get(p_idx)
            if prop:
                worth += prop.price
                worth += prop.houses * prop.house_cost
        return worth

    def can_afford(self, amount: int) -> bool:
        return self.cash >= amount

@dataclass
class Bank:
    """Official bank supplies: 32 houses, 12 hotels."""
    houses: int = 32
    hotels: int = 12

    def has_house(self) -> bool:
        return self.houses > 0

    def has_hotel(self) -> bool:
        return self.hotels > 0

    def take_house(self, count: int = 1) -> bool:
        if self.houses >= count:
            self.houses -= count
            return True
        return False

    def return_house(self, count: int = 1):
        self.houses = min(32, self.houses + count)

    def take_hotel(self, count: int = 1) -> bool:
        if self.hotels >= count:
            self.hotels -= count
            return True
        return False

    def return_hotel(self, count: int = 1):
        self.hotels = min(12, self.hotels + count)

@dataclass
class DiceRoll:
    die1: int = 1
    die2: int = 1
    speed_die: Optional[Any] = None  # None, 1, 2, 3, "bus", "mr_monopoly"
    
    @property
    def is_doubles(self) -> bool:
        # Hasbro Speed Die rule: "Only the white dice are used when determining if you rolled doubles."
        return self.die1 == self.die2

    @property
    def is_triples(self) -> bool:
        # Hasbro Speed Die rule: "three-of-a-kind (all of the dice show the same number)"
        return isinstance(self.speed_die, int) and self.die1 == self.die2 == self.speed_die

    @property
    def white_total(self) -> int:
        return self.die1 + self.die2

    @property
    def effective_total(self) -> int:
        if isinstance(self.speed_die, int):
            return self.die1 + self.die2 + self.speed_die
        return self.die1 + self.die2

    @property
    def utility_total(self) -> int:
        # Hasbro rule: "Use the sum of all three dice when determining how much to pay on a utility. Bus & Mr Monopoly are valued at 0."
        if isinstance(self.speed_die, int):
            return self.die1 + self.die2 + self.speed_die
        return self.die1 + self.die2

@dataclass
class Card:
    id: str
    text: str
    action: str
    target: Optional[int] = None
    amount: int = 0
    spaces: int = 0
    house_cost: int = 0
    hotel_cost: int = 0
    is_chance: bool = True
