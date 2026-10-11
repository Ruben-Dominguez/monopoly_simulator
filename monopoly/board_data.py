"""
Official Atlantic City Monopoly Board Data & Title Deed Specifications.
Conforms strictly to the Hasbro official rulebook (00009.pdf).
"""

from typing import Dict, List, Any

# 8 Color groups + Special groups
COLOR_BROWN = "Brown"
COLOR_LIGHT_BLUE = "Light Blue"
COLOR_PINK = "Pink"
COLOR_ORANGE = "Orange"
COLOR_RED = "Red"
COLOR_YELLOW = "Yellow"
COLOR_GREEN = "Green"
COLOR_DARK_BLUE = "Dark Blue"
GROUP_RAILROAD = "Railroad"
GROUP_UTILITY = "Utility"
GROUP_SPECIAL = "Special"

# 40 Board Spaces in clockwise order (0 to 39)
# Format:
# index, name, type ("property", "railroad", "utility", "tax", "chance", "community_chest", "corner")
# For properties: color, price, house_cost, rents: [base, 1h, 2h, 3h, 4h, hotel], mortgage
BOARD_SPACES_DATA: List[Dict[str, Any]] = [
    # Bottom Row (0 - 10): GO -> Jail
    {"index": 0, "name": "GO", "type": "corner", "sub_type": "go"},
    {
        "index": 1, "name": "Mediterranean Avenue", "type": "property",
        "color": COLOR_BROWN, "price": 60, "house_cost": 50,
        "rents": [2, 10, 30, 90, 160, 250], "mortgage": 30
    },
    {"index": 2, "name": "Community Chest", "type": "community_chest"},
    {
        "index": 3, "name": "Baltic Avenue", "type": "property",
        "color": COLOR_BROWN, "price": 60, "house_cost": 50,
        "rents": [4, 20, 60, 180, 320, 450], "mortgage": 30
    },
    {"index": 4, "name": "Income Tax", "type": "tax", "amount": 200, "percent": 0.10},
    {
        "index": 5, "name": "Reading Railroad", "type": "railroad",
        "price": 200, "mortgage": 100, "rents": [25, 50, 100, 200]
    },
    {
        "index": 6, "name": "Oriental Avenue", "type": "property",
        "color": COLOR_LIGHT_BLUE, "price": 100, "house_cost": 50,
        "rents": [6, 30, 90, 270, 400, 550], "mortgage": 50
    },
    {"index": 7, "name": "Chance", "type": "chance"},
    {
        "index": 8, "name": "Vermont Avenue", "type": "property",
        "color": COLOR_LIGHT_BLUE, "price": 100, "house_cost": 50,
        "rents": [6, 30, 90, 270, 400, 550], "mortgage": 50
    },
    {
        "index": 9, "name": "Connecticut Avenue", "type": "property",
        "color": COLOR_LIGHT_BLUE, "price": 120, "house_cost": 50,
        "rents": [8, 40, 100, 300, 450, 600], "mortgage": 60
    },
    {"index": 10, "name": "Jail / Just Visiting", "type": "corner", "sub_type": "jail"},

    # Left Row (11 - 20): Jail -> Free Parking
    {
        "index": 11, "name": "St. Charles Place", "type": "property",
        "color": COLOR_PINK, "price": 140, "house_cost": 100,
        "rents": [10, 50, 150, 450, 625, 750], "mortgage": 70
    },
    {
        "index": 12, "name": "Electric Company", "type": "utility",
        "price": 150, "mortgage": 75, "multipliers": [4, 10]
    },
    {
        "index": 13, "name": "States Avenue", "type": "property",
        "color": COLOR_PINK, "price": 140, "house_cost": 100,
        "rents": [10, 50, 150, 450, 625, 750], "mortgage": 70
    },
    {
        "index": 14, "name": "Virginia Avenue", "type": "property",
        "color": COLOR_PINK, "price": 160, "house_cost": 100,
        "rents": [12, 60, 180, 500, 700, 900], "mortgage": 80
    },
    {
        "index": 15, "name": "Pennsylvania Railroad", "type": "railroad",
        "price": 200, "mortgage": 100, "rents": [25, 50, 100, 200]
    },
    {
        "index": 16, "name": "St. James Place", "type": "property",
        "color": COLOR_ORANGE, "price": 180, "house_cost": 100,
        "rents": [14, 70, 200, 550, 750, 950], "mortgage": 90
    },
    {"index": 17, "name": "Community Chest", "type": "community_chest"},
    {
        "index": 18, "name": "Tennessee Avenue", "type": "property",
        "color": COLOR_ORANGE, "price": 180, "house_cost": 100,
        "rents": [14, 70, 200, 550, 750, 950], "mortgage": 90
    },
    {
        "index": 19, "name": "New York Avenue", "type": "property",
        "color": COLOR_ORANGE, "price": 200, "house_cost": 100,
        "rents": [16, 80, 220, 600, 800, 1000], "mortgage": 100
    },
    {"index": 20, "name": "Free Parking", "type": "corner", "sub_type": "free_parking"},

    # Top Row (21 - 30): Free Parking -> Go To Jail
    {
        "index": 21, "name": "Kentucky Avenue", "type": "property",
        "color": COLOR_RED, "price": 220, "house_cost": 150,
        "rents": [18, 90, 250, 700, 875, 1050], "mortgage": 110
    },
    {"index": 22, "name": "Chance", "type": "chance"},
    {
        "index": 23, "name": "Indiana Avenue", "type": "property",
        "color": COLOR_RED, "price": 220, "house_cost": 150,
        "rents": [18, 90, 250, 700, 875, 1050], "mortgage": 110
    },
    {
        "index": 24, "name": "Illinois Avenue", "type": "property",
        "color": COLOR_RED, "price": 240, "house_cost": 150,
        "rents": [20, 100, 300, 750, 925, 1100], "mortgage": 120
    },
    {
        "index": 25, "name": "B. & O. Railroad", "type": "railroad",
        "price": 200, "mortgage": 100, "rents": [25, 50, 100, 200]
    },
    {
        "index": 26, "name": "Atlantic Avenue", "type": "property",
        "color": COLOR_YELLOW, "price": 260, "house_cost": 150,
        "rents": [22, 110, 330, 800, 975, 1150], "mortgage": 130
    },
    {
        "index": 27, "name": "Ventnor Avenue", "type": "property",
        "color": COLOR_YELLOW, "price": 260, "house_cost": 150,
        "rents": [22, 110, 330, 800, 975, 1150], "mortgage": 130
    },
    {
        "index": 28, "name": "Water Works", "type": "utility",
        "price": 150, "mortgage": 75, "multipliers": [4, 10]
    },
    {
        "index": 29, "name": "Marvin Gardens", "type": "property",
        "color": COLOR_YELLOW, "price": 280, "house_cost": 150,
        "rents": [24, 120, 360, 850, 1025, 1200], "mortgage": 140
    },
    {"index": 30, "name": "Go To Jail", "type": "corner", "sub_type": "go_to_jail"},

    # Right Row (31 - 39): Go To Jail -> Boardwalk
    {
        "index": 31, "name": "Pacific Avenue", "type": "property",
        "color": COLOR_GREEN, "price": 300, "house_cost": 200,
        "rents": [26, 130, 390, 900, 1100, 1275], "mortgage": 150
    },
    {
        "index": 32, "name": "North Carolina Avenue", "type": "property",
        "color": COLOR_GREEN, "price": 300, "house_cost": 200,
        "rents": [26, 130, 390, 900, 1100, 1275], "mortgage": 150
    },
    {"index": 33, "name": "Community Chest", "type": "community_chest"},
    {
        "index": 34, "name": "Pennsylvania Avenue", "type": "property",
        "color": COLOR_GREEN, "price": 320, "house_cost": 200,
        "rents": [28, 150, 450, 1000, 1200, 1400], "mortgage": 160
    },
    {
        "index": 35, "name": "Short Line Railroad", "type": "railroad",
        "price": 200, "mortgage": 100, "rents": [25, 50, 100, 200]
    },
    {"index": 36, "name": "Chance", "type": "chance"},
    {
        "index": 37, "name": "Park Place", "type": "property",
        "color": COLOR_DARK_BLUE, "price": 350, "house_cost": 200,
        "rents": [35, 175, 500, 1100, 1300, 1500], "mortgage": 175
    },
    {"index": 38, "name": "Luxury Tax", "type": "tax", "amount": 75, "percent": 0.0},
    {
        "index": 39, "name": "Boardwalk", "type": "property",
        "color": COLOR_DARK_BLUE, "price": 400, "house_cost": 200,
        "rents": [50, 200, 600, 1400, 1700, 2000], "mortgage": 200
    },
]

# Color Group Mapping (Color -> List of board indices)
COLOR_GROUPS: Dict[str, List[int]] = {
    COLOR_BROWN: [1, 3],
    COLOR_LIGHT_BLUE: [6, 8, 9],
    COLOR_PINK: [11, 13, 14],
    COLOR_ORANGE: [16, 18, 19],
    COLOR_RED: [21, 23, 24],
    COLOR_YELLOW: [26, 27, 29],
    COLOR_GREEN: [31, 32, 34],
    COLOR_DARK_BLUE: [37, 39],
}

RAILROAD_INDICES = [5, 15, 25, 35]
UTILITY_INDICES = [12, 28]

# Visual RGB Colors for Board Rendering
COLOR_RGB_MAP = {
    COLOR_BROWN: (149, 84, 54),
    COLOR_LIGHT_BLUE: (170, 224, 250),
    COLOR_PINK: (217, 58, 150),
    COLOR_ORANGE: (247, 148, 29),
    COLOR_RED: (237, 27, 36),
    COLOR_YELLOW: (254, 242, 0),
    COLOR_GREEN: (31, 166, 76),
    COLOR_DARK_BLUE: (0, 114, 187),
    GROUP_RAILROAD: (50, 50, 50),
    GROUP_UTILITY: (120, 120, 120),
}

# Standard Chance Cards Deck
CHANCE_CARDS = [
    {"id": "c1", "text": "Advance to GO (Collect $200)", "action": "advance_to", "target": 0},
    {"id": "c2", "text": "Advance to Illinois Ave. If you pass GO, collect $200", "action": "advance_to", "target": 24},
    {"id": "c3", "text": "Advance to St. Charles Place. If you pass GO, collect $200", "action": "advance_to", "target": 11},
    {"id": "c4", "text": "Advance token to nearest Utility. If unowned, you may buy it. If owned, pay owner 10 times dice roll.", "action": "advance_nearest_utility"},
    {"id": "c5", "text": "Advance token to nearest Railroad and pay owner twice the rental to which they are entitled. If unowned, buy it.", "action": "advance_nearest_railroad"},
    {"id": "c6", "text": "Bank pays you dividend of $50", "action": "collect_money", "amount": 50},
    {"id": "c7", "text": "Get Out of Jail Free card", "action": "jail_free"},
    {"id": "c8", "text": "Go Back 3 Spaces", "action": "move_relative", "spaces": -3},
    {"id": "c9", "text": "Go to Jail. Go directly to Jail. Do not pass GO, do not collect $200", "action": "go_to_jail"},
    {"id": "c10", "text": "Make general repairs on all your property: For each house pay $25, for each hotel pay $100", "action": "repairs", "house_cost": 25, "hotel_cost": 100},
    {"id": "c11", "text": "Pay poor tax of $15", "action": "pay_money", "amount": 15},
    {"id": "c12", "text": "Take a trip to Reading Railroad. If you pass GO, collect $200", "action": "advance_to", "target": 5},
    {"id": "c13", "text": "Take a walk on the Boardwalk. Advance token to Boardwalk", "action": "advance_to", "target": 39},
    {"id": "c14", "text": "You have been elected Chairman of the Board. Pay each player $50", "action": "pay_each_player", "amount": 50},
    {"id": "c15", "text": "Your building loan matures. Collect $150", "action": "collect_money", "amount": 150},
    {"id": "c16", "text": "You have won a crossword competition. Collect $100", "action": "collect_money", "amount": 100},
]

# Standard Community Chest Cards Deck
COMMUNITY_CHEST_CARDS = [
    {"id": "cc1", "text": "Advance to GO (Collect $200)", "action": "advance_to", "target": 0},
    {"id": "cc2", "text": "Bank error in your favor. Collect $200", "action": "collect_money", "amount": 200},
    {"id": "cc3", "text": "Doctor's fees. Pay $50", "action": "pay_money", "amount": 50},
    {"id": "cc4", "text": "From sale of stock you get $50", "action": "collect_money", "amount": 50},
    {"id": "cc5", "text": "Get Out of Jail Free card", "action": "jail_free"},
    {"id": "cc6", "text": "Go to Jail. Go directly to Jail. Do not pass GO, do not collect $200", "action": "go_to_jail"},
    {"id": "cc7", "text": "Grand Opera Night. Collect $50 from every player for opening night seats", "action": "collect_from_each", "amount": 50},
    {"id": "cc8", "text": "Holiday Fund matures. Receive $100", "action": "collect_money", "amount": 100},
    {"id": "cc9", "text": "Income tax refund. Collect $20", "action": "collect_money", "amount": 20},
    {"id": "cc10", "text": "It is your birthday. Collect $10 from every player", "action": "collect_from_each", "amount": 10},
    {"id": "cc11", "text": "Life insurance matures. Collect $100", "action": "collect_money", "amount": 100},
    {"id": "cc12", "text": "Hospital fees. Pay $50", "action": "pay_money", "amount": 50},
    {"id": "cc13", "text": "School fees. Pay $50", "action": "pay_money", "amount": 50},
    {"id": "cc14", "text": "Receive $25 consultancy fee", "action": "collect_money", "amount": 25},
    {"id": "cc15", "text": "You are assessed for street repairs: $40 per house, $115 per hotel", "action": "repairs", "house_cost": 40, "hotel_cost": 115},
    {"id": "cc16", "text": "You have won second prize in a beauty contest. Collect $10", "action": "collect_money", "amount": 10},
]
