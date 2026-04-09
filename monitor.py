"""
Antikraak Monitor Haarlem - Hoofdscript
Checkt alle sites op nieuwe antikraak-listings in Haarlem
en stuurt Telegram-berichten bij nieuwe vondsten.

Bevat: gezondheidscheck, three-strikes-regel, foutafhandeling,
bestandslogging.
"""

import traceback
from datetime import datetime
from shared import (
    log, send_telegram, load_state, save_state,
    format_telegram_message, check_health, FAIL_THRESHOLD,
)

# Importeer alle scrapers
from scrapers import vps, vastgoedbeschermer, gapph

# Lijst van alle sites die we monitoren
SITES = [
    {
        "name": "vps",
        "label": "VPS Leegstandbeheer",
        "scraper": vps,
    },
    {
        "name": "vastgoedbeschermer",
        "label": "Vastgoedbeschermer",
        "scraper": vastgoedbeschermer,
    },
    {
        "name": "gapph",
        "label": "Gapph",
        "scraper": gapph,
    },
]


def handle_failure(name, label, state, error_message):
    """
    Verwerk een gefaalde check met de three-strikes-regel.
    Geeft de nieuwe fail_count terug.
    """
    previous_fails = state.get("fail_count", 0) if state else 0
    new_fail_count = previous_fails + 1

    log(f"[{name}] Fout #{new_fail_count}: {error_message}")

    if new_fail_count == FAIL_THRESHOLD:
        # Exact op de drempel: stuur waarschuwing
        send_telegram(
            f"⚠️ <b>{label} faalt al {FAIL_THRESHOLD}x achter elkaar!</b>\n\n"
            f"Laatste fout: {error_message}\n\n"
            f"De monitor blijft het proberen. Je krijgt bericht zodra het weer werkt."
        )
    elif new_fail_count > FAIL_THRESHOLD:
        # Boven de drempel: log het maar stuur geen extra berichten
        log(f"[{name}] Blijft falen (#{new_fail_count}), geen extra Telegram-bericht")
    else:
        # Onder de drempel: alleen loggen
        log(f"[{name}] Fout #{new_fail_count} van {FAIL_THRESHOLD} (nog geen waarschuwing)")

    return new_fail_count


def handle_recovery(name, label, state):
    """
    Stuur een hersteld-bericht als de site eerder faalde maar nu weer werkt.
    """
    previous_fails = state.get("fail_count", 0) if state else 0

    if previous_fails >= FAIL_THRESHOLD:
        send_telegram(
            f"✅ <b>{label} werkt weer!</b>\n\n"
            f"Na {previous_fails} mislukte pogingen is de site weer bereikbaar."
        )
        log(f"[{name}] Hersteld na {previous_fails} fouten")
    elif previous_fails > 0:
        log(f"[{name}] Hersteld na {previous_fails} fout(en) (onder drempel, geen bericht)")


def check_site(site):
    """Check één site op nieuwe listings. Geeft True terug als het gelukt is."""
    name = site["name"]
    label = site["label"]

    log(f"--- {label} ---")

    # Laad de huidige state
    state = load_state(name)
    is_first_run = state is None

    try:
        # Haal listings en gezondheidsinfo op
        result = site["scraper"].fetch_listings()
        haarlem_listings = result["listings"]
        health = result["health"]

        # Gezondheidscheck
        health_ok, problems = check_health(name, health, state)

        if not health_ok:
            # Gezondheidscheck gefaald - behandel als fout
            error_msg = "; ".join(problems)
            fail_count = handle_failure(name, label, state, error_msg)

            # Sla state op met verhoogde fail-teller, maar behoud geziene URLs
            seen_urls = set(state["seen_urls"]) if state else set()
            save_state(name, seen_urls, fail_count=fail_count)
            return False

        # Gezondheid OK - check of we hersteld zijn van eerdere fouten
        if not is_first_run:
            handle_recovery(name, label, state)

        # Eerste run: baseline opslaan
        if is_first_run:
            log(f"[{name}] EERSTE RUN - Baseline opslaan (geen notificaties)")
            seen_urls = set(listing["url"] for listing in haarlem_listings)
            last_found = datetime.now().isoformat() if haarlem_listings else None
            save_state(name, seen_urls, fail_count=0,
                       last_listing_found=last_found,
                       last_page_size=health["page_size"])
            return True

        # Vergelijk met eerder geziene listings
        seen_urls = set(state["seen_urls"])
        new_listings = [l for l in haarlem_listings if l["url"] not in seen_urls]

        if new_listings:
            log(f"[{name}] {len(new_listings)} NIEUWE listing(s)!")
            for listing in new_listings:
                message = format_telegram_message(listing, label)
                send_telegram(message)
                log(f"[{name}] Nieuw: {listing['title']}")
        else:
            log(f"[{name}] Geen nieuwe listings.")

        # Werk geziene URLs bij
        for listing in haarlem_listings:
            seen_urls.add(listing["url"])

        # Bepaal wanneer we voor het laatst een listing vonden
        last_found = state.get("last_listing_found")
        if haarlem_listings:
            last_found = datetime.now().isoformat()

        save_state(name, seen_urls, fail_count=0,
                   last_listing_found=last_found,
                   last_page_size=health["page_size"])
        return True

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        fail_count = handle_failure(name, label, state, error_msg)

        # Sla state op met verhoogde fail-teller
        seen_urls = set(state["seen_urls"]) if state and state.get("seen_urls") else set()
        save_state(name, seen_urls, fail_count=fail_count)
        return False


def main():
    log("=== Antikraak Monitor Haarlem - Start ===")

    results = {}
    for site in SITES:
        try:
            success = check_site(site)
            results[site["name"]] = success
        except Exception as e:
            # Dit vangt alles op wat check_site zelf niet afving
            log(f"[{site['name']}] Onverwachte kritieke fout: {e}")
            log(traceback.format_exc())
            send_telegram(
                f"🚨 <b>Kritieke fout in de monitor!</b>\n\n"
                f"Site: {site['label']}\n"
                f"Fout: {type(e).__name__}: {e}\n\n"
                f"<pre>{traceback.format_exc()[-500:]}</pre>"
            )
            results[site["name"]] = False

    # Samenvatting
    ok = sum(1 for v in results.values() if v)
    fail = sum(1 for v in results.values() if not v)
    log(f"=== Klaar: {ok} sites OK, {fail} gefaald ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Allerlaatste vangnet - als zelfs main() crasht
        error_text = traceback.format_exc()
        print(f"KRITIEKE FOUT: {error_text}")
        try:
            send_telegram(
                f"🚨 <b>Monitor compleet gecrasht!</b>\n\n"
                f"<pre>{error_text[-800:]}</pre>"
            )
        except Exception:
            pass  # Als zelfs Telegram niet werkt, kunnen we niks meer doen
