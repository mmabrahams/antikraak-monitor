# Antikraak-monitor Haarlem

## Doel

Een monitor die regelmatig de aanbodpagina's van antikraak-beheerders checkt op nieuwe listings in Haarlem, en mij via Telegram een pushbericht stuurt zodra er iets nieuws is.

## Te monitoren sites

| # | Beheerder | URL | Methode | Notities |
|---|-----------|-----|---------|----------|
| 1 | Gapph | https://www.gapph.nl/woonruimte/antikraak/haarlem | Simpele scraping (HTML) + API `/woonruimte/load` voor extra listings | Publiek aanbod, geen login nodig om te bekijken. Login (€25/jr) alleen nodig om te reageren. |
| 2 | VPS Leegstandbeheer | https://vpsleegstandbeheer.nl/antikraak-haarlem/ | Simpele scraping (HTML) + filteren op "Haarlem" | Toont landelijk portfolio als er niks in Haarlem is. Wij filteren zelf. |
| 3 | Vastgoedbeschermer | https://vastgoedbeschermer.nl/ik-zoek-ruimte/aanbod-woonruimte/ | Simpele scraping (HTML) + filteren op "Haarlem" / Noord-Holland | 14 listings in HTML, actief in Noord-Holland. Nu niks in Haarlem maar kan veranderen. |

### Onderzocht en geschrapt

| Site | Reden |
|------|-------|
| Tijdelijke Huur en Antikraak (tijdelijkehuurenantikraak.nl) | Domein offline — DNS resolve faalt. Site bestaat niet meer. |
| De Kabath (dekabath.nl) | Alleen marketingtekst, aanbod vermoedelijk achter login. Overgeslagen op verzoek gebruiker. |
| Villex.nl | Redirect naar Gapph — zelfde bedrijf. |
| Kamernet.nl | Betaald abonnement vereist om contact op te nemen. Geen Haarlem-listings zichtbaar. |
| Kamer.nl | Blokkeert geautomatiseerde verzoeken (403). |
| Ad Hoc Beheer | Aanbodpagina geeft 404, listings laden via JavaScript, geen Haarlem-aanbod zichtbaar. Te onbetrouwbaar. |

## Technische keuzes

- **Taal:** Python (beginner-vriendelijk, goed gedocumenteerd).
- **Draait op:** GitHub Actions met cron-schedule `*/5 * * * *` (elke 5 minuten). GitHub Actions cron is in de praktijk vaak vertraagd — dat accepteren we voorlopig en meten we via logging. Geen sleep-loops binnen runs.
- **State:** Opgeslagen in een aparte git-branch `state`. De monitor checkt deze branch uit aan het begin van elke run, werkt de state bij, en pusht terug naar de `state`-branch. De `main`-branch blijft schoon.
- **State bevat:** welke listings al gezien zijn, faal-tellers per site, timestamp van laatst gevonden listing per site.
- **Secrets:** Telegram bot token en chat ID via GitHub Actions secrets.
- **Portabiliteit:** Scraper en notificatielogica gescheiden van de Actions-workflow, zodat later verhuizen naar een Raspberry Pi of VPS mogelijk is zonder alles te herschrijven.

## Scraping-strategie (hybride)

1. Probeer eerst of listings in de initiële HTML staan via een simpele `requests`-call.
2. Als een site JavaScript-rendering gebruikt: zoek samen naar een verborgen JSON-API. Het onderzoek in de Network-tab van de browser doet de gebruiker, met precieze klik-instructies.
3. Alleen als er geen API te vinden is, gebruik Playwright voor die specifieke site.
4. Houd simpele en Playwright-scrapers gescheiden zodat snelle sites snel blijven.
5. Elke site krijgt zijn eigen parser-module zodat één kapotte parser de rest niet meesleept.

## Gezondheidscheck

- **Niet** alarmeren op basis van "aantal listings = 0" — leegte is normaal in Haarlem.
- Wel checken: HTTP-status 200, verwachte container-structuur aanwezig, pagina-grootte ongeveer normaal vergeleken met eerdere runs.
- **Three-strikes-regel:** pas een waarschuwing sturen na 3 opeenvolgende gefaalde runs voor dezelfde site. Een "hersteld"-bericht sturen zodra de site weer werkt na eerder te hebben gefaald.
- Een drempel voor "structurele leegte" (bijv. X dagen geen listings terwijl dat raar is) bepalen we later, nadat we een week of twee echte data hebben verzameld. Niet nu hardcoden.

## Foutafhandeling

- Hoofdlogica in een try/except die bij elke onverwachte fout een Telegram-bericht stuurt met foutmelding en stacktrace.
- In de GitHub Actions-workflow een `if: failure()`-stap die via curl een Telegram-bericht stuurt als de job zelf crasht voordat Python kan reageren. Dubbel vangnet.

## Eerste run

Bij de allereerste run alle gevonden listings stil opslaan als baseline, zonder notificaties te sturen. Pas vanaf de tweede run worden echt nieuwe listings als notificatie verstuurd.

## Logging

Log bij elke check het exacte tijdstip, zodat na een week gemeten kan worden hoe vaak het script écht draait (GitHub Actions cron heeft vaak vertraging).

## Filters

Geen filters — alles in Haarlem is relevant.

## Verwachting

Antikraak-aanbod in Haarlem is schaars. De monitor kan weken of langer niks vinden zonder dat er iets mis is. Dit is geen bug.
