"""
Testscript: simuleert fouten om te checken of de foutafhandeling werkt.
Gebruik: python3 test_fouten.py
"""

import json
import os
import sys
from datetime import datetime
from shared import log, send_telegram, load_state, save_state, check_health, FAIL_THRESHOLD

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def test_three_strikes():
    """Simuleer 3 opeenvolgende fouten voor een nepsite."""
    test_name = "_test_nepsite"
    test_label = "Test Nepsite"

    log("=== TEST 1: Three-strikes-regel ===")
    log("We simuleren 3 opeenvolgende fouten...")

    # Ruim eerdere teststate op
    state_file = os.path.join(BASE_DIR, f"state_{test_name}.json")
    if os.path.exists(state_file):
        os.remove(state_file)

    # Simuleer 3 fouten
    for i in range(1, FAIL_THRESHOLD + 1):
        state = load_state(test_name)
        previous_fails = state.get("fail_count", 0) if state else 0
        new_fail_count = previous_fails + 1

        log(f"  Fout #{new_fail_count}...")

        if new_fail_count == FAIL_THRESHOLD:
            send_telegram(
                f"⚠️ <b>{test_label} faalt al {FAIL_THRESHOLD}x achter elkaar!</b>\n\n"
                f"Laatste fout: Test-fout (gesimuleerd)\n\n"
                f"⚠️ Dit is een TEST"
            )
            log(f"  -> Waarschuwing verstuurd!")
        else:
            log(f"  -> Onder drempel ({new_fail_count}/{FAIL_THRESHOLD}), geen bericht")

        save_state(test_name, set(), fail_count=new_fail_count)

    log("Check je telefoon — je zou ÉÉN waarschuwing moeten zien (niet drie)")
    log("")

    return test_name


def test_recovery(test_name):
    """Simuleer herstel na eerdere fouten."""
    test_label = "Test Nepsite"

    log("=== TEST 2: Hersteld-bericht ===")
    log("We simuleren dat de site weer werkt na 3 fouten...")

    state = load_state(test_name)
    previous_fails = state.get("fail_count", 0) if state else 0

    if previous_fails >= FAIL_THRESHOLD:
        send_telegram(
            f"✅ <b>{test_label} werkt weer!</b>\n\n"
            f"Na {previous_fails} mislukte pogingen is de site weer bereikbaar.\n\n"
            f"⚠️ Dit is een TEST"
        )
        log(f"  Hersteld-bericht verstuurd!")

    # Reset de fail counter
    save_state(test_name, set(), fail_count=0)
    log("Check je telefoon — je zou een 'werkt weer' bericht moeten zien")
    log("")


def test_health_check():
    """Simuleer een gezondheidscheck die faalt."""
    log("=== TEST 3: Gezondheidscheck ===")

    # Test 1: container niet gevonden
    health = {"page_size": 50000, "container_found": False, "total_listings": 0}
    ok, problems = check_health("_test", health, None)
    log(f"  Container niet gevonden: ok={ok}, problemen={problems}")

    # Test 2: pagina verdacht klein
    fake_state = {"last_page_size": 100000}
    health = {"page_size": 5000, "container_found": True, "total_listings": 5}
    ok, problems = check_health("_test", health, fake_state)
    log(f"  Pagina te klein: ok={ok}, problemen={problems}")

    # Test 3: alles OK
    health = {"page_size": 95000, "container_found": True, "total_listings": 10}
    ok, problems = check_health("_test", health, fake_state)
    log(f"  Alles OK: ok={ok}, problemen={problems}")

    log("")


def test_crash_notification():
    """Simuleer een crash die een Telegram-bericht stuurt."""
    log("=== TEST 4: Crash-bericht ===")
    log("We simuleren een onverwachte crash...")

    try:
        # Dit gooit expres een fout
        result = 1 / 0
    except Exception as e:
        import traceback
        send_telegram(
            f"🚨 <b>Kritieke fout in de monitor!</b>\n\n"
            f"Fout: {type(e).__name__}: {e}\n\n"
            f"⚠️ Dit is een TEST"
        )
        log(f"  Crash-bericht verstuurd!")

    log("Check je telefoon — je zou een crash-bericht moeten zien")
    log("")


def cleanup(test_name):
    """Ruim testbestanden op."""
    state_file = os.path.join(BASE_DIR, f"state_{test_name}.json")
    if os.path.exists(state_file):
        os.remove(state_file)
    log("Testbestanden opgeruimd.")


def main():
    log("========================================")
    log("  FOUTAFHANDELING TESTEN")
    log("========================================")
    log("")

    test_health_check()
    test_name = test_three_strikes()
    test_recovery(test_name)
    test_crash_notification()
    cleanup(test_name)

    log("========================================")
    log("  ALLE TESTS KLAAR")
    log("========================================")
    log("Je zou 3 Telegram-berichten moeten hebben:")
    log("  1. ⚠️ Waarschuwing (three-strikes)")
    log("  2. ✅ Hersteld-bericht")
    log("  3. 🚨 Crash-bericht")


if __name__ == "__main__":
    main()
