# Antikraak-monitor Haarlem — Technisch ontwerp

## Doel

Een monitor die regelmatig de aanbodpagina's van antikraak-beheerders checkt op nieuwe listings in Haarlem, en mij via Telegram een pushbericht stuurt zodra er iets nieuws is.

## Te monitoren sites (definitief)

| # | Beheerder | URL | Methode | Notities |
|---|-----------|-----|---------|----------|
| 1 | VPS Leegstandbeheer | https://vpsleegstandbeheer.nl/antikraak-haarlem/ | Simpele scraping (HTML) + filteren op "Haarlem" | Toont landelijk portfolio als er niks in Haarlem is. Wij filteren zelf. Gezondheidscheck op aanwezigheid `/pand/`-links + `cb--cards_slider` class. |
| 2 | Vastgoedbeschermer | https://vastgoedbeschermer.nl/ik-zoek-ruimte/aanbod-woonruimte/ | Simpele scraping (HTML) + filteren op "Haarlem" | Listings staan in `object-card` divs. Elke kaart komt 2x voor in de HTML (afbeelding + tekst), we dedupliceren op URL. |
| 3 | Gapph | https://www.gapph.nl/woonruimte/zoeken?region_search=haarlem | Zoekfunctie (HTML) + filteren op exact "Haarlem" | Gebruikt de zoekfunctie die listings in de buurt van Haarlem toont. We filteren op exact stadsnaam "Haarlem" (niet Heemstede, niet Haarlemmermeer). Publiek aanbod, geen login nodig om te bekijken. |

### Onderzocht en geschrapt

| Site | Reden | Onderzocht op |
|------|-------|---------------|
| Tijdelijke Huur en Antikraak (tijdelijkehuurenantikraak.nl) | Domein offline — DNS resolve faalt. Site bestaat niet meer. | 2026-04-09 |
| De Kabath (dekabath.nl) | Alleen marketingtekst, aanbod vermoedelijk achter login. Overgeslagen op verzoek gebruiker. | 2026-04-09 |
| Villex.nl | Redirect naar Gapph (302 → gapph.nl). Zelfde bedrijf. | 2026-04-09 |
| Kamernet.nl | Betaald abonnement vereist. Geen Haarlem-listings zichtbaar. | 2026-04-09 |
| Kamer.nl | Blokkeert geautomatiseerde verzoeken (HTTP 403). | 2026-04-09 |
| Ad Hoc Beheer (adhocbeheer.nl) | Aanbodpagina geeft 404, listings laden via JavaScript, geen Haarlem-aanbod zichtbaar. Te onbetrouwbaar. | 2026-04-09 |

### Afwijkingen van oorspronkelijk plan

- **Gapph URL gewijzigd:** oorspronkelijk `/antikraak/haarlem` (marketingpagina), nu `/woonruimte/zoeken?region_search=haarlem` (echte zoekfunctie met publiek aanbod).
- **Geen Playwright nodig:** alle drie de sites serveren listings in de initiële HTML. De hybride strategie was niet nodig.
- **De Kabath geschrapt:** oorspronkelijk in de lijst, maar op verzoek van gebruiker overgeslagen na onderzoek.
- **Vastgoedbeschermer toegevoegd:** niet in het oorspronkelijke plan, gevonden tijdens extra onderzoek. Actief in Noord-Holland.

## Technische keuzes (definitief)

- **Taal:** Python 3 met `requests` en `beautifulsoup4`.
- **Draait op:** GitHub Actions met cron-schedule `*/5 * * * *`.
- **State:** Aparte git-branch `state`. Workflow haalt state op aan het begin, pusht terug aan het eind. De `main`-branch bevat alleen code.
- **State bevat per site:** geziene URLs, faal-teller, timestamp van laatste check, timestamp van laatst gevonden listing, paginagrootte van vorige run.
- **Secrets:** Telegram bot token en chat ID via GitHub Actions secrets. Lokaal via `.env` bestand (in `.gitignore`).
- **Portabiliteit:** Alle scraper- en notificatielogica staat in Python-bestanden, volledig los van de GitHub Actions workflow. Verhuizen naar cron op een Raspberry Pi of VPS vereist alleen het vervangen van de workflow door een crontab-regel.

## Scraping-strategie (definitief)

Alle drie de sites gebruiken simpele HTML-scraping via `requests` + `BeautifulSoup`. Geen JavaScript-rendering nodig, geen Playwright, geen verborgen API's.

Elke site heeft een eigen parser-bestand in `scrapers/`. Elke parser retourneert een dict met:
- `listings`: lijst van Haarlem-listings
- `health`: gezondheidsinfo (paginagrootte, container gevonden, totaal listings)

## Gezondheidscheck (definitief)

- **Niet** alarmeren op basis van "0 listings" — leegte is normaal in Haarlem.
- Check 1: verwachte HTML-structuur (CSS-class) aanwezig.
- Check 2: paginagrootte niet kleiner dan 30% van vorige run.
- **Three-strikes-regel:** waarschuwing na 3 opeenvolgende fouten. "Hersteld"-bericht zodra het weer werkt.
- **Structurele leegte:** nog niet geïmplementeerd. Timestamp van laatst gevonden listing wordt gelogd. Drempel bepalen na 2+ weken data.

## Foutafhandeling (definitief)

Drie lagen:
1. **Per scraper:** try/except vangt fouten op, stuurt Telegram-bericht met foutmelding, andere sites draaien gewoon door.
2. **Hoofdscript:** buitenste try/except vangt alles op wat laag 1 mist, stuurt crash-bericht met stacktrace.
3. **GitHub Actions:** `if: failure()`-stap stuurt via curl een Telegram-bericht als de job zelf crasht voordat Python kan reageren.

## Logging

- Naar stdout (zichtbaar in GitHub Actions logs).
- Naar `monitor.log` bestand (lokaal testen).
- Elk bericht bevat een tijdstempel in het formaat `[YYYY-MM-DD HH:MM:SS]`.

## Telegram-bot

- **Naam:** Wonen Haarlem (@WonenHaarlemMiqibot)
- **Chat ID:** opgeslagen in GitHub Secrets als `TELEGRAM_CHAT_ID`
- **Bot token:** opgeslagen in GitHub Secrets als `TELEGRAM_BOT_TOKEN`

## Filters

Geen filters — alles in Haarlem is relevant.

## Verwachting

Antikraak-aanbod in Haarlem is schaars. De monitor kan weken of langer niks vinden zonder dat er iets mis is. Dit is geen bug.
