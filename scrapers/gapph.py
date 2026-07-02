"""
Scraper voor Gapph.
Gebruikt de zoekfunctie om listings in de buurt van Haarlem te vinden,
en pagineert door de resultaten om alles te pakken te krijgen.
"""

import requests
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import log, HEADERS, in_target_area

SITE_NAME = "gapph"
SITE_LABEL = "Gapph"
# We halen het VOLLEDIGE aanbod op (niet de regio-zoekfunctie, want die
# bleek listings in bijv. Heemstede weg te laten) en filteren zelf op plaats.
SEARCH_URL = "https://www.gapph.nl/woonruimte"
LOAD_URL = "https://www.gapph.nl/woonruimte/load"
BASE_URL = "https://www.gapph.nl/"

# De CSS-class die we verwachten als bewijs dat de paginastructuur klopt
EXPECTED_CONTAINER = "target_link"


def _parse_cards(soup):
    """Parse listing-kaarten uit een stuk HTML (ontdubbeld op URL)."""
    cards = soup.find_all(
        "div",
        class_=lambda c: c and "target_link" in c if c else False,
    )

    listings = []
    seen = set()
    for card in cards:
        texts = [t.strip() for t in card.get_text().split("\n") if t.strip()]
        links = card.find_all("a", href=True)

        if not texts or not links:
            continue

        raw_url = links[0]["href"]
        if raw_url.startswith("http"):
            url = raw_url
        else:
            url = BASE_URL + raw_url.lstrip("/")

        if url in seen:
            continue
        seen.add(url)

        price = ""
        city = ""
        listing_type = ""
        description = ""

        for text in texts:
            if text.startswith("€"):
                if not price:
                    price = text.replace("\xa0", " ")
            elif text.startswith("Maximale"):
                continue
            elif text in ["Antikraakwoning", "Tijdelijke huurwoning"]:
                listing_type = text
            elif not city:
                city = text
            else:
                description = text

        listing = {
            "url": url,
            "title": f"{listing_type} in {city}" if listing_type and city else city or "Onbekend",
            "location": city,
            "price": price,
            "size": "",
            "type": listing_type,
            "description": description,
        }
        listings.append(listing)

    return listings


def fetch_listings():
    """
    Haal listings op via de Gapph-zoekfunctie en filter op Haarlem.
    Geeft een dict terug met 'listings' en 'health' info.
    """
    log(f"[{SITE_NAME}] Zoekpagina ophalen: {SEARCH_URL}")
    response = requests.get(SEARCH_URL, headers=HEADERS, timeout=15)
    response.raise_for_status()

    page_size = len(response.text)
    log(f"[{SITE_NAME}] Pagina opgehaald (status {response.status_code}, {page_size} bytes)")

    soup = BeautifulSoup(response.text, "html.parser")

    # Gezondheidscheck: verwachte container aanwezig?
    # Bij Gapph kan de zoekpagina leeg zijn als er niks in de buurt is.
    # We checken of de pagina überhaupt de juiste structuur heeft (zoekformulier).
    search_form = soup.find(id="azoeken")
    container_found = search_form is not None

    # LET OP: we gebruiken bewust GEEN doorklik-paginering ("Meer aanbod").
    # Dat bleek een archief met oude, al-vergeven woningen terug te geven.
    # De eerste pagina toont het volledige actuele aanbod.
    listings = _parse_cards(soup)
    total_listings = len(listings)
    log(f"[{SITE_NAME}] {total_listings} actuele listings gevonden")

    # Filter op het zoekgebied (Haarlem e.o., zie TARGET_PLACES in shared.py)
    matches = []
    for listing in listings:
        if in_target_area(listing["location"]):
            matches.append(listing)

    log(f"[{SITE_NAME}] {len(matches)} listings in zoekgebied")

    # Dubbelcheck per match: is de woning echt nog beschikbaar?
    # (voorkomt meldingen over al-vergeven woningen)
    beschikbaar = []
    for listing in matches:
        try:
            detail = requests.get(listing["url"], headers=HEADERS, timeout=15)
            if detail.ok and "niet beschikbaar" in detail.text.lower():
                log(f"[{SITE_NAME}] Overgeslagen (niet meer beschikbaar): {listing['title']}")
                continue
        except Exception as e:
            # Bij twijfel tóch melden: liever een melding te veel dan een gemiste woning
            log(f"[{SITE_NAME}] Dubbelcheck mislukt ({e}), listing wordt toch gemeld")
        beschikbaar.append(listing)

    return {
        "listings": beschikbaar,
        "health": {
            "page_size": page_size,
            "container_found": container_found,
            "total_listings": total_listings,
        },
    }
