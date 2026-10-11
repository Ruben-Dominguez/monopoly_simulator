"""
Monopoly Auction System.
Implements the official Hasbro Banker Auction when a player declines to purchase a property.
"""

from typing import List, Optional, Dict, Tuple
from .models import PropertyState, Player

class AuctionState:
    def __init__(self, property_state: PropertyState, players: List[Player]):
        self.property = property_state
        self.players = [p for p in players if not p.is_bankrupt]
        # Track which players are still participating in bidding
        self.active_bidder_ids: List[int] = [p.id for p in self.players]
        self.current_bid: int = 0
        self.highest_bidder_id: Optional[int] = None
        self.current_bidder_idx: int = 0
        self.is_completed: bool = False
        self.log_messages: List[str] = [
            f"Auction started for {self.property.name} (Valued at ${self.property.price})!"
        ]

    @property
    def current_bidder(self) -> Optional[Player]:
        if not self.active_bidder_ids or self.is_completed:
            return None
        current_id = self.active_bidder_ids[self.current_bidder_idx % len(self.active_bidder_ids)]
        for p in self.players:
            if p.id == current_id:
                return p
        return None

    def place_bid(self, player_id: int, bid_amount: int) -> Tuple[bool, str]:
        if self.is_completed:
            return False, "Auction already ended."
        if player_id not in self.active_bidder_ids:
            return False, "Player has already folded."
        if bid_amount <= self.current_bid:
            return False, f"Bid must be higher than current bid (${self.current_bid})."
        
        # Verify player can afford it
        player = next((p for p in self.players if p.id == player_id), None)
        if not player or player.cash < bid_amount:
            return False, "Player does not have enough cash."

        self.current_bid = bid_amount
        self.highest_bidder_id = player_id
        self.log_messages.append(f"{player.name} bid ${bid_amount}.")
        
        # Advance to next bidder
        self._advance_turn()
        self._check_completion()
        return True, "Bid placed successfully."

    def pass_bid(self, player_id: int):
        if player_id in self.active_bidder_ids:
            player = next((p for p in self.players if p.id == player_id), None)
            name = player.name if player else f"Player {player_id}"
            self.log_messages.append(f"{name} passed.")
            
            # Remove from active bidders
            idx = self.active_bidder_ids.index(player_id)
            self.active_bidder_ids.remove(player_id)
            if self.active_bidder_ids and idx <= self.current_bidder_idx:
                self.current_bidder_idx = self.current_bidder_idx % len(self.active_bidder_ids)
            
            self._check_completion()

    def _advance_turn(self):
        if self.active_bidder_ids:
            self.current_bidder_idx = (self.current_bidder_idx + 1) % len(self.active_bidder_ids)

    def _check_completion(self):
        # If only 1 active bidder remains and a bid was made, or 0 active bidders
        if len(self.active_bidder_ids) == 0:
            self.is_completed = True
        elif len(self.active_bidder_ids) == 1 and self.highest_bidder_id == self.active_bidder_ids[0]:
            self.is_completed = True
        elif len(self.active_bidder_ids) == 1 and self.highest_bidder_id is None:
            # The last player hasn't bid yet, give them an opportunity, but if they pass, ended.
            pass

    def conclude(self) -> Tuple[Optional[Player], int]:
        self.is_completed = True
        if self.highest_bidder_id is not None:
            winner = next((p for p in self.players if p.id == self.highest_bidder_id), None)
            return winner, self.current_bid
        return None, 0
