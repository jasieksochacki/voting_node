import os
import time
import threading
import random
from fastapi import FastAPI
from models import NodeVote
from voting import VotingSystem

app = FastAPI()
voting = VotingSystem()

@app.post("/receive-vote")
def receive_vote(vote: NodeVote):
    voting.receive_vote(vote)
    return {"message": "Głos odebrany"}

@app.post("/init-vote")
def init_vote(candidate: str):
    voting.broadcast_vote(candidate)
    return {"status": "Głosowanie zakończone", "voter": voting.node_id}

@app.get("/leader")
def get_leader():
    leaders = voting.determine_leader()
    return {"leaders": leaders}


@app.get("/votes")
def all_votes():
    return voting.votes

@app.get("/node-info")
def node_info():
    return {
        "node_id": os.getenv("NODE_ID", "default-node"),
        "status": "online"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

def auto_monitor_loop():
    while True:
        time.sleep(10)
        voting.check_peers()
        if voting.should_trigger_election():
            print(f"[{voting.node_id}] Automatyczne głosowanie z powodu awarii")
            candidate = random.choice([voting.node_id] + voting.peers)
            voting.broadcast_vote(candidate)

threading.Thread(target=auto_monitor_loop, daemon=True).start()