from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from voting import VotingSystem

app = FastAPI()
voting = VotingSystem()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lub podaj konkretny frontend jeśli trzeba
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VoteRequest(BaseModel):
    voter: str
    candidate: str

class PointRequest(BaseModel):
    node_id: str
    points: int

@app.get("/leader")
def get_leader():
    return {"leader": voting.determine_leader()}

@app.post("/vote")
def vote(request: VoteRequest):
    result = voting.cast_vote(request.voter, request.candidate)
    if not result:
        return {"error": "Vote rejected or already voted"}
    return {"message": "Vote accepted"}

@app.post("/set-points")
def set_points(request: PointRequest):
    voting.set_points(request.node_id, request.points)
    return {"message": "Points updated"}

@app.post("/reset")
def reset_votes():
    voting.reset_votes()
    return {"message": "Votes reset"}
