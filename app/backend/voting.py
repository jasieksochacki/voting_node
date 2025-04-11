import os
import requests
from datetime import datetime
from models import NodeVote

class VotingSystem:
    def __init__(self):
        self.node_id = os.getenv("NODE_ID", "unknown-node")
        self.peers = os.getenv("PEERS", "").split(",")
        self.votes = {}  # voter -> candidate
        self.last_seen = {peer: datetime.utcnow() for peer in self.peers}

    def broadcast_vote(self, candidate):
        vote = NodeVote(voter=self.node_id, candidate=candidate)
        print(f"[{self.node_id}] Głosuję na: {candidate}")
        for peer in self.peers:
            try:
                url = f"http://{peer}/receive-vote"
                requests.post(url, json=vote.dict(), timeout=1)
            except:
                print(f"[{self.node_id}] Nie mogę wysłać do {peer}")
        self.votes[self.node_id] = candidate

    def receive_vote(self, vote: NodeVote):
        self.votes[vote.voter] = vote.candidate
        print(f"[{self.node_id}] Otrzymałem głos: {vote.voter} ➞ {vote.candidate}")

    def determine_leader(self):
        count = {}
        for candidate in self.votes.values():
            count[candidate] = count.get(candidate, 0) + 1

        if not count:
            return []

        max_votes = max(count.values())
        leaders = [candidate for candidate, votes in count.items() if votes == max_votes]

        return leaders

    def check_peers(self):
        now = datetime.utcnow()
        for peer in self.peers:
            try:
                r = requests.get(f"http://{peer}/health", timeout=1)
                if r.status_code == 200:
                    self.last_seen[peer] = now
            except:
                print(f"[{self.node_id}] Peer {peer} niedostępny!")

    def should_trigger_election(self, max_seconds=15):
        now = datetime.utcnow()
        for peer, last_time in self.last_seen.items():
            delta = (now - last_time).total_seconds()
            if delta > max_seconds:
                print(f"[{self.node_id}] Wykryto brak odpowiedzi od {peer} ({int(delta)}s)")
                return True
        return False
