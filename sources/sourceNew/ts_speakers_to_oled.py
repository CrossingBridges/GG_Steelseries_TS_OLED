import socket
import time
import configparser
import os

from gs_common import send_text

# Config laden
config = configparser.ConfigParser()
config_file = "config.ini"

if not os.path.exists(config_file):
    print(f"❌ {config_file} nicht gefunden!")
    print("Bitte config.ini mit deinem API-Key erstellen.")
    input("Enter zum Beenden...")
    exit(1)

config.read(config_file)

try:
    TS_HOST = config.get("TeamSpeak", "host")
    TS_PORT = config.getint("TeamSpeak", "port")
    TS_API_KEY = config.get("TeamSpeak", "api_key")
    POLL_INTERVAL = config.getfloat("Settings", "poll_interval")
    NICK_LENGTH = config.getint("Settings", "nick_length")
    MAX_SPEAKERS = config.getint("Settings", "max_speakers")
except configparser.Error as e:
    print(f"❌ Fehler in config.ini: {e}")
    input("Enter zum Beenden...")
    exit(1)

if TS_API_KEY == "HIER_DEINEN_API_KEY_EINTRAGEN":
    print("❌ API-Key noch nicht in config.ini gesetzt!")
    print("Bitte öffne config.ini und trage deinen API-Key ein.")
    input("Enter zum Beenden...")
    exit(1)

print(f"✅ Config geladen: API-Key={TS_API_KEY[:10]}...")
# ⭐ FIX: Poll-Interval auf 0.05s (50ms) für schnelleres Erkennen
EFFECTIVE_POLL = max(0.05, POLL_INTERVAL)  # Mindestens 50ms, auch wenn config sagt 0.1

def format_name(raw: str, nick_len: int = 6) -> str:
    s = raw.strip()
    
    # [BR]- oder [br]- entfernen
    if s.startswith("[BR]-") or s.startswith("[br]-"):
        s = s[5:]  # entfernt die ersten 5 Zeichen "[BR]-"
    
    real = ""
    if "(" in s and ")" in s:
        start = s.find("(") + 1
        end = s.find(")", start)
        if end > start:
            real = s[start:end].strip()
    
    if "(" in s:
        nick = s[:s.find("(")].strip()
    else:
        nick = s
    
    if len(nick) > nick_len:
        nick = nick[:nick_len]
    
    if real:
        return f"{nick} ({real})"
    else:
        return nick


def recv_until_prompt(sock: socket.socket) -> str:
    data = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
        text = data.decode("utf-8", errors="ignore")
        if "selected schandlerid=" in text:
            break
    return text


def recv_response(sock: socket.socket, timeout: float = 5.0) -> str:
    """
    Liest Antworten vom ClientQuery-Socket.
    Nimmt alles, was kommt, bis kein neues Daten mehr im Timeout ankommen.
    """
    sock.settimeout(timeout)
    data = b""
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
    except socket.timeout:
        # Timeout ist okay, wir haben wahrscheinlich alles, was kommt
        pass
    
    return data.decode("utf-8", errors="ignore")


def send_cmd(sock: socket.socket, cmd: str) -> str:
    sock.sendall((cmd + "\n").encode("utf-8"))
    return recv_response(sock, timeout=2.0)


def parse_speakers(clientlist_output: str) -> list[str]:
    speakers = []
    for line in clientlist_output.splitlines():
        if "client_nickname=" not in line:
            continue
        
        if (
            "client_flag_talking=1" not in line
            and "client_is_talker=1" not in line
            and "client_talk_request=1" not in line
        ):
            continue
        
        key = "client_nickname="
        start = line.find(key)
        if start == -1:
            continue
        
        start += len(key)
        end = line.find(" ", start)
        
        if end == -1:
            nick = line[start:]
        else:
            nick = line[start:end]
        
        nick = nick.replace("\\s", " ").replace("\\", "")
        
        if nick:
            speakers.append(format_name(nick))
    
    return speakers


def main():
    print("Verbinde zu TeamSpeak ClientQuery...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TS_HOST, TS_PORT))
    
    print("Verbunden, warte auf Banner...")
    banner = recv_until_prompt(sock)
    print("ClientQuery Banner:")
    print(banner)
    
    print(f"\nSende auth apikey={TS_API_KEY}...")
    resp = send_cmd(sock, f"auth apikey={TS_API_KEY}")
    print("auth-Antwort:")
    print(resp)
    
    if "error id=0" not in resp:
        print("❌ auth fehlgeschlagen!")
        sock.close()
        return
    
    print("✅ auth erfolgreich!")
    _ = send_cmd(sock, "whoami")
    
    last_text = ""
    print(f"\n🎤 Starte Sprecher-Monitor (Poll: {EFFECTIVE_POLL*1000:.0f}ms). Strg+C zum Beenden.")
    
    try:
        while True:
            out = send_cmd(sock, "clientlist -voice")
            speakers = parse_speakers(out)
            
            if speakers:
                text = " | ".join(speakers[:MAX_SPEAKERS])  # Nutze MAX_SPEAKERS aus config
            else:
                text = ""
            
            # ⭐ WICHTIG: Nur aktualisieren wenn Text sich geändert hat
            if text != last_text:
                if text:
                    print(f"📱 OLED: {text}")
                    send_text(text)
                else:
                    # 🔑 Sofort MEHRMALS Leer-Event senden für instantanes Löschen
                    print("📱 OLED: (gelöscht)")
                    send_text("")  # Leeres Event = sofort weg
                
                last_text = text
            
            # ⭐ FIX: Schneller abfragen (50ms statt 100ms)
            time.sleep(EFFECTIVE_POLL)
    
    except KeyboardInterrupt:
        print("\n⏹️ Beendet (Strg+C).")
    
    finally:
        try:
            send_cmd(sock, "quit")
        except Exception:
            pass
        sock.close()


if __name__ == "__main__":
    main()
