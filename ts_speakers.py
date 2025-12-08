"""
TeamSpeak 3 → OLED Display - LEERZEICHEN ENTFERNT
VERSION 5.2 - KOMPAKTERE NICKNAMES

Formatierung:
  [BR]-Nickname(Realname)  → NicknameRealname (Leerzeichen entfernt)
  [br]-Nickname(Real)      → NicknameReal
  Nickname                 → Nickname (max 6 Zeichen, ohne Leerzeichen)
  
Beispiele:
  [BR]-Crossbearer(Daniel)     → Crossb | Daniel
  [BR]-The Deadman(Uwe)        → TheDe | Uwe
  [BR]-SILENT MAN(Jörg)        → SILENTMAN
  FatzRatz                     → FatzRa
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
DEBUG = config.getboolean("Settings", "debug", fallback=False)
DEBOUNCE_TIME = config.getfloat("Settings", "debounce_time", fallback=0.1)

print(f"\n✅ Config: {TS_HOST}:{TS_PORT} | Poll: {POLL_INTERVAL}s")

def format_nick(raw: str) -> str:
    """
    Formatiert Nicknames richtig.
    
    [BR]-Crossbearer(Daniel) → Crossb | Daniel
    [BR]-The Deadman(Uwe) → TheDe | Uwe
    Falcon → Falcon
    
    Leerzeichen werden entfernt um mehr Platz zu sparen!
    """
    if not raw:
        return ""
    
    s = raw.strip()
    
    # Unescape TeamSpeak Escape-Sequenzen
    s = s.replace("\\s", " ").replace("\\\\", "\\").replace("\\p", "/")
    
    # [BR]- oder [br]- IMMER löschen
    if s.startswith(("[BR]-", "[br]-")):
        s = s[5:]
    
    # Real-Namen aus Klammern extrahieren
    realname = ""
    if "(" in s and ")" in s:
        start = s.find("(") + 1
        end = s.find(")", start)
        if end > start:
            realname = s[start:end].strip()
    
    # Nickname-Teil (vor der Klammer)
    if "(" in s:
        nickname = s[:s.find("(")].strip()
    else:
        nickname = s
    
    # LEERZEICHEN ENTFERNEN um Platz zu sparen!
    nickname = nickname.replace(" ", "")
    realname = realname.replace(" ", "")
    
    # Nickname auf 6 Zeichen begrenzen
    if len(nickname) > 6:
        nickname = nickname[:6]
    
    # Zusammensetzen
    if realname:
        return f"{nickname} | {realname}"
    else:
        return nickname

def parse_speakers(text: str) -> Dict[int, str]:
    """
    Parse clientlist -voice Output.
    """
    speakers = {}
    
    # Split by pipe (die Clients sind mit | getrennt in EINER Zeile)
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
            
            # Prüfe ob Client spricht
            is_talking = "client_flag_talking=1" in entry or "client_is_talker=1" in entry
            
            if not is_talking:
                continue
            
            # Extrahiere Nickname
            m = re.search(r"client_nickname=([^\s]*)", entry)
            if not m:
                continue
            
            nick_raw = m.group(1)
            nick = format_nick(nick_raw)
            
            if nick:
                speakers[clid] = nick
                if DEBUG:
                    print(f"  ✨ {nick_raw} → {nick}")
        
        except Exception as e:
            if DEBUG:
                print(f"  ⚠️  Parse error: {e}")
            continue
    
    return speakers

def main():
    print("\n🎤 TeamSpeak → OLED (KOMPAKT)")
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
                raw = parse_speakers(output)
                
                if DEBUG and raw:
                    print(f"  🎤 Speakers: {raw}")
                
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
