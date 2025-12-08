import os
import json
import requests

GAME = "TEAMSPEAK"
EVENT = "SPEAKING"

def get_gamesense_url():
    path = os.path.join(
        os.environ["PROGRAMDATA"],
        "SteelSeries",
        "SteelSeries Engine 3",
        "coreProps.json",
    )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return f"http://{data['address']}"

def send_text(text: str):
    base = get_gamesense_url()
    payload = {
        "game": GAME,
        "event": EVENT,
        "data": {
            "value": text     # ← NUR das, keine frame
        }
    }
    r = requests.post(f"{base}/game_event", json=payload)
    print("GameSense:", text, "→", r.status_code, r.text)

