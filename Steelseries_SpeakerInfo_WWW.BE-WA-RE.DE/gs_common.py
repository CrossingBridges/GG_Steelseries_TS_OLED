"""
GameSense (SteelSeries OLED) - gemeinsame Funktionen
VERBESSERT: Korrekte Text-Formatierung für OLED Display
"""

import os
import json
import requests
from pathlib import Path

GAME = "TEAMSPEAK"
EVENT = "SPEAKING"


def get_gamesense_url() -> str:
    """
    Liest die GameSense URL aus der SteelSeries Engine 3 Config.
    
    Returns:
        str: Die GameSense API URL (z.B. http://127.0.0.1:55355)
    """
    try:
        path = Path(os.environ["PROGRAMDATA"]) / "SteelSeries" / "SteelSeries Engine 3" / "coreProps.json"
        
        if not path.exists():
            raise FileNotFoundError(f"❌ SteelSeries coreProps.json nicht gefunden: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        url = f"http://{data['address']}"
        return url
        
    except KeyError as e:
        raise KeyError(f"❌ coreProps.json hat kein 'address' Feld: {e}")


def send_text(text: str, debug: bool = False) -> bool:
    """
    Sendet Text an das SteelSeries OLED Display.
    
    WICHTIG: Das OLED zeigt die Daten als einfacher Text an.
    Zeilenumbrüche (\n) werden NICHT korrekt dargestellt.
    Stattdessen nutzen wir den Text direkt ohne spezielle Formatierung.
    
    Args:
        text (str): Der anzuzeigende Text (maximal ~30 Zeichen für gute Lesbarkeit)
        debug (bool): Debug-Ausgabe aktivieren
        
    Returns:
        bool: True wenn erfolgreich, False bei Fehler
    """
    try:
        base = get_gamesense_url()
        payload = {
            "game": GAME,
            "event": EVENT,
            "data": {
                "value": text
            }
        }
        
        response = requests.post(f"{base}/game_event", json=payload, timeout=2)
        
        if debug:
            print(f"  📡 GameSense: '{text}' → Status {response.status_code}")
        
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print(f"  ❌ GameSense: Verbindung fehlgeschlagen (SteelSeries Engine 3 läuft nicht?)")
        return False
    except Exception as e:
        print(f"  ❌ GameSense Fehler: {e}")
        return False
