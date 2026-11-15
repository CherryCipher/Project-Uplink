# Uplink — automatische leaderboards

De website blijft **statisch** (HTML/JS). Geen database en geen game-server API nodig.
`scripts/build_leaderboards.py` leest lokale logbestanden en maakt
`leaderboards.json`. Op de game-detailpagina's wordt dit bestand opgevraagd.
Als het niet bestaat, blijft de bestaande handmatige `games.json`-scorelijst werken.

## Wat werkt er?

| Game | Bron | Kolom | Status |
| --- | --- | --- | --- |
| Xonotic | `sv_logscores_file` `:scores:` / `:labels:` / `:player:` / `:end` | Score | Getoetst aan de aangeleverde Uplink-logindeling |
| OpenArena | Quake III `g_log` `Exit:` / `score:`-regels | Score | Parser + fixtures; echte serverlog nog controleren |
| AssaultCube | `fragged`-meldingen uit server-/syslog | Frags (events) | Experimenteel: eerste echte log nodig voor definitieve betrouwbaarheid |

**Let op:** dit zijn geaggregeerde scores per nickname. Voor Xonotic gebruiken we de echte scorekolom en niet het aantal kills. Een naamswijziging
maakt een nieuwe speler. Xonotic frags, OpenArena matchscores en AssaultCube
fragmeldingen zijn **verschillende metrieken**. Maak er geen gezamenlijke
ranglijst van zonder normalisatie. Onvoltooide Xonotic matches worden genegeerd.
AssaultCube telt alleen herkende `fragged`-events en bevat dus mogelijk niet
alle punten uit de echte scoreboard (gibs, teamkills, CTF, enzovoort).

## 1. Zet serverlogs aan

**Xonotic**, voeg toe aan je serverconfig en herstart de gameserver:

```cfg
sv_logscores_file 1
sv_logscores_filename "scores.log"
sv_logscores_bots 0
```

Voorbeeld Xonotic scores.log (het formaat dat de parser ondersteunt):

```text
:scores:dm_nexdm01:131
:player:10:3:130:1:Lex
:player:4:8:129:1:Guest
:end
```

De parser ondersteunt ook de gelabelde `:player:see-labels:`-regels uit de Uplink-`scores.log`. Hij leest de `score!!`-kolom als **Score** (in de testwedstrijd: 30); `kills` is een aparte kolom (31). Een ander, niet-gelabeld eventlog-formaat is niet automatisch hetzelfde.

**OpenArena**, in je serverconfig:

```cfg
seta g_log "games.log"
seta g_logSync "1"
```

Controleer of de log na een wedstrijd `Exit:` en `score:` met
`ping:`, `client:` en `name:` bevat. Verander instellingen alleen
als ze door jouw OpenArena-versie worden ondersteund.

**AssaultCube** logt op Linux doorgaans via syslog/journald. Zorg dat de
serverlogs naar een leesbaar **bestand** worden geëxporteerd. Inspecteer
`fragged`-regels van jouw versie; de parser herkent bijvoorbeeld:

```text
[192.0.2.10] Lex fragged Guest
```

Dat is een **voorbeeld voor het parsercontract**, niet een bevestigde regel
uit jouw server. Ontbreekt dit patroon, dan blijft het leaderboard leeg
tot de parser op echte logs is afgestemd. Stuur hiervoor enkele
geanonimiseerde frag-/scorelogregels.

## 2. Maak de logs bereikbaar op de webserver

Het script kan alleen paden lezen die bereikbaar zijn **op de machine
waarop het draait**. Omdat de drie games in afzonderlijke containers
draaien, moet je de logbestanden beschikbaar maken op de webserver
(bijvoorbeeld read-only mounts of periodieke kopieën via SSH). Zet
alleen logbestanden over, niet de hele gameconfig, en publiceer ruwe logs
niet onder de webroot. IP-adressen en chat kunnen erin staan.

Controleer met `ls -lh <pad>` dat de bestanden bestaan en leesbaar zijn.
De werkelijke paden verschillen per installatie.

## 3. Eenmalig draaien

Voer dit commando uit vanuit de map met `game.html` op de **webserver**,
en vervang de drie voorbeeldpaden door echte logbestanden:

```bash
python3 scripts/build_leaderboards.py \
  --xonotic /pad/naar/xonotic/scores.log \
  --assaultcube /pad/naar/assaultcube/server.log \
  --openarena /pad/naar/openarena/games.log \
  --output ./leaderboards.json
```

Je kunt één of twee argumenten weglaten om slechts die games te
verversen; bestaande scores voor de andere games blijven behouden.

Open `leaderboards.json`. Het resultaat heeft bijvoorbeeld deze structuur:

```json
{
  "games": {
    "xonotic": {
      "label": "Frags",
      "players": [
        {"name": "Lex", "score": 10},
        {"name": "Guest", "score": 4}
      ],
      "updated": "2026-11-15T15:00:00+00:00"
    }
  }
}
```

De timestamps zijn illustratief; het script gebruikt de werkelijke UTC-tijd.
De uiteindelijke JSON wordt atomair vervangen. Bij ontbrekend log stopt
het script zonder bestaande data te overschrijven.

## 4. Automatisch verversen

Wanneer het handmatig werkt, kun je elke minuut een cronjob toevoegen.
Gebruik **absolute paden** voor script, logs en output. Bijvoorbeeld:

```cron
* * * * * /usr/bin/python3 /var/www/uplink/scripts/build_leaderboards.py --xonotic /pad/xonotic/scores.log --assaultcube /pad/assaultcube/server.log --openarena /pad/openarena/games.log --output /var/www/uplink/leaderboards.json
```

Zorg dat de cron-gebruiker leesrechten heeft op de logs en schrijfrechten
op `leaderboards.json`. Gebruik bij meerdere handmatige/scheduled runs
een lock zoals `flock`. Publiceer `leaderboards.json` via Nginx naast de
HTML. `leaderboards.json` staat in `.gitignore` en wordt bewust **niet**
naar GitHub gepusht.

## 5. Lokaal testen (Windows)

```powershell
py -m unittest discover -s tests -v
py -m http.server 8000
```

De automatische scores verschijnen alleen wanneer er een
`leaderboards.json` naast `game.html` bestaat. Als die ontbreekt, blijven
bestaande handmatig ingevulde scores zichtbaar. Voor de daadwerkelijke
serverintegratie moeten de echte logs worden geïnspecteerd en vergeleken
met het spel-scoreboard, vooral bij AssaultCube.

## Referenties

- Xonotic: https://github-wiki-see.page/m/xonotic/xonotic/wiki/Score-logging
- OpenArena: Quake III engine `g_log` server-logformat
- AssaultCube serverlogs: https://assault.cubers.net/docs/server.html
- AssaultCube logbeperkingen: https://github.com/ActionFPS/game-log-parser
