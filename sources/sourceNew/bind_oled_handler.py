import requests
from gs_common import get_gamesense_url

BASE = get_gamesense_url()
GAME = "TEAMSPEAK"
EVENT = "SPEAKING"

def send_text(text: str):
    payload = {
        "game": GAME,
        "event": EVENT,
        "data": {
            "value": 1,             # beliebiger int, wird nur fürs Keepalive genutzt[web:9]
            "frame": {
                "custom-text": text # wird vom Handler als Text angezeigt[web:3]
            }
        }
    }
    r = requests.post(f"{BASE}/game_event", json=payload)
    print("game_event:", text, "→", r.status_code, r.text)

if __name__ == "__main__":
    while True:
        name = input("Text fürs OLED (q = Quit): ")
        if name.lower() == "q":
            break
        send_text(name)
