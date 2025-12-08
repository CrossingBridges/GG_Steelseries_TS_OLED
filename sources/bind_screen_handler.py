import requests
from gs_common import get_gamesense_url, GAME, EVENT

BASE = get_gamesense_url()

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
                    "has-text": True,
                    "context-frame-key": "custom-text"
                }
            ]
        }
    ]
}

r = requests.post(f"{BASE}/bind_game_event", json=payload)
print("bind_game_event:", r.status_code, r.text)
