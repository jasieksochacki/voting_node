import os

class VotingSystem:
    def __init__(self):
        self.node_id = os.getenv("NODE_ID", "default-node")
        self.votes = {}
        self.points = {}
        self.voted_nodes = set()

    def set_points(self, node_id: str, points: int):
        self.points[node_id] = points

    def cast_vote(self, voter: str, candidate: str) -> bool:
        if voter in self.voted_nodes:
            return False  # już głosował
        self.votes[voter] = candidate
        self.voted_nodes.add(voter)
        return True

    def determine_leader(self) -> str:
        # Tylko głosy od węzłów, które mają status (punktacja)
        score_map = {}
        for vote in self.votes.values():
            if vote in self.points:
                score_map[vote] = score_map.get(vote, 0) + self.points[vote]
        if not score_map:
            return "Brak"
        return max(score_map, key=score_map.get)

    def reset_votes(self):
        self.votes = {}
        self.voted_nodes = set()
