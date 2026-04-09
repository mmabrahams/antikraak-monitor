"""
Scraper voor Vastgoedbeschermer.
Haalt listings op van de woonruimte-aanbodpagina en filtert op Haarlem.
"""

import requests
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import log, HEADERS

SITE_NAME = "vastgoedbeschermer"
SITE_LABEL = "Vastgoedbeschermer"
URL = "https://vastgoedbeschermer.nl/ik-zoek-ruimte/aanbod-woonruimte/"

# De CSS-class die we verwachten als bewijs dat de paginastructuur klopt
EXPECTED_CONTAINER = "object-card"


def fetch_listings():
    """
    Haal alle listings op van Vastgoedbeschermer en filter op Haarlem.
    Geeft een dict terug met 'listings' en 'health' info.
    """
    log(f"[{SITE_NAME}] Pagina ophalen: {URL}")
    response = requests.get(URL, headers=HEADERS, timeout=15)
    response.raise_for_status()

    page_size = len(response.text)
    log(f"[{SITE_NAME}] Pagina opgehaald (status {response.status_code}, {page_size} bytes)")

    soup = BeautifulSoup(response.text, "html.parser")

    # Gezondheidscheck: verwachte container aanwezig?
    container = soup.find(
        "div",
        class_=lambda c: c and EXPECTED_CONTAINER in c if c else False,
    )
    container_found = container is not None

    # Zoek alle 'object-card' containers
    cards = soup.find_all(
        "div",
        class_=lambda c: c and "object-card" in c if c else False,
    )

    listings = []
    seen_urls = set()

    for card in cards:
        texts = [t.strip() for t in card.get_text().split("\n") if t.strip()]
        if not texts:
            continue

        links = card.find_all("a", href=True)
        url = ""
        for link in links:
            if "/woonruimte/" in link["href"]:
                url = link["href"]
                break

        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        filtered_texts = [t for t in texts if t != "Naar Woonruimte" and t != "Voldoende reacties"]

        listing = {
            "url": url,
            "title": filtered_texts[0] if len(filtered_texts) > 0 else "Onbekend",
            "location": filtered_texts[1] if len(filtered_texts) > 1 else "",
            "price": filtered_texts[2] if len(filtered_texts) > 2 else "",
            "size": filtered_texts[3] if len(filtered_texts) > 3 else "",
        }
        listings.append(listing)

    total_listings = len(listings)
    log(f"[{SITE_NAME}] {total_listings} listings gevonden")

    # Filter op Haarlem
    haarlem = []
    for listing in listings:
        combined = (listing["title"] + " " + listing["location"]).lower()
        if "haarlem" in combined:
            haarlem.append(listing)

    log(f"[{SITE_NAME}] {len(haarlem)} listings in Haarlem")

    return {
        "listings": haarlem,
        "health": {
            "page_size": page_size,
            "container_found": container_found,
            "total_listings": total_listings,
        },
    }
