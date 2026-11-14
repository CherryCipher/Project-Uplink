# Project UPLINK — Games & Software Library

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
- `software-detail.html?id=stoat` — softwaredetails, met twee screenshots en géén leaderboard.

## Stoat

`software.json` verwijst voorlopig naar `https://stoat.chat/download` zodat er geen verzonnen installer wordt aangeboden. Wil je het bestand lokaal aanbieden, plaats een officiële installer in `downloads/` en verander `downloadUrl` naar bijvoorbeeld `downloads/stoat-installer.exe` (gebruik de daadwerkelijke bestandsnaam).

Voor Stoat horen bestanden in `assets/stoat/` met `box.jpg`, `hero.jpg`, `1.jpg` en `2.jpg`. Ontbrekende foto's gebruiken placeholders. De systeemeisen zijn expliciet nog niet als minimum gespecificeerd.

Je bestaande `games.json` blijft ongewijzigd: neem dat bestand mee uit je huidige project. De ZIP bevat geen nieuw `games.json` zodat jouw ingestelde games en scores niet verloren gaan.
