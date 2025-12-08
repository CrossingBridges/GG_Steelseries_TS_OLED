"""
Registriert das 'SPEAKING' Event beim GameSense Handler (einmalig ausführen)
"""

import os
import json
import requests
from pathlib import Path


def get_gamesense_url() -> str:
    """
    Liest die GameSense URL aus der SteelSeries Engine 3 Config.
    """
    try:
        path = Path(os.environ["PROGRAMDATA"]) / "SteelSeries" / "SteelSeries Engine 3" / "coreProps.json"
        
        if not path.exists():
            raise FileNotFoundError(f"❌ coreProps.json nicht gefunden: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return f"http://{data['address']}"
    except Exception as e:
        print(f"❌ Fehler beim Auslesen von coreProps.json: {e}")
        raise


def bind_oled_handler():
    """
    Registriert das TeamSpeak SPEAKING Event beim GameSense Handler.
    Muss nur einmalig vor der ersten Nutzung ausgeführt werden.
    """
    try:
        base = get_gamesense_url()
        
        payload = {
            "game": "TEAMSPEAK",
            "event": "SPEAKING",
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
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(f"{base}/bind_game_event", json=payload, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ OLED Handler erfolgreich registriert!")
            return True
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Kann keine Verbindung zu SteelSeries Engine 3 herstellen!")
        print("   Stelle sicher, dass SteelSeries Engine 3 läuft.")
        return False
    except Exception as e:
        print(f"❌ Fehler beim Registrieren des OLED Handlers: {e}")
        return False


if __name__ == "__main__":
    print("🔧 Registriere TeamSpeak SPEAKING Event beim OLED...")
    success = bind_oled_handler()
    
    if success:
        print("\n✅ Setup erfolgreich! Du kannst jetzt ts_speakers_to_oled.py starten.")
    else:
        print("\n❌ Setup fehlgeschlagen. Bitte überprüfe deine SteelSeries Engine 3 Installation.")
    
    input("\nDrücke Enter zum Beenden...")
