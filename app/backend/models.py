from pydantic import BaseModel

class NodeVote(BaseModel):
    voter: str
    candidate: str

