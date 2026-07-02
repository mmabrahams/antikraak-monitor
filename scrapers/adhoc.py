"""
Scraper voor Ad Hoc Beheer.
Haalt het volledige aanbod op (één pagina, geen paginering) en filtert
op woonruimte in het zoekgebied (Haarlem e.o.).
"""

import re
import requests
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import log, HEADERS, in_target_area

SITE_NAME = "adhoc"
SITE_LABEL = "Ad Hoc Beheer"
URL = "https://www.adhocbeheer.nl/aanbod/"

# De CSS-class die we verwachten als bewijs dat de paginastructuur klopt
EXPECTED_CONTAINER = "wpgb-card-wrapper"


def fetch_listings():
    """
    Haal alle listings op van Ad Hoc en filter op woonruimte in het zoekgebied.
    Geeft een dict terug met 'listings' en 'health' info.
    """
    log(f"[{SITE_NAME}] Pagina ophalen: {URL}")
    response = requests.get(URL, headers=HEADERS, timeout=15)
    response.raise_for_status()

    page_size = len(response.text)
    log(f"[{SITE_NAME}] Pagina opgehaald (status {response.status_code}, {page_size} bytes)")

    soup = BeautifulSoup(response.text, "html.parser")

    # Alle aanbod-kaarten
    cards = soup.find_all(
        "div",
        class_=lambda c: c and EXPECTED_CONTAINER in c if c else False,
    )

    # Gezondheidscheck: kaarten aanwezig én de verwachte structuur in de HTML?
    container_found = len(cards) > 0 and EXPECTED_CONTAINER in response.text

    listings = []
    seen = set()
    for card in cards:
        # Detail-link naar het pand (afbeeldings-links overslaan)
        url = ""
        for link in card.find_all("a", href=True):
            if "/units/" in link["href"]:
                url = link["href"]
                break
        if not url or url in seen:
            continue
        seen.add(url)

        texts = [t.strip() for t in card.get_text("\n").split("\n") if t.strip()]
        if not texts:
            continue

        title = texts[0]
        listing_type = texts[1] if len(texts) > 1 else ""

        # Grootte staat als bijv. "62 m2" in de kaarttekst
        size = ""
        for t in texts:
            if re.match(r"^\d+\s*m2$", t):
                size = t
                break

        # Plaats: het deel na " in " in de titel, anders het laatste woord
        if " in " in title:
            location = title.split(" in ", 1)[1]
        else:
            location = title.split()[-1] if title.split() else ""

        listings.append({
            "url": url,
            "title": title,
            "location": location,
            "price": "",
            "size": size,
            "type": listing_type,
        })

    total_listings = len(listings)
    log(f"[{SITE_NAME}] {total_listings} listings gevonden")

    # Alleen WOONruimte (geen werkruimtes/bedrijfshallen)
    woonruimte = [
        l for l in listings
        if "woonruimte" in (l["title"] + " " + l["type"]).lower()
        or "woning" in (l["title"] + " " + l["type"]).lower()
    ]

    # Filter op het zoekgebied (Haarlem e.o., zie TARGET_PLACES in shared.py)
    matches = []
    for listing in woonruimte:
        if in_target_area(listing["title"] + " " + listing["location"]):
            matches.append(listing)

    log(f"[{SITE_NAME}] {len(matches)} woonruimte-listings in zoekgebied")

    return {
        "listings": matches,
        "health": {
            "page_size": page_size,
            "container_found": container_found,
            "total_listings": total_listings,
        },
    }
