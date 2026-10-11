"""
Comprehensive Automated Tests for Hasbro Monopoly Rules.
"""

import unittest
from monopoly.models import Player, PropertyState, SpaceType, Bank, BoardSpace, DiceRoll
from monopoly.rules import RulesEngine
from monopoly.game import MonopolyGame
from monopoly.auction import AuctionState

class TestMonopolyRules(unittest.TestCase):
    def setUp(self):
        self.player_configs = [
            {"name": "Alice", "is_cpu": False, "color": (255, 0, 0), "token_name": "Top Hat"},
            {"name": "Bob", "is_cpu": True, "color": (0, 0, 255), "token_name": "Battleship"},
        ]
        self.game = MonopolyGame(self.player_configs, use_speed_die=False)

    def test_initial_starting_conditions(self):
        self.assertEqual(len(self.game.players), 2)
        self.assertEqual(self.game.players[0].cash, 1500)
        self.assertEqual(self.game.bank.houses, 32)
        self.assertEqual(self.game.bank.hotels, 12)
        self.assertEqual(len(self.game.board), 40)

    def test_speed_die_starting_cash(self):
        speed_game = MonopolyGame(self.player_configs, use_speed_die=True)
        self.assertEqual(speed_game.players[0].cash, 2500)

    def test_railroad_rent_scaling(self):
        # 1 RR = 25, 2 RR = 50, 3 RR = 100, 4 RR = 200
        p1 = self.game.players[0]
        reading = self.game.properties[5]
        reading.owner_id = p1.id
        self.assertEqual(RulesEngine.calculate_rent(reading, self.game.properties, 7), 25)

        penn = self.game.properties[15]
        penn.owner_id = p1.id
        self.assertEqual(RulesEngine.calculate_rent(reading, self.game.properties, 7), 50)

        b_o = self.game.properties[25]
        b_o.owner_id = p1.id
        self.assertEqual(RulesEngine.calculate_rent(reading, self.game.properties, 7), 100)

        short_line = self.game.properties[35]
        short_line.owner_id = p1.id
        self.assertEqual(RulesEngine.calculate_rent(reading, self.game.properties, 7), 200)

    def test_utility_rent(self):
        p1 = self.game.players[0]
        electric = self.game.properties[12]
        electric.owner_id = p1.id
        # 1 utility: 4x roll
        self.assertEqual(RulesEngine.calculate_rent(electric, self.game.properties, 7), 28)

        water = self.game.properties[28]
        water.owner_id = p1.id
        # Both utilities: 10x roll
        self.assertEqual(RulesEngine.calculate_rent(electric, self.game.properties, 7), 70)

    def test_unimproved_monopoly_double_rent(self):
        p1 = self.game.players[0]
        boardwalk = self.game.properties[39]
        park_place = self.game.properties[37]

        boardwalk.owner_id = p1.id
        self.assertEqual(RulesEngine.calculate_rent(boardwalk, self.game.properties, 7), 50)

        park_place.owner_id = p1.id
        # Dark Blue complete set: unimproved rent doubles (Boardwalk 50 -> 100)
        self.assertEqual(RulesEngine.calculate_rent(boardwalk, self.game.properties, 7), 100)

    def test_even_building_rule(self):
        p1 = self.game.players[0]
        med = self.game.properties[1]
        baltic = self.game.properties[3]
        med.owner_id = p1.id
        baltic.owner_id = p1.id

        # Can build 1 house on Mediterranean
        can, _ = RulesEngine.can_build_house(med, self.game.properties, p1, self.game.bank)
        self.assertTrue(can)
        RulesEngine.build_house(med, self.game.properties, p1, self.game.bank)
        self.assertEqual(med.houses, 1)
        self.assertEqual(self.game.bank.houses, 31)

        # Cannot build 2nd house on Mediterranean until Baltic has 1 (even building!)
        can, msg = RulesEngine.can_build_house(med, self.game.properties, p1, self.game.bank)
        self.assertFalse(can)
        self.assertIn("evenly", msg)

        # Build 1 house on Baltic
        can, _ = RulesEngine.can_build_house(baltic, self.game.properties, p1, self.game.bank)
        self.assertTrue(can)
        RulesEngine.build_house(baltic, self.game.properties, p1, self.game.bank)
        self.assertEqual(baltic.houses, 1)

        # Now can build 2nd house on Mediterranean
        can, _ = RulesEngine.can_build_house(med, self.game.properties, p1, self.game.bank)
        self.assertTrue(can)

    def test_mortgage_and_unmortgage_with_10_percent_interest(self):
        p1 = self.game.players[0]
        boardwalk = self.game.properties[39]
        boardwalk.owner_id = p1.id
        p1.cash = 500

        # Mortgage Boardwalk (value = $200)
        can, _ = RulesEngine.can_mortgage(boardwalk, self.game.properties, p1)
        self.assertTrue(can)
        RulesEngine.mortgage_property(boardwalk, self.game.properties, p1)
        self.assertTrue(boardwalk.is_mortgaged)
        self.assertEqual(p1.cash, 700)
        # Mortgaged property collects 0 rent
        self.assertEqual(RulesEngine.calculate_rent(boardwalk, self.game.properties, 7), 0)

        # Unmortgage requires mortgage + 10% interest ($200 + $20 = $220)
        can, _ = RulesEngine.can_unmortgage(boardwalk, p1)
        self.assertTrue(can)
        RulesEngine.unmortgage_property(boardwalk, p1)
        self.assertFalse(boardwalk.is_mortgaged)
        self.assertEqual(p1.cash, 700 - 220)

    def test_bank_housing_shortage(self):
        p1 = self.game.players[0]
        med = self.game.properties[1]
        baltic = self.game.properties[3]
        med.owner_id = p1.id
        baltic.owner_id = p1.id

        # Empty bank houses
        self.game.bank.houses = 0
        can, msg = RulesEngine.can_build_house(med, self.game.properties, p1, self.game.bank)
        self.assertFalse(can)
        self.assertIn("shortage", msg.lower())

    def test_auction_flow(self):
        prop = self.game.properties[1]
        auction = AuctionState(prop, self.game.players)
        self.assertEqual(auction.current_bid, 0)
        self.assertFalse(auction.is_completed)

        # Alice bids $10
        success, _ = auction.place_bid(0, 10)
        self.assertTrue(success)
        self.assertEqual(auction.current_bid, 10)
        self.assertEqual(auction.highest_bidder_id, 0)

        # Bob passes
        auction.pass_bid(1)
        self.assertTrue(auction.is_completed)

        winner, amount = auction.conclude()
        self.assertEqual(winner.id, 0)
        self.assertEqual(amount, 10)

if __name__ == "__main__":
    unittest.main()
