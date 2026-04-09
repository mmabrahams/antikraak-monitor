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
from shared import log, HEADERS

SITE_NAME = "gapph"
SITE_LABEL = "Gapph"
SEARCH_URL = "https://www.gapph.nl/woonruimte/zoeken?region_search=haarlem"
LOAD_URL = "https://www.gapph.nl/woonruimte/load"
BASE_URL = "https://www.gapph.nl/"

# De CSS-class die we verwachten als bewijs dat de paginastructuur klopt
EXPECTED_CONTAINER = "target_link"


def _parse_cards(soup):
    """Parse listing-kaarten uit een stuk HTML."""
    cards = soup.find_all(
        "div",
        class_=lambda c: c and "target_link" in c if c else False,
    )

    listings = []
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

    listings = _parse_cards(soup)
    log(f"[{SITE_NAME}] {len(listings)} listings op eerste pagina")

    # Laad extra pagina's als die er zijn
    loadmore = soup.find(id="loadmore")
    pages_loaded = 1

    while loadmore and pages_loaded < 15:
        last_id = loadmore.get("data-id", "")
        if not last_id:
            break

        log(f"[{SITE_NAME}] Extra pagina laden (lastid={last_id})...")
        load_response = requests.post(
            LOAD_URL,
            headers=HEADERS,
            data={"lastid": last_id},
            timeout=15,
        )

        if not load_response.ok or not load_response.text.strip():
            break

        page_soup = BeautifulSoup(load_response.text, "html.parser")
        page_listings = _parse_cards(page_soup)
        listings.extend(page_listings)
        pages_loaded += 1

        loadmore = page_soup.find(id="loadmore")

    total_listings = len(listings)
    log(f"[{SITE_NAME}] {total_listings} listings totaal ({pages_loaded} pagina's)")

    # Filter op Haarlem (exacte stadsnaam)
    haarlem = []
    for listing in listings:
        if listing["location"].lower().strip() == "haarlem":
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
