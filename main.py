"""
Monopoly Simulator Entry Point.
Launches the full GUI application or executes high-speed headless simulations for statistical analysis.
"""

import sys
import argparse
import time
from monopoly.game import MonopolyGame
from monopoly.models import GamePhase

def run_headless_simulation(rounds: int, num_players: int, speed_die: bool):
    print(f"=== MONOPOLY HEADLESS SIMULATOR BENCHMARK ===")
    print(f"Running up to {rounds} rounds with {num_players} CPU players (Speed Die: {speed_die})...\n")

    configs = [
        {"name": f"CPU Bot {i+1}", "is_cpu": True, "color": (100, 100, 100), "token_name": f"T{i+1}"}
        for i in range(num_players)
    ]

    start_time = time.time()
    game = MonopolyGame(configs, use_speed_die=speed_die)

    turn = 0
    while game.phase != GamePhase.GAME_OVER and game.round_count <= rounds:
        game.step_cpu()
        turn += 1
        if turn % 200 == 0:
            print(f"Round {game.round_count}/{rounds} | Turns: {turn} | Active Players: {len(game.active_players)}")

    elapsed = time.time() - start_time
    print(f"\nSimulation finished in {elapsed:.3f} seconds ({turn} turns, {turn/max(0.001, elapsed):.1f} turns/sec).")
    
    if game.winner:
        print(f"WINNER: {game.winner.name} (Cash: ${game.winner.cash}, Properties: {len(game.winner.properties)})")
    else:
        print("Game reached round limit without complete elimination.")
        for p in game.players:
            print(f" - {p.name}: Cash ${p.cash}, Properties: {len(p.properties)}, Bankrupt: {p.is_bankrupt}")

def main():
    parser = argparse.ArgumentParser(description="Monopoly Simulator - Official Hasbro Rules")
    parser.add_argument("--headless", action="store_true", help="Run without GUI in high-speed simulation mode")
    parser.add_argument("--rounds", type=int, default=150, help="Maximum rounds for headless simulation")
    parser.add_argument("--players", type=int, default=4, help="Number of players (1-6)")
    parser.add_argument("--speed-die", action="store_true", help="Enable Hasbro Speed Die rules")
    args = parser.parse_args()

    if args.headless:
        run_headless_simulation(args.rounds, args.players, args.speed_die)
    else:
        # Launch Pygame GUI
        from gui_app import MonopolyApp
        app = MonopolyApp()
        app.run()

if __name__ == "__main__":
    main()
