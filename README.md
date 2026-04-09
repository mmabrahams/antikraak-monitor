# Antikraak Monitor Haarlem

## Wat doet dit?

Deze monitor checkt automatisch elke 5 minuten drie antikraak-websites op nieuwe woningen in Haarlem. Als er iets nieuws verschijnt, krijg je direct een bericht op Telegram met de titel, prijs, en een link naar de listing.

De monitor draait 24/7 in de cloud via GitHub Actions — je laptop hoeft niet aan te staan.

---

## Hoe werkt het?

### Welke sites worden gecheckt

| Site | Wat de monitor doet |
|------|---------------------|
| **VPS Leegstandbeheer** | Haalt de Haarlem-pagina op, zoekt alle listings, filtert op "Haarlem" (de site toont ook andere steden). |
| **Vastgoedbeschermer** | Haalt de aanbodpagina op, zoekt alle listings, filtert op "Haarlem". |
| **Gapph** | Gebruikt de zoekfunctie van Gapph om listings in de buurt van Haarlem te vinden, filtert op exact "Haarlem". |

### Hoe het technisch werkt

```
Elke ~5 minuten:
  1. GitHub Actions start het script
  2. Het script haalt de opgeslagen "state" op (welke listings al gezien zijn)
  3. Per site: haal de pagina op → zoek listings → filter op Haarlem
  4. Vergelijk met wat al gezien is → stuur Telegram bij iets nieuws
  5. Sla de bijgewerkte state op
```

- **Code** staat in de `main`-branch op GitHub
- **State** (welke listings al gezien zijn) staat in een aparte `state`-branch
- **Secrets** (Telegram-token en chat ID) staan veilig in GitHub Secrets
- **Elke site heeft een eigen bestandje** — als er eentje kapotgaat, draaien de andere gewoon door

### Welke berichten kun je krijgen?

| Bericht | Betekenis |
|---------|-----------|
| 🏠 **Nieuwe antikraak in Haarlem!** | Er is een nieuwe listing gevonden. Klik op de link om te reageren. |
| ⚠️ **[Site] faalt al 3x achter elkaar!** | Een website is 3 keer op rij niet bereikbaar of gewijzigd. De monitor blijft het proberen. |
| ✅ **[Site] werkt weer!** | Een site die eerder faalde, werkt weer. |
| 🚨 **Kritieke fout / GitHub Actions gecrasht!** | Er is iets ernstigs misgegaan. Zie hieronder hoe je dit oplost. |

---

## Hoe zie ik of de monitor nog draait?

1. Ga naar **github.com/mmabrahams/antikraak-monitor**
2. Klik bovenaan op het tabje **Actions**
3. Je ziet een lijst met runs. Elke run heeft een status:
   - ✅ **Groen vinkje** = gelukt
   - ❌ **Rood kruisje** = mislukt
   - 🟡 **Oranje cirkel** = nog bezig
4. Klik op een run om details te zien
5. Klik op **check** (onder "Jobs") om de stap-voor-stap logs te bekijken

**Hoe vaak draait hij echt?** Kijk naar de tijdstempels van de runs in de Actions-tab. GitHub Actions cron kan vertraagd zijn (zie Beperkingen hieronder).

---

## Wat doe ik als een parser kapot is?

Als je een bericht krijgt dat een site faalt, of als je ziet dat runs steeds mislukken:

### Stap 1: Check of het een tijdelijk probleem is

Soms is een website even offline. Als je na een paar uur een "✅ werkt weer!" bericht krijgt, hoef je niks te doen.

### Stap 2: Gebruik Claude Code om het te fixen

Open Claude Code en plak deze prompt:

```
Mijn antikraak-monitor heeft een probleem. De scraper voor [NAAM VAN DE SITE]
werkt niet meer. Het project staat in /Users/miquel/Claude appjes/antikraak-monitor/

Belangrijk: ik ben beginner en kan geen code lezen.

Kun je:
1. De betreffende site ophalen en kijken wat er veranderd is
2. De scraper aanpassen zodat het weer werkt
3. Lokaal testen of het werkt (draai python3 monitor.py)
4. De fix uploaden naar GitHub (git add, commit, push naar main)

De repo staat op github.com/mmabrahams/antikraak-monitor
```

Vervang `[NAAM VAN DE SITE]` door de site die problemen geeft (bijv. "VPS Leegstandbeheer" of "Gapph").

---

## Hoe voeg ik een site toe of verwijder ik er een?

### Site toevoegen

Open Claude Code en plak:

```
Ik wil een nieuwe site toevoegen aan mijn antikraak-monitor.
Het project staat in /Users/miquel/Claude appjes/antikraak-monitor/

De nieuwe site is: [URL VAN DE SITE]

Belangrijk: ik ben beginner en kan geen code lezen.

Kun je:
1. De site onderzoeken (staan listings in de HTML of is JavaScript nodig?)
2. Een nieuwe scraper maken in de scrapers/ map
3. De scraper toevoegen aan monitor.py
4. Lokaal testen
5. Uploaden naar GitHub
```

### Site verwijderen

Open Claude Code en plak:

```
Ik wil [NAAM VAN DE SITE] verwijderen uit mijn antikraak-monitor.
Het project staat in /Users/miquel/Claude appjes/antikraak-monitor/

Belangrijk: ik ben beginner en kan geen code lezen.

Kun je de site verwijderen uit de code en de wijziging uploaden naar GitHub?
```

---

## Hoe wijzig ik de Telegram-instellingen?

Als je een andere Telegram-bot wilt gebruiken of berichten naar een andere chat wilt sturen:

1. Ga naar **github.com/mmabrahams/antikraak-monitor**
2. Klik op **Settings** (tandwiel-icoon, helemaal rechts bovenaan)
3. Klik links op **Secrets and variables** → **Actions**
4. Je ziet `TELEGRAM_BOT_TOKEN` en `TELEGRAM_CHAT_ID`
5. Klik op het potloodje naast de secret die je wilt wijzigen
6. Plak de nieuwe waarde en klik op **Update secret**

**Voor lokaal testen:** wijzig het bestand `.env` in de projectmap op je computer.

---

## Hoe verhuis ik naar een Raspberry Pi of VPS?

Als GitHub Actions te traag of onbetrouwbaar blijkt, kun je de monitor op eigen hardware draaien. De code is daar klaar voor — de scraper-logica staat los van GitHub Actions.

Open Claude Code en plak:

```
Ik wil mijn antikraak-monitor verhuizen van GitHub Actions naar
[een Raspberry Pi / een VPS]. Het project staat in
/Users/miquel/Claude appjes/antikraak-monitor/

Belangrijk: ik ben beginner en kan geen code lezen.

Kun je me stap voor stap helpen om:
1. De monitor op mijn [Raspberry Pi / VPS] te installeren
2. Een cron-job in te stellen die het script elke 5 minuten draait
3. De state lokaal op te slaan in plaats van in een git-branch
4. Te testen of alles werkt
```

---

## Bekende beperkingen

### Aanbod is schaars — dat is normaal
Antikraak-aanbod in Haarlem is van nature schaars. Het kan **weken of maanden** duren zonder dat de monitor iets vindt. Dat betekent niet dat hij kapot is. De monitor vergroot je kans om snel te reageren als er iets komt, maar hij creëert geen aanbod.

### GitHub Actions cron is niet exact
GitHub belooft "elke 5 minuten", maar in de praktijk kan het **10 tot 30 minuten of meer** duren tussen runs, vooral bij drukte op het platform. Dit is een bekende beperking van GitHub Actions. Als exacte timing belangrijk is, overweeg dan verhuizen naar een Raspberry Pi of VPS.

### Sites die we niet of gedeeltelijk monitoren

| Site | Situatie |
|------|----------|
| **Gapph** (achter login) | Gapph heeft een Mijn Gapph-portaal (€25/jaar) met mogelijk extra aanbod. Wij monitoren alleen het **publieke** aanbod via de zoekfunctie. Om te reageren op een listing heb je wel een account nodig. |
| **De Kabath** | Bewust overgeslagen — alleen marketingtekst op de publieke pagina, aanbod vermoedelijk achter login. |
| **Tijdelijke Huur en Antikraak** | Site bestaat niet meer (domein offline sinds april 2026). |

### Als een site blijvend onbereikbaar is

Als je al meer dan een week "⚠️ faalt"-berichten krijgt voor een site:

1. Probeer de URL zelf te openen in je browser
2. Als de site echt weg is: verwijder hem uit de monitor (zie instructies hierboven)
3. Zoek eventueel een vervangende site (zie de prompt hierboven voor "site toevoegen")

---

## Bestanden in dit project

```
antikraak-monitor/
├── .github/workflows/
│   └── monitor.yml          ← GitHub Actions workflow (de "timer")
├── scrapers/
│   ├── vps.py               ← VPS Leegstandbeheer scraper
│   ├── vastgoedbeschermer.py ← Vastgoedbeschermer scraper
│   └── gapph.py             ← Gapph scraper
├── monitor.py               ← Hoofdscript (roept alle scrapers aan)
├── shared.py                ← Gedeelde functies (Telegram, state, logging)
├── simuleer_listing.py      ← Testscript: stuur nep-berichten
├── test_fouten.py           ← Testscript: test foutafhandeling
├── requirements.txt         ← Lijst van benodigde Python-bibliotheken
├── .env                     ← Lokale secrets (NIET op GitHub)
├── .gitignore               ← Bestanden die niet naar GitHub gaan
├── PROJECT.md               ← Technische designkeuzes en onderzoek
└── README.md                ← Dit bestand
```
