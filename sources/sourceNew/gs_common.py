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
    """Text auf OLED anzeigen (nutzt deinen custom-text Handler)."""
    base = get_gamesense_url()
    
    # ⭐ FIX: value=0 damit nicht der Wert angezeigt wird, sondern nur der Text!
    payload = {
        "game": GAME,
        "event": EVENT,
        "data": {
            "value": 0,  # 0 = nicht angezeigt, nur frame-Text wird genutzt
            "frame": {
                "custom-text": text
            }
        }
    }
    
    r = requests.post(f"{base}/game_event", json=payload)
    print("GameSense:", text, "→", r.status_code, r.text)