import os, json, requests

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

BASE = get_gamesense_url()
GAME = "TEAMSPEAK"
EVENT = "SPEAKING"

payload = {
    "game": GAME,
    "event": EVENT,
    "min_value": 0,
    "max_value": 100,
    "icon_id": 13,
    "value_optional": True,
    "handlers": [
        {
            "device-type": "screened",
            "mode": "screen",
            "zone": "one",
            "datas": [
                {
                    "has-text": True
                    # kein context-frame-key → GG nimmt "Eventwert"[web:3]
                }
            ]
        }
    ]
}

r = requests.post(f"{BASE}/bind_game_event", json=payload)
print("bind_game_event:", r.status_code, r.text)
