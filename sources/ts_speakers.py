"""
TeamSpeak 3 → OLED Display - FIXED VERSION
VERSION 5.0 - MIT CLID SUPPORT (NICHT client_id)

Das Problem war: TeamSpeak gibt "clid=" zurück, nicht "client_id="
Jetzt parsen wir richtig!
"""

import socket
import time
import configparser
import re
from typing import Dict, Tuple
from gs_common import send_text

config = configparser.ConfigParser()
config.read("config.ini")

TS_HOST = config.get("TeamSpeak", "host", fallback="localhost")
TS_PORT = config.getint("TeamSpeak", "port", fallback=25639)
TS_API_KEY = config.get("TeamSpeak", "api_key")
POLL_INTERVAL = config.getfloat("Settings", "poll_interval", fallback=0.1)
MAX_SPEAKERS = config.getint("Settings", "max_speakers", fallback=4)
NICK_LENGTH = config.getint("Settings", "nick_length", fallback=10)
DEBUG = config.getboolean("Settings", "debug", fallback=False)
DEBOUNCE_TIME = config.getfloat("Settings", "debounce_time", fallback=0.1)

print(f"\n✅ Config: {TS_HOST}:{TS_PORT} | Poll: {POLL_INTERVAL}s")

def format_nick(raw: str) -> str:
    """Formatiert Nicknames."""
    if not raw:
        return ""
    s = raw.strip().replace("\\s", " ").replace("\\\\", "\\")
    if "(" in s:
        s = s[:s.find("(")].strip()
    if len(s) > NICK_LENGTH:
        s = s[:NICK_LENGTH]
    return s

def parse_speakers(text: str) -> Dict[int, str]:
    """
    Parse clientlist -voice Output.
    
    WICHTIG: TeamSpeak nutzt "clid=" nicht "client_id="!
    Und die Clients sind mit | getrennt in EINER Zeile!
    """
    speakers = {}
    
    # Split by pipe, nicht by newline!
    for entry in text.split("|"):
        entry = entry.strip()
        if not entry or "clid=" not in entry:
            continue
        
        try:
            # Extrahiere clid
            m = re.search(r"clid=(\d+)", entry)
            if not m:
                continue
            clid = int(m.group(1))
            
            if clid == 0:
                continue
            
            # WICHTIG: Prüfe auf client_flag_talking=1 ODER client_is_talker=1
            is_talking = "client_flag_talking=1" in entry or "client_is_talker=1" in entry
            
            if not is_talking:
                continue
            
            # Extrahiere Nickname
            m = re.search(r"client_nickname=([^\s]*)", entry)
            if not m:
                continue
            
            nick = format_nick(m.group(1))
            if nick:
                speakers[clid] = nick
                if DEBUG:
                    print(f"  ✨ Speaker: {clid} = {nick}")
        
        except Exception as e:
            if DEBUG:
                print(f"  ⚠️  Parse error: {e}")
            continue
    
    return speakers

def main():
    print("\n🎤 TeamSpeak → OLED (FIXED CLID)")
    print("="*50)
    
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((TS_HOST, TS_PORT))
        
        # Banner
        data = b""
        for _ in range(50):
            try:
                data += sock.recv(4096)
                if b"selected schandlerid=" in data:
                    break
            except socket.timeout:
                break
        
        if b"selected schandlerid=" not in data:
            print("❌ Banner nicht erhalten")
            return
        
        print("✅ Verbunden")
        
        # Auth
        sock.sendall(f"auth apikey={TS_API_KEY}\n".encode())
        sock.settimeout(1)
        data = b""
        try:
            data = sock.recv(4096)
        except:
            pass
        
        if b"error id=0" not in data:
            print("❌ Auth fehler")
            return
        
        print("✅ Auth OK")
        
        # Test OLED
        if not send_text("TEST"):
            print("❌ OLED nicht erreichbar")
            return
        
        print("✅ OLED OK\n")
        
        # Main loop
        active = {}
        last_text = ""
        
        print("[Time] 🔵 Display\n")
        
        while True:
            try:
                sock.sendall(b"clientlist -voice\n")
                sock.settimeout(1)
                data = b""
                try:
                    while True:
                        chunk = sock.recv(4096)
                        if not chunk:
                            break
                        data += chunk
                except socket.timeout:
                    pass
                
                output = data.decode("utf-8", errors="ignore")
                
                if DEBUG:
                    print(f"\n  📨 Raw output:\n  {output[:200]}...")
                
                raw = parse_speakers(output)
                
                if DEBUG and raw:
                    print(f"  🎤 Erkannte Sprecher: {raw}")
                
                # Update active (mit Debounce)
                now = time.time()
                for clid, name in raw.items():
                    if clid not in active:
                        active[clid] = (name, now)
                
                # Remove alte Sprecher nach Debounce
                remove = [clid for clid, (n, t) in active.items() if clid not in raw and (now - t) > DEBOUNCE_TIME]
                for clid in remove:
                    del active[clid]
                
                # Display formatieren
                if active:
                    speakers = sorted(active.items())[:MAX_SPEAKERS]
                    text = " | ".join([n for clid, (n, t) in speakers])
                else:
                    text = "IDLE"
                
                # Nur senden wenn geändert
                if text != last_text:
                    ts = time.strftime("%H:%M:%S")
                    send_text(text)
                    print(f"[{ts}] 🔵 {text}")
                    last_text = text
                
                time.sleep(POLL_INTERVAL)
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                if DEBUG:
                    print(f"⚠️  {e}")
                time.sleep(POLL_INTERVAL)
    
    except Exception as e:
        print(f"❌ {e}")
    
    finally:
        if sock:
            try:
                sock.close()
            except:
                pass
        try:
            send_text("IDLE")
        except:
            pass
        print("\n⏹️  Beendet")

if __name__ == "__main__":
    main()
    input("\nDrücke Enter...")
