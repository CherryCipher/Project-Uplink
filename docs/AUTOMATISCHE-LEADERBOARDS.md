# Automatisch verversen: elke vijf minuten

De statische Uplink-site blijft ongewijzigd. Een `systemd`-timer op de
**webserver 192.168.222.30** haalt via SSH de scorelogs van de gamecontainers
op. Het Python-script verwerkt uitsluitend geslaagde downloads en publiceert
`/var/www/html/leaderboards.json`. Geen database of internet nodig.

## Inbegrepen bronconfiguratie

In `config/leaderboard-sources.json`:

- **Xonotic (.100): aan** — werkende `uplinklogs`-account en SSH-sleutel
  `/root/.ssh/id_ed25519_uplink`; bewezen scorepad
  `/home/xonotic/.xonotic/data/data/scores.log`
- **AssaultCube (.101): uit** — vul eerst het echte logpad in, maak een
  SSH-leesaccount en sleutel en valideer de parser met werkelijke logregels
- **OpenArena (.103): uit** — idem

Geen credentials in JSON. Voor extra games met reeds ondersteunde parser:
voeg een entry toe met de game-id, zet `enabled` op `true` zodra de
SSH-verbinding en het logbestand zijn getest. Voor een nieuwe game met een
ander logformaat is ook een parser nodig. Elke game gebruikt de eigen sleutel.

## Eerste installatie op de Uplink-webserver

1. Merge de PR op GitHub en zorg dat de bestanden op de webserver onder
   `/var/www/html` zijn bijgewerkt. Gebruik je bestaande deploymentmethode.
2. Controleer de bestaande SSH-verbinding met Xonotic:

   ```bash
   ssh -i /root/.ssh/id_ed25519_uplink -o BatchMode=yes \
     uplinklogs@192.168.222.100 \
     "cat /home/xonotic/.xonotic/data/data/scores.log" | tail -n 5
   ```

3. Test de Python-updater handmatig **op de webserver**:

   ```bash
   python3 /var/www/html/scripts/poll_leaderboards.py \
     --config /var/www/html/config/leaderboard-sources.json
   cat /var/www/html/leaderboards.json
   curl -I http://127.0.0.1/leaderboards.json
   ```

   HTTP 200 is vereist. De updater plaatst een leesbaar bestand met mode
   `0644`, ook bij iedere daaropvolgende verversing. Hij schrijft via
   een tijdelijk bestand en een atomische vervanging.

4. Installeer de meegeleverde systemd-units (als root):

   ```bash
   install -m 644 /var/www/html/deploy/systemd/uplink-leaderboards.service /etc/systemd/system/
   install -m 644 /var/www/html/deploy/systemd/uplink-leaderboards.timer /etc/systemd/system/
   systemctl daemon-reload
   systemctl enable --now uplink-leaderboards.timer
   ```

5. Controleer of het schema actief is:

   ```bash
   systemctl list-timers --all | grep uplink-leaderboards
   systemctl start uplink-leaderboards.service
   systemctl status uplink-leaderboards.service --no-pager
   journalctl -u uplink-leaderboards.service -n 40 --no-pager
   ```

De timer voert een run uit ongeveer een minuut na boot en daarna **vijf
minuten na het einde van de vorige run**. Een mislukte gameserververbinding
verwijdert geen eerder gepubliceerde scoregegevens. Een succesvolle bron
wordt ook verwerkt als een andere bron niet bereikbaar is. Bij volledige
storing eindigt de service met foutstatus en blijft de vorige JSON behouden.

De service gebruikt in deze eerste versie root, omdat de reeds ingerichte
SSH-sleutel onder `/root/.ssh` staat. Gebruik deze sleutel uitsluitend voor
het beperkte `uplinklogs`-account; laat SSH-root-wachtwoordlogin uit.
Een aparte servicegebruiker met eigen sleutel is een latere hardening-optie.

## Een game toevoegen

1. Zorg dat de gameserver een geschikt logbestand schrijft.
2. Maak daar een gebruiker met alleen leesrechten en een SSH-sleutel.
3. Test vanaf de webserver `ssh -i /pad/naar/sleutel gebruiker@server "cat /pad/naar/log"`.
4. Vul bij de betreffende game in `config/leaderboard-sources.json`:
   `enabled`, `host`, `user`, `identity_file` en `remote_log`.
5. Test handmatig met het commando uit stap 3; pas daarna de timer toe.

## Lokaal testen

```powershell
py -m unittest discover -s tests -v
```

De updater kan ook vanuit een aparte Python-omgeving worden getest,
zonder toegang tot je Uplink-netwerk, via de toegevoegde mock-tests.

## Beperkingen

- De website vraagt de JSON op tijdens het openen/verversen van de
  gamepagina. Een reeds geopend browsertabblad werkt niet vanzelf live bij.
- De logs worden bij elke run volledig opnieuw verwerkt, niet vanaf een
  permanente positie. Dat voorkomt dubbel tellen, maar bij zeer grote logs
  kan een incrementele verwerking later zinvoller zijn.
- AssaultCube-statistieken blijven experimenteel tot we echte logregels
  hebben gecontroleerd.
- Logs en `leaderboards.json` staan niet in Git. De centrale updater
  maakt alleen de bewerkte score-JSON openbaar, niet de ruwe logs.


## OpenArena: bots uitsluiten

Gebruik in het OpenArena-blok van `config/leaderboard-sources.json` de optie
`exclude_names` (een lijst van nicknames). De updater vergelijkt namen
hoofdletterongevoelig en exact, na het weghalen van Quake-kleurcodes.
De beginnamenlijst is gebaseerd op bots uit de aangeleverde Uplink-logs:

```json
"exclude_names": [
  "Sarge", "Dark", "Angelyss", "Grism",
  "Grunt", "Penguin", "Major", "Beret"
]
```

Voeg nieuwe botnamen handmatig toe wanneer ze in de scorelijst verschijnen.
Een echte speler die exact dezelfde naam kiest, wordt ook weggefilterd.
Het is dus een eenvoudige naamfilter, geen betrouwbare identificatie van
botaccounts. Alleen OpenArena wordt momenteel gefilterd.

**Let op bij deployment:** de ingecheckte bronconfig heeft OpenArena nog op
`enabled: false` met een voorbeeld-logpad. De werkende configuratie op de
webserver heeft juist `enabled: true` en het echte pad
`/var/games/openarena-server/server.oa/baseoa/games.log`.
Overschrijf de werkende serverconfig dus niet blind vanuit Git; voeg alleen
de `exclude_names`-lijst toe. De timer leest die automatisch bij de volgende run.
