# Project UPLINK — Games, Software & HUB

## Starten

Open deze map in VS Code en voer uit:

```powershell
py -m http.server 8000
```

Ga naar http://localhost:8000. `file://` werkt niet met `fetch` van JSON.

## Pagina's

- `index.html` — games catalogus (bestaande `games.json`).
- `game.html?id=xonotic` — bestaande game-details met leaderboard.
- `software.html` — aparte softwarecatalogus op basis van `software.json`.
- `hub.html` — overzicht van interne netwerkdiensten, gevuld vanuit `hub.json`.
- `software-detail.html?id=stoat` — softwaredetails, met twee screenshots en géén leaderboard.

## Stoat

`software.json` verwijst voorlopig naar `https://stoat.chat/download` zodat er geen verzonnen installer wordt aangeboden. Wil je het bestand lokaal aanbieden, plaats een officiële installer in `downloads/` en verander `downloadUrl` naar bijvoorbeeld `downloads/stoat-installer.exe` (gebruik de daadwerkelijke bestandsnaam).

Voor Stoat horen bestanden in `assets/stoat/` met `box.jpg`, `hero.jpg`, `1.jpg` en `2.jpg`. Ontbrekende foto's gebruiken placeholders. De systeemeisen zijn expliciet nog niet als minimum gespecificeerd.

Je bestaande `games.json` blijft ongewijzigd: neem dat bestand mee uit je huidige project. De ZIP bevat geen nieuw `games.json` zodat jouw ingestelde games en scores niet verloren gaan.

## HUB-links toevoegen

Open `hub.json` en voeg binnen de `links`-array een object toe:

```json
{
  "title": "Mijn service",
  "description": "Een korte omschrijving voor gasten.",
  "image": "assets/mijn-service.png",
  "url": "http://mijn-service.uplink.lan"
}
```

- `title`: titel van de kaart.
- `description`: korte beschrijving onder de titel.
- `image`: afbeelding links op de kaart, bij voorkeur in `assets/`. Mag leeg blijven; dan verschijnt een kleurvlak.
- `url`: volledige http://- of https://-link. Opent altijd in een nieuw tabblad.

Laat tussen de JSON-objecten een komma staan. Bewaar eigen afbeeldingen in `assets/`.
De HUB werkt zonder database en zonder extra backend. Start lokaal `py -m http.server 8000` en bezoek `http://localhost:8000/hub.html`. Lokale `.lan`-links werken alleen als je met het Uplink-netwerk verbonden bent en de betreffende service bereikbaar is.

## Automatische game-leaderboards

Voor Xonotic, AssaultCube en OpenArena is een optionele logparser toegevoegd.
Zie [docs/LEADERBOARDS.md](docs/LEADERBOARDS.md) voor configuratie, testen en beperkingen.
De website blijft statisch; `leaderboards.json` wordt lokaal op de webserver aangemaakt en niet naar Git gepusht.

## Gamekaart-badges instellen

In `games.json` kun je per game optioneel twee onafhankelijke booleans toevoegen:

```json
"localServer": true,
"liveScoring": true
```

- `localServer: true`: toont een klein servericoon rechtsboven op de gamebox. Dit geeft aan dat Uplink voor de game een lokale server aanbiedt, **niet** dat de server op dit moment technisch bereikbaar is.
- `liveScoring: true`: toont de opvallende **LIVE SCORING**-balk onderaan de gamebox. Schakel dit alleen in bij games die al een automatisch bijgewerkt leaderboard hebben.
- Als de velden ontbreken of `false` zijn, verschijnt er geen badge.

Deze informatie is handmatig en komt onafhankelijk van de feitelijke `leaderboards.json`; de bestaande leaderboard-updater blijft ongewijzigd.


## Program — planning per dag

De pagina `program.html` gebruikt `program.json` voor een tijdlijn met dagen en
activiteiten. Maak een dag aan met `date`, `label` en `events`. Voorbeeld:

```json
{
  "date": "2027-01-29",
  "label": "Friday 29th",
  "events": [
    {
      "start": "10:00",
      "end": "11:00",
      "game": "openarena",
      "title": "OpenArena Tournament",
      "description": "Join the arena!"
    },
    {
      "start": "12:00",
      "end": "13:00",
      "title": "Lunch",
      "type": "break"
    },
    {
      "start": "14:00",
      "end": "15:00",
      "title": "Board Games",
      "type": "activity",
      "url": "hub.html",
      "linkLabel": "Explore services"
    }
  ]
}
```

- `game` is de **id** uit `games.json`, bijvoorbeeld `openarena`,
  `xonotic` of `assaultcube`. De pagina haalt zelf de naam, box-art
  en link naar `game.html?id=...` op; voer geen afbeeldingspaden in het
  programma in. `title` is optioneel; je kunt daarmee een speciale naam
  zoals "OpenArena Tournament" tonen.
- Zonder `game` is de activiteit vrij invulbaar, bijvoorbeeld lunch,
  pauzes, bordspellen of workshops. `type: "break"` geeft het label
  `BREAK / FOOD`, anders staat er `ACTIVITY`.
- `url` en optioneel `linkLabel` geven een gewone activiteit een eigen
  link. Voor gameactiviteiten is de link al automatisch.
- Zet tijdstippen in `HH:MM` 24-uursnotatie; per dag sorteert de site
  automatisch op starttijd. De `label` bepaalt de zichtbare dagtitel.
- `title` en `subtitle` bovenaan `program.json` bepalen de paginakop.
- De voorbeeldagenda voor vrijdag 29 en zaterdag 30 januari 2027 is
  **voorbeeldinhoud** die je zelf moet vervangen door het echte programma.

Alle bestanden zijn statisch en werken op je bestaande Nginx-webserver.
Na een wijziging aan `program.json` is geen herstart van services nodig.
