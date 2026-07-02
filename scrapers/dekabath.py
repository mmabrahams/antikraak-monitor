"""
Scraper voor De Kabath.
Haalt de aanbodpagina op, gefilterd op woonruimte, en filtert
op het zoekgebied (Haarlem e.o.).
"""

import re
import requests
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import log, HEADERS, in_target_area

SITE_NAME = "dekabath"
SITE_LABEL = "De Kabath"
# We vragen de site zelf al om alleen WOONruimte te tonen
URL = "https://dekabath.nl/aanbod/?type_functie=woonruimte"
BASE_URL = "https://dekabath.nl"

# Dit filterveld staat altijd op de pagina, ook als er 0 resultaten zijn.
# Zo kunnen we "site kapot" onderscheiden van "geen aanbod".
EXPECTED_CONTAINER = "type_functie"

# Een echte listing-link ziet eruit als /aanbod/naam-van-het-pand/
_LISTING_LINK = re.compile(r"^(?:https://dekabath\.nl)?/aanbod/[a-z0-9\-]+/?$")


def fetch_listings():
    """
    Haal alle woonruimte-listings op van De Kabath en filter op het zoekgebied.
    Geeft een dict terug met 'listings' en 'health' info.
    """
    log(f"[{SITE_NAME}] Pagina ophalen: {URL}")
    response = requests.get(URL, headers=HEADERS, timeout=15)
    response.raise_for_status()

    page_size = len(response.text)
    log(f"[{SITE_NAME}] Pagina opgehaald (status {response.status_code}, {page_size} bytes)")

    soup = BeautifulSoup(response.text, "html.parser")

    # Gezondheidscheck: het filterformulier moet er altijd staan
    container_found = EXPECTED_CONTAINER in response.text

    listings = []
    seen = set()
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if not _LISTING_LINK.match(href):
            continue

        url = href if href.startswith("http") else BASE_URL + href
        if url in seen:
            continue
        seen.add(url)

        # De link bevat zelf de kaartinfo: titel, prijs, grootte, functie
        texts = [t.strip() for t in link.get_text("\n").split("\n") if t.strip()]
        if not texts:
            continue

        title = texts[0]

        # Label-waarde-paren uitlezen (bijv. "Prijs:" gevolgd door "€ 105")
        price = ""
        size = ""
        listing_type = ""
        for i, t in enumerate(texts):
            if t.startswith("Prijs") and i + 1 < len(texts):
                price = texts[i + 1]
            elif t.startswith("Grootte") and i + 1 < len(texts):
                size = texts[i + 1]
            elif t.startswith("Functie") and i + 1 < len(texts):
                listing_type = texts[i + 1]

        # Plaats: laatste woord van de titel (bijv. "Werkruimte Haarlem")
        location = title.split()[-1] if title.split() else ""

        listings.append({
            "url": url,
            "title": title,
            "location": location,
            "price": price,
            "size": size,
            "type": listing_type,
        })

    total_listings = len(listings)
    log(f"[{SITE_NAME}] {total_listings} woonruimte-listings gevonden")

    # Filter op het zoekgebied (Haarlem e.o., zie TARGET_PLACES in shared.py)
    matches = []
    for listing in listings:
        combined = listing["title"] + " " + listing["url"]
        if in_target_area(combined):
            matches.append(listing)

    log(f"[{SITE_NAME}] {len(matches)} listings in zoekgebied")

    return {
        "listings": matches,
        "health": {
            "page_size": page_size,
            "container_found": container_found,
            "total_listings": total_listings,
        },
    }
