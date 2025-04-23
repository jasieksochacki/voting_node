import os
import json
import random
import asyncio
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NODE_ID = os.getenv("NODE_ID")
NODE_PORT = int(os.getenv("NODE_PORT"))
IS_BATTLE_CONTROLLER = os.getenv("IS_BATTLE_CONTROLLER", "false").lower() == "true"

NODES = []
ALIVE = True
current_leader = None
BATTLE_POINTS = 0
VOTE_MODE = "auto"
ATTACK_MODE = "none"
VOTED = False
VOTES_CAST = {}
WAITING_FOR_NEW_LEADER = False

@app.on_event("startup")
async def startup_event():
    global NODES, BATTLE_POINTS
    with open('statuses.json', 'r') as f:
        NODES = json.load(f)
    for node in NODES:
        if node["id"] == NODE_ID:
            BATTLE_POINTS = node["battle_points"]
            break
    print(f"[{NODE_ID}] Ready on port {NODE_PORT} with {BATTLE_POINTS} points")
    if IS_BATTLE_CONTROLLER:
        print(f"[{NODE_ID}] Acting as Battle Controller")

@app.get("/status")
async def status():
    return {
        "id": NODE_ID,
        "alive": ALIVE,
        "leader": current_leader,
        "battle_points": BATTLE_POINTS,
        "vote_mode": VOTE_MODE,
        "attack_mode": ATTACK_MODE,
        "voted": VOTED,
        "votes_cast": VOTES_CAST,
        "is_battle_controller": IS_BATTLE_CONTROLLER,
        "current_leader": current_leader
    }

@app.post("/set_vote_mode")
async def set_vote_mode(request: Request):
    global VOTE_MODE
    data = await request.json()
    VOTE_MODE = data.get("mode", "auto")
    print(f"[{NODE_ID}] Vote mode set to {VOTE_MODE}")
    if VOTE_MODE == "auto":
        asyncio.create_task(auto_vote())
    return {"message": f"Vote mode set to {VOTE_MODE}"}

@app.post("/set_attack_mode")
async def set_attack_mode(request: Request):
    global ATTACK_MODE
    data = await request.json()
    ATTACK_MODE = data.get("mode", "none")
    print(f"[{NODE_ID}] Attack mode set to {ATTACK_MODE}")
    if ATTACK_MODE == "auto" and IS_BATTLE_CONTROLLER:
        print(f"[{NODE_ID}] Starting auto attack loop")
        asyncio.create_task(auto_attack_loop())
    return {"message": f"Attack mode set to {ATTACK_MODE}"}

@app.post("/vote_for")
async def vote_for(request: Request):
    global VOTED, VOTES_CAST
    if not ALIVE or VOTED:
        return {"message": "Already voted or dead"}
    data = await request.json()
    target = data.get("target_id")
    VOTES_CAST[NODE_ID] = target
    VOTED = True
    print(f"[{NODE_ID}] Voted for {target}")
    await check_election_result()
    return {"message": f"Voted for {target}"}

async def auto_vote():
    global VOTED, VOTES_CAST
    if not ALIVE or VOTED:
        return
    try:
        alive = []
        async with httpx.AsyncClient() as client:
            for node in NODES:
                try:
                    r = await client.get(f"http://{node['ip']}:{node['port']}/status")
                    if r.status_code == 200:
                        d = r.json()
                        if d["alive"]:
                            alive.append(d)
                except:
                    continue
        if not alive:
            return
        max_pts = max(n["battle_points"] for n in alive)
        best = [n for n in alive if n["battle_points"] == max_pts]
        chosen = sorted(best, key=lambda x: x["id"])[0]
        async with httpx.AsyncClient() as client:
            await client.post(f"http://{NODE_ID}:{NODE_PORT}/vote_for", json={"target_id": chosen["id"]})
    except:
        pass

async def check_election_result():
    global current_leader, WAITING_FOR_NEW_LEADER
    try:
        votes = {}
        alive_ids = []
        total_votes = 0
        async with httpx.AsyncClient() as client:
            for node in NODES:
                try:
                    r = await client.get(f"http://{node['ip']}:{node['port']}/status")
                    if r.status_code == 200:
                        data = r.json()
                        if data.get("alive"):
                            alive_ids.append(data["id"])
                            for _, t in data.get("votes_cast", {}).items():
                                votes[t] = votes.get(t, 0) + 1
                                total_votes += 1
                except:
                    continue
        if total_votes < len(alive_ids):
            print(f"[{NODE_ID}] Waiting for all votes: {total_votes}/{len(alive_ids)}")
            return

        max_votes = max(votes.values())
        top = [k for k, v in votes.items() if v == max_votes]
        leader_id = sorted(top)[0]
        current_leader = leader_id
        print(f"[{NODE_ID}] New leader elected: {leader_id}")
        async with httpx.AsyncClient() as client:
            for node in NODES:
                try:
                    await client.post(f"http://{node['ip']}:{node['port']}/set_leader", json={"leader_id": leader_id})
                except:
                    continue
        WAITING_FOR_NEW_LEADER = False
    except:
        pass

@app.post("/set_leader")
async def set_leader(request: Request):
    global current_leader
    data = await request.json()
    current_leader = data.get("leader_id")
    print(f"[{NODE_ID}] Leader set to {current_leader}")
    return {"message": "Leader updated"}

@app.post("/hit")
async def hit():
    global ALIVE, current_leader, VOTED, VOTES_CAST, WAITING_FOR_NEW_LEADER
    if ALIVE:
        ALIVE = False
        was_leader = current_leader == NODE_ID
        current_leader = None
        VOTED = False
        VOTES_CAST = {}
        print(f"[{NODE_ID}] Hit! Destroyed.")
        if was_leader:
            WAITING_FOR_NEW_LEADER = True
            asyncio.create_task(trigger_re_election())
    return {"message": "Hit confirmed"}

@app.post("/reset_vote")
async def reset_vote():
    global VOTED, VOTES_CAST, current_leader
    if not ALIVE:
        return {"message": "Dead node"}
    VOTED = False
    VOTES_CAST = {}
    current_leader = None
    if VOTE_MODE == "auto":
        asyncio.create_task(auto_vote())
    return {"message": "Vote reset"}

async def trigger_re_election():
    await asyncio.sleep(2)
    async with httpx.AsyncClient() as client:
        for node in NODES:
            try:
                await client.post(f"http://{node['ip']}:{node['port']}/reset_vote")
            except:
                continue
    await asyncio.sleep(5)
    await check_election_result()

async def get_current_leader():
    async with httpx.AsyncClient() as client:
        for node in NODES:
            try:
                r = await client.get(f"http://{node['ip']}:{node['port']}/status")
                if r.status_code == 200:
                    data = r.json()
                    if data.get("current_leader"):
                        return data["current_leader"]
            except:
                continue
    return None

async def auto_attack_loop():
    global WAITING_FOR_NEW_LEADER
    await asyncio.sleep(2)
    while ATTACK_MODE == "auto":
        if not IS_BATTLE_CONTROLLER:
            await asyncio.sleep(2)
            continue
        if WAITING_FOR_NEW_LEADER:
            print(f"[{NODE_ID}] Waiting for new leader...")
            await asyncio.sleep(2)
            leader = await get_current_leader()
            if leader:
                print(f"[{NODE_ID}] New leader is {leader}. Resuming attack.")
                WAITING_FOR_NEW_LEADER = False
            continue

        await asyncio.sleep(6)

        alive_nodes = []
        async with httpx.AsyncClient() as client:
            for node in NODES:
                if node["id"] == NODE_ID:
                    continue
                try:
                    r = await client.get(f"http://{node['ip']}:{node['port']}/status")
                    if r.status_code == 200 and r.json().get("alive"):
                        alive_nodes.append((node, r.json()))
                except:
                    continue

        if not alive_nodes:
            print(f"[{NODE_ID}] No targets found. Waiting...")
            await asyncio.sleep(3)
            continue

        target, data = random.choice(alive_nodes)
        print(f"[{NODE_ID}] Auto-attacking: {target['id']}")
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"http://{target['ip']}:{target['port']}/hit")
        except:
            print(f"[{NODE_ID}] Attack failed.")

        if data.get("leader"):
            print(f"[{NODE_ID}] Leader {target['id']} destroyed!")
            WAITING_FOR_NEW_LEADER = True
