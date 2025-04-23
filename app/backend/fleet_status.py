import asyncio
import httpx

NODES = [
    {"id": "black_pearl", "ip": "localhost", "port": 8000},
    {"id": "flying_dutchman", "ip": "localhost", "port": 8001},
    {"id": "queen_annes_revenge", "ip": "localhost", "port": 8002},
    {"id": "interceptor", "ip": "localhost", "port": 8003},
    {"id": "endeavour", "ip": "localhost", "port": 8004},
]

async def fetch_status(node):
    try:
        async with httpx.AsyncClient() as client:
            status_resp = await client.get(f"http://{node['ip']}:{node['port']}/status")
            leader_resp = await client.get(f"http://{node['ip']}:{node['port']}/current_leader")

            status_data = status_resp.json()
            leader_id = leader_resp.json().get("current_leader", None)

            return {
                "id": node["id"],
                "alive": status_data.get("alive", False),
                "battle_points": status_data.get("battle_points", 0),
                "current_leader": leader_id,
                "voted_for": status_data.get("voted_for", "N/A")
            }
    except:
        return {
            "id": node["id"],
            "alive": False,
            "battle_points": 0,
            "current_leader": None,
            "voted_for": "N/A"
        }

async def check_fleet_status():
    while True:
        print("\n[+] Checking Fleet Status:")
        statuses = await asyncio.gather(*(fetch_status(n) for n in NODES))
        alive_nodes = [s for s in statuses if s["alive"]]
        leader_id = next((s["current_leader"] for s in alive_nodes if s["current_leader"]), None)

        if not alive_nodes:
            print("❌ All ships are dead. Exiting monitor.")
            break

        print("🗳️  Voting Summary:")
        for s in statuses:
            if s["alive"] and s["voted_for"] != "N/A":
                print(f" - {s['id']} voted for {s['voted_for']}")

        for s in statuses:
            label = "[Dead]"
            if s["alive"]:
                label = "[Alive]"
                if s["id"] == leader_id:
                    label += " (Captain)"
            print(f" - {s['id']} {label} (Points: {s['battle_points']})")

        if not leader_id:
            print(" [!] No current leader known – election may be in progress.")

        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(check_fleet_status())
