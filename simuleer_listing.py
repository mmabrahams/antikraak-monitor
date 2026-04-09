"""
Hulpscript: simuleert een nieuwe Haarlem-listing om te testen
of de Telegram-berichten goed aankomen.
Stuurt een testbericht namens elke site.
Gebruik: python3 simuleer_listing.py
"""

from shared import send_telegram, format_telegram_message, log
from datetime import datetime

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Simuleer een listing per site
test_listings = [
    {
        "listing": {
            "url": "https://vpsleegstandbeheer.nl/pand/test-haarlem/",
            "title": "TEST Woning | Haarlem",
            "location": "Haarlem, Noord-Holland",
            "price": "€150 p.m.",
            "size": "55 m²",
        },
        "label": "VPS Leegstandbeheer",
    },
    {
        "listing": {
            "url": "https://vastgoedbeschermer.nl/woonruimte/test-haarlem/",
            "title": "Haarlem",
            "location": "Noord-Holland",
            "price": "€ 280,- per maand",
            "size": "Oppervlakte 50-75m²",
        },
        "label": "Vastgoedbeschermer",
    },
    {
        "listing": {
            "url": "https://www.gapph.nl/woonruimte/antikraak/haarlem/9999",
            "title": "Antikraakwoning in Haarlem",
            "location": "Haarlem",
            "price": "€ 100,-",
            "size": "",
            "type": "Antikraakwoning",
        },
        "label": "Gapph",
    },
]

log("=== TEST: Simuleer listings van alle sites ===")

for item in test_listings:
    message = format_telegram_message(item["listing"], item["label"])
    message += f"\n\n⚠️ Dit is een TEST ({now})"
    send_telegram(message)
    log(f"Testbericht verstuurd voor {item['label']}")

log("=== Alle testberichten verstuurd. Check je telefoon! ===")
