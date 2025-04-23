import asyncio
import random
import httpx

# Statyczna lista node'ów (statków)
NODES = [
    {"id": "black_pearl", "ip": "black_pearl", "port": 8000},
    {"id": "flying_dutchman", "ip": "flying_dutchman", "port": 8000},
    {"id": "queen_annes_revenge", "ip": "queen_annes_revenge", "port": 8000},
    {"id": "interceptor", "ip": "interceptor", "port": 8000},
    {"id": "endeavour", "ip": "endeavour", "port": 8000}
]

WAITING_FOR_LEADER = False

async def get_alive_nodes():
    alive = []
    async with httpx.AsyncClient() as client:
        for node in NODES:
            try:
                resp = await client.get(f"http://{node['ip']}:{node['port']}/status")
                if resp.status_code == 200:
                    data = resp.json()
                    if data["alive"]:
                        alive.append((node, data))
            except:
                continue
    return alive

async def get_current_leader():
    async with httpx.AsyncClient() as client:
        for node in NODES:
            try:
                resp = await client.get(f"http://{node['ip']}:{node['port']}/status")
                if resp.status_code == 200:
                    data = resp.json()
                    leader = data.get("current_leader")
                    if leader:
                        return leader
            except:
                continue
    return None

async def is_attack_mode_enabled():
    async with httpx.AsyncClient() as client:
        for node in NODES:
            try:
                r = await client.get(f"http://{node['ip']}:{node['port']}/status")
                if r.status_code == 200:
                    data = r.json()
                    if data.get("attack_mode") == "auto":
                        return True
            except:
                continue
    return False

async def wait_for_attack_mode():
    print("[Battle Controller] Waiting for attack mode to be set to 'auto'...")
    while True:
        enabled = await is_attack_mode_enabled()
        if enabled:
            print("[Battle Controller] Auto attack mode confirmed. Starting...")
            return
        await asyncio.sleep(2)

async def all_ships_destroyed():
    alive = await get_alive_nodes()
    return len(alive) == 0

async def attack_loop():
    global WAITING_FOR_LEADER

    await wait_for_attack_mode()

    while True:
        if WAITING_FOR_LEADER:
            print("[Battle Controller] Waiting for new leader...")
            await asyncio.sleep(2)
            leader = await get_current_leader()
            if leader:
                print(f"[Battle Controller] New leader is {leader}. Resuming attacks.")
                WAITING_FOR_LEADER = False
            continue

        alive = await get_alive_nodes()
        if not alive:
            print("[Battle Controller] All ships destroyed. Ending battle.")
            return

        target, status = random.choice(alive)
        print(f"[Battle Controller] Auto-attacking: {target['id']}")

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"http://{target['ip']}:{target['port']}/hit")
                if resp.status_code == 200 and status.get("leader"):
                    print(f"[Battle Controller] Leader {target['id']} destroyed! Pausing.")
                    WAITING_FOR_LEADER = True
        except:
            print(f"[Battle Controller] Failed to attack {target['id']}")

        await asyncio.sleep(6)

if __name__ == "__main__":
    asyncio.run(attack_loop())
