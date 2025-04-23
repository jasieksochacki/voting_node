from pydantic import BaseModel

class VoteRequest(BaseModel):
    candidate: str

class NodeVote(BaseModel):
    voter: str
    candidate: str