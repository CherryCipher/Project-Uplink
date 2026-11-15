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
