# 🎩 Monopoly Simulator (Official Hasbro Rules & Speed Die)

A high-performance, visual Monopoly Simulator written in Python with Pygame, faithfully adhering to the official Hasbro rulebook ([Hasbro Rule Pamphlet 00009.pdf](https://www.hasbro.com/common/instruct/00009.pdf)).

---

## 🌟 Key Features

1. **Official Hasbro Rules Engine**:
   - **Classic Atlantic City Board**: All 40 spaces, complete color sets, 4 railroads with tiered rent, 2 utilities with dice multipliers, and exact card decks (Chance & Community Chest).
   - **Bank Supply Limits**: Strictly enforced **32 Houses** and **12 Hotels** with housing shortages.
   - **Even Building Rule**: Houses must be built and sold evenly across complete monopolies.
   - **Banker Auctions**: If a player declines to buy an unowned property at printed price, the Banker immediately auctions it to the highest bidder among all players.
   - **Official Income Tax**: Choose between flat $200 or 10% of total net worth (calculated from cash, properties, and buildings).
   - **Official Jail Mechanics**: Escaping via doubles within 3 turns, paying $50 before rolling on turn 1 or 2, paying $50 on turn 3, or using a "Get Out of Jail Free" card. Rent and trading remain active while in Jail.
   - **Free Parking**: Official rule honored (strictly a resting spot, no money jackpot).
   - **Mortgages**: Unimproved properties only; unmortgaging costs mortgage + 10% interest. Transferred mortgaged properties require 10% fee immediately upon receipt.
   - **Bankruptcy & Debt Resolution**: Liquidating houses back to the bank for 50%, mortgaging, or surrendering assets to creditor / bank auction.

2. **Hasbro Speed Die Mode (Pages 1–2 of Pamphlet)**:
   - Hand out an extra **$1,000** to each player at start ($2,500 total).
   - Speed Die activates after a player lands on or passes GO for the first time.
   - **1, 2, or 3**: Added directly to the white dice roll.
   - **Bus**: "Get off the bus early" — choose to move die 1, die 2, or both dice.
   - **Mr. Monopoly**: Move white dice roll first, then advance to the next unowned bank property (or next property owing rent if bank has none).
   - **Triples (Three-of-a-Kind)**: Teleport to any space on the board.
   - Utility rent sums all three dice.

3. **Dynamic Visual Interface (Pygame)**:
   - Crisp 720x720 2D board with property color bars, house/hotel indicators, token badges, and animated dice.
   - **Speed Control Bar**: Speed up or slow down at any moment with a single click:
     - `PAUSE`
     - `1x` (Normal speed)
     - `2x` (Fast)
     - `5x` (Very Fast)
     - `20x` (High Speed)
     - `MAX` (Instant Simulation)
     - `STEP` (Single-action manual stepping)
   - **Interactive HUD & Modals**:
     - Player setup menu (1–6 players, Human vs CPU toggles, custom tokens).
     - Live Player Roster with cash, net worth, jail status, and deeds.
     - Interactive Property Management modal (build houses, sell buildings, mortgage/unmortgage).
     - Interactive Auction bidding panel.
     - Live scrolling game activity log.

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+ (Tested up to Python 3.14.6)
- `pygame-ce` (installed via pip)

```bash
pip install pygame-ce
```

### 2. Launch the Visual GUI Simulator

```bash
python main.py
```

### 3. Run Headless Benchmarking Mode

Want to test strategies across thousands of turns in fractions of a second? Run headless:

```bash
# Run 100 rounds with 4 CPU bots (Classic Mode)
python main.py --headless --rounds 100 --players 4

# Run 100 rounds with Speed Die rules
python main.py --headless --rounds 100 --players 4 --speed-die
```

### 4. Run the Rules Test Suite

Verify all Hasbro rules via automated unit tests:

```bash
python -m unittest discover -s tests
```

---

## 📁 Architecture Overview

```
monopoly_simulator/
├── monopoly/
│   ├── board_data.py       # 40 board spaces, deed stats, Chance & Community Chest cards
│   ├── models.py           # Pure domain models (Player, PropertyState, Bank, DiceRoll, Card)
│   ├── rules.py            # Hasbro rules validation & calculations (rents, even building, mortgages)
│   ├── speed_die.py        # Speed Die dice handler and rules
│   ├── auction.py          # Interactive banker auction engine
│   ├── ai.py               # Strategic CPU AI (evaluations, bidding, building, debt management)
│   ├── game.py             # Core turn state machine and game orchestrator
│   └── renderer.py         # 2D board rendering, token badges, houses, dice, and center HUD
├── gui_app.py              # Visual UI, modals, setup screen, and speed controllers
├── main.py                 # CLI & GUI launcher entry point
├── tests/
│   └── test_rules.py       # Automated unit test suite
└── README.md
```
