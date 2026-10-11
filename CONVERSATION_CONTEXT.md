# 📜 Project Context & Full Conversation History

This document summarizes the entire context, design decisions, architectural implementation, and conversation history for the **Monopoly Simulator** project. When opening this repository in **Antigravity IDE**, feed or `@mention` this file to give the assistant complete memory and context.

---

## 🎯 Project Overview & Original Prompt

### User Request
> *"Act as an indie game dev, i want to create a monopoly simulator in python, i want it to have a visual interface that can speed up with a press of a button, it will have the option to choose between 1-6 players or CPUs. it should contain a gui that has all the rules stated in this panflet: https://www.hasbro.com/common/instruct/00009.pdf."*

### Key Requirements Delivered
1. **Official Hasbro Rules Engine**: Faithful implementation of Hasbro's official rulebook ([00009.pdf](https://www.hasbro.com/common/instruct/00009.pdf)).
2. **Visual Pygame GUI**: 2D Atlantic City board with color deeds, house/hotel indicators, token badges, live HUD, activity feed, and interactive modals.
3. **One-Click Speed Up Controls**: Real-time simulation speed bar (`PAUSE`, `1x`, `2x`, `5x`, `20x`, `MAX` / Turbo, `STEP`).
4. **1 to 6 Players / CPUs**: Setup menu allowing any combination of Human and CPU bots (e.g. 1 human vs 3 bots, or 6 bots running headless).
5. **Dual Modes**: Both Classic Monopoly and Hasbro Speed Die Mode.
6. **Dual Launchers**: Graphical GUI (`python main.py`) + High-speed Headless Benchmark (`python main.py --headless` at >70,000 turns/sec).
7. **Git & GitHub Integration**: Repository initialized, committed, and published to `https://github.com/Ruben-Dominguez/monopoly_simulator`.

---

## 🏗️ Architecture & Codebase Map

```
monopoly_simulator/
├── monopoly/
│   ├── board_data.py       # All 40 spaces, prices, mortgages, rents, Chance & Community Chest cards
│   ├── models.py           # Domain models: Player, PropertyState, Bank, DiceRoll, Card, GamePhase
│   ├── rules.py            # RulesEngine: rent calculations, monopolies, even building, mortgages, bankruptcy
│   ├── speed_die.py        # Official Hasbro Speed Die rules (1-3 add, Bus choice, Mr. Monopoly, Triples)
│   ├── auction.py          # Interactive Banker Auction system when purchase is declined
│   ├── ai.py               # Strategic CPU AI: valuation heuristics, bidding, building, debt liquidation
│   ├── game.py             # MonopolyGame turn orchestrator and state machine
│   └── renderer.py         # Pygame 2D board rendering, tokens, houses, hotels, dice, HUD
├── gui_app.py              # Visual interface, game setup, speed controls, modals (Deeds, Taxes, Auctions)
├── main.py                 # CLI & GUI launcher entry point (supports --headless and --speed-die)
├── tests/
│   └── test_rules.py       # 9 automated unit tests verifying Hasbro rules compliance
├── .gitignore              # Standard Python ignore rules
├── README.md               # User documentation
└── CONVERSATION_CONTEXT.md # This complete context dossier
```

---

## 📜 Hasbro Official Rules Details Implemented

- **Bank Supply Limits**: Strictly enforced **32 Houses** and **12 Hotels**. If the bank has no houses left, building shortages apply.
- **Even Building & Selling**: Houses must be built evenly across monopolies (cannot build 2nd house until all properties in group have 1). Selling buildings back to Bank yields 50% face value, broken down evenly.
- **Banker Auctions**: When a player declines to buy an unowned space at printed price, the Banker puts it up for auction to all players.
- **Income Tax Option**: Choice between paying flat **$200** or **10% of total worth** (cash + printed property prices + building costs).
- **Jail Rules**:
  - Sent to Jail via: "Go to Jail" space, Chance/Community Chest card, or rolling doubles 3 times in a row.
  - Escaping: doubles within 3 turns, paying $50 before rolling on turn 1 or 2, paying $50 on turn 3 if doubles failed, or "Get Out of Jail Free" card.
  - In Jail: player continues collecting rent, trading, and building.
- **Free Parking**: Pure resting place (no jackpot money pot per Hasbro rules).
- **Mortgages & Transfers**: Unimproved properties only. Unmortgaging costs mortgage value + 10% interest. Transferred mortgaged properties require 10% fee immediately upon receipt.
- **Speed Die Mode (Pages 1–2)**:
  - $2,500 starting cash ($1,000 extra).
  - Activates after player passes or lands on GO for the first time.
  - White dice determine doubles.
  - Speed Die rolls: 1, 2, 3 (added to roll); Bus (choose die 1, die 2, or sum); Mr. Monopoly (advance to next unowned property or next rent property); Triples (teleport anywhere on board).

---

## 💻 Tech Stack & Environment

- **OS**: Windows 11 (PowerShell)
- **Python**: 3.14.6
- **GUI Engine**: `pygame-ce` 2.5.8
- **GitHub Repo**: [https://github.com/Ruben-Dominguez/monopoly_simulator](https://github.com/Ruben-Dominguez/monopoly_simulator)
- **Local Path**: `C:\Users\ruben\OneDrive\Desktop\projects\monopoly_simulator`

---

## 💬 Conversation Trajectory Summary

1. **User Request**: Create an indie-dev style Monopoly simulator in Python with a visual GUI, speed-up button, 1-6 players/CPUs, and full Hasbro pamphlet rules.
2. **Engine Implementation**:
   - Analyzed official Hasbro PDF `00009.pdf`.
   - Built pure Python game engine (`monopoly/`), automated unit tests (`tests/test_rules.py`), visual GUI (`gui_app.py`), and CLI launcher (`main.py`).
   - Verified that headless simulation processes >70,000 turns/sec.
3. **GitHub Setup**:
   - Initialized Git repository, configured `.gitignore`, and made initial commit.
   - Installed GitHub CLI (`gh`) via `winget`.
   - Completed device login for `Ruben-Dominguez` via web device flow (`A56A-8224`).
   - Created public repository `monopoly_simulator` on GitHub and pushed `main` branch.
4. **Transition to Antigravity IDE**:
   - User noted the desktop interface differed from their experience on macOS.
   - Clarified distinction between Antigravity 2.0 (Desktop App) and Antigravity IDE (VS Code based).
   - Created this context document to ensure zero context loss when opening the project in Antigravity IDE.

---

## 🚀 Suggested Next Steps for the LLM in Antigravity IDE

If continuing development in Antigravity IDE, here are high-impact additions ready to be built:
1. **Interactive Trading System**: Allow human and AI players to propose and negotiate property/cash trades.
2. **AI Personalities**: Introduce distinct CPU archetypes (e.g. *Aggressive Developer*, *Cautious Investor*, *Railroad Collector*).
3. **Heatmap & Probability Overlay**: Add a visual toggle showing landing probabilities and expected rent yields per board space over 1,000+ simulation turns.
