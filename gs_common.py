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
    return f"http://{data['address']}"  # z.B. http://127.0.0.1:62086[web:9]

def send_text(text: str):
    """Text auf OLED anzeigen (nutzt deinen custom-text Handler)."""
    base = get_gamesense_url()
    payload = {
        "game": GAME,
        "event": EVENT,
        "data": {
            "value": 1,
            "frame": {
                "custom-text": text
            }
        }
    }
    r = requests.post(f"{base}/game_event", json=payload)
    print("GameSense:", text, "→", r.status_code, r.text)
