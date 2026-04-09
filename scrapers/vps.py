"""
Scraper voor VPS Leegstandbeheer.
Haalt listings op van de antikraak-haarlem pagina en filtert op Haarlem.
"""

import requests
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import log, HEADERS

SITE_NAME = "vps"
SITE_LABEL = "VPS Leegstandbeheer"
URL = "https://vpsleegstandbeheer.nl/antikraak-haarlem/"

# De CSS-class die we verwachten in de HTML als bewijs dat de paginastructuur klopt
EXPECTED_CONTAINER = "cb--cards_slider"


def fetch_listings():
    """
    Haal alle listings op van de VPS-pagina en filter op Haarlem.
    Geeft een dict terug met 'listings' en 'health' info.
    """
    log(f"[{SITE_NAME}] Pagina ophalen: {URL}")
    response = requests.get(URL, headers=HEADERS, timeout=15)
    response.raise_for_status()

    page_size = len(response.text)
    log(f"[{SITE_NAME}] Pagina opgehaald (status {response.status_code}, {page_size} bytes)")

    soup = BeautifulSoup(response.text, "html.parser")

    # Zoek alle links naar individuele panden
    all_links = soup.find_all("a", href=True)
    property_links = [link for link in all_links if "/pand/" in link.get("href", "")]

    # Gezondheidscheck: zijn er pand-links EN bevat de HTML de verwachte structuur?
    container_found = len(property_links) > 0 and EXPECTED_CONTAINER in response.text

    listings = []
    for link in property_links:
        parent = link.parent
        texts = [t.strip() for t in parent.get_text().split("\n") if t.strip()]

        listing = {
            "url": link["href"],
            "title": texts[0] if len(texts) > 0 else "Onbekend",
            "location": texts[1] if len(texts) > 1 else "",
            "price": texts[2] if len(texts) > 2 else "",
            "size": texts[3] if len(texts) > 3 else "",
        }
        listings.append(listing)

    total_listings = len(listings)
    log(f"[{SITE_NAME}] {total_listings} listings gevonden op de pagina")

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
