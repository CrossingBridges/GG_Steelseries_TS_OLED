import requests

from gs_common import get_gamesense_url, GAME, EVENT

BASE = get_gamesense_url()

# Handler mit length-millis: 0 - bleibt auf dem Screen bis zu neuem Event
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
                    "context-frame-key": "custom-text",
                    "length-millis": 0  # 0 = bleibt bis neues Event kommt (nicht 10 Sekunden!)
                }
            ]
        }
    ]
}

r = requests.post(f"{BASE}/bind_game_event", json=payload)
print("bind_game_event:", r.status_code, r.text)