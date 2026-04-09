"""
Gedeelde functies voor de antikraak-monitor.
Telegram-berichten, state-beheer, en logging.
"""

import requests
import json
import os
from datetime import datetime

# --- Laad .env bestand als het bestaat (voor lokaal testen) ---
_env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                os.environ.setdefault(_key.strip(), _val.strip())

# --- Instellingen ---
# Token en chat ID komen uit omgevingsvariabelen (GitHub Secrets)
# of uit een lokaal .env bestand voor lokaal testen
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "monitor.log")

# Three-strikes: na zoveel opeenvolgende fouten sturen we een waarschuwing
FAIL_THRESHOLD = 3

# Standaard headers voor het ophalen van websites
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"
}


def log(message):
    """Print een bericht met tijdstip ervoor en schrijf naar logbestand."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {message}"
    print(line)

    # Schrijf ook naar het logbestand
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass  # Als het logbestand niet schrijfbaar is, ga gewoon door


def send_telegram(message):
    """Stuur een bericht via Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.ok:
            log("Telegram-bericht verstuurd.")
        else:
            log(f"Telegram-fout: {response.status_code} - {response.text}")
    except Exception as e:
        log(f"Kon Telegram-bericht niet versturen: {e}")


def load_state(site_name):
    """Laad de opgeslagen state voor een specifieke site."""
    state_file = os.path.join(BASE_DIR, f"state_{site_name}.json")
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return json.load(f)
    return None  # None betekent: allereerste run


def save_state(site_name, seen_urls, fail_count=0, last_listing_found=None,
               last_page_size=None):
    """Sla de volledige state op voor een specifieke site."""
    state_file = os.path.join(BASE_DIR, f"state_{site_name}.json")

    # Laad bestaande state om velden te behouden die we niet updaten
    existing = load_state(site_name) or {}

    state = {
        "seen_urls": list(seen_urls),
        "last_check": datetime.now().isoformat(),
        "fail_count": fail_count,
        "last_listing_found": last_listing_found or existing.get("last_listing_found"),
        "last_page_size": last_page_size or existing.get("last_page_size"),
    }
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)
    log(f"[{site_name}] State opgeslagen ({len(seen_urls)} URLs, {fail_count} fails)")


def format_telegram_message(listing, site_label):
    """Maak een mooi Telegram-bericht voor een nieuwe listing."""
    parts = [
        "🏠 <b>Nieuwe antikraak in Haarlem!</b>",
        "",
        f"<b>{listing['title']}</b>",
        f"📍 {listing['location']}",
    ]
    if listing.get("price"):
        parts.append(f"💰 {listing['price']}")
    if listing.get("size"):
        parts.append(f"📐 {listing['size']}")
    if listing.get("type"):
        parts.append(f"🏷️ {listing['type']}")
    parts.append("")
    parts.append(f"🔗 <a href=\"{listing['url']}\">Bekijk de listing</a>")
    parts.append("")
    parts.append(f"— {site_label}")

    return "\n".join(parts)


def check_health(site_name, health, state):
    """
    Controleer de gezondheid van een scrape-resultaat.
    Geeft (ok, problemen) terug.
    ok = True als alles goed lijkt, False als er iets mis is.
    problemen = lijst van strings die beschrijven wat er mis is.
    """
    problems = []

    # Check 1: Verwachte container-structuur aanwezig?
    if not health.get("container_found"):
        problems.append("Verwachte HTML-structuur niet gevonden (site mogelijk gewijzigd)")

    # Check 2: Pagina-grootte vergelijken met vorige keer
    current_size = health.get("page_size", 0)
    if state and state.get("last_page_size"):
        previous_size = state["last_page_size"]
        # Als de pagina minder dan 30% van de vorige grootte is, is er iets mis
        if previous_size > 0 and current_size < previous_size * 0.3:
            problems.append(
                f"Pagina is verdacht klein ({current_size} bytes vs {previous_size} vorige keer)"
            )

    if problems:
        log(f"[{site_name}] Gezondheidsproblemen: {', '.join(problems)}")
    else:
        log(f"[{site_name}] Gezondheidscheck OK")

    return len(problems) == 0, problems
