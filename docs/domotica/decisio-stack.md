# Decisió d'arquitectura — registre autoritzat

> ### 🟢 Revisió del 22/09/2026 — **la lògica v2 es codifica**
>
> La proposta de [logica-v2.md](logica-v2.md) passa a ser la lògica de control, i es codifica
> segons [logica-v2-pla.md](logica-v2-pla.md): per fases, **primer en ombra**. El que canvia
> d'aquest document:
>
> | | Abans | Ara |
> |---|---|---|
> | **Què decideix** | `sensor.decisio_del_soterrani` amb la v1 | **El mateix sensor, amb la v2**: el `unique_id` es manté. La lògica passa a una macro (`custom_templates/decisio.jinja`) que el sensor, ara **per disparador**, avalua **un sol cop**: l'estat i el motiu ja no es poden desquadrar |
> | **On viu** | `packages/rosada.yaml` | `packages/control.yaml` (paràmetres, modes, decisió, executors). `rosada.yaml` es queda la física |
> | **Qui governa el deshumidificador** | L'endoll P110M, i el `humidifier` només per llegir i ajustar («dos amos no») | **El `humidifier`, pel llindar**, a posta. L'endoll mesura i **no s'apaga mai** (principi 6 de la v2) |
> | **Enclavament** | Dur: o ventilador o deshumidificador (tasca C.3 de [fases.md](fases.md)) | **Superat.** Mentre ventila, el deshumidificador es queda al 70 %; en urgència treballen tots dos |
> | **Actuar** | L'automatisme «encara no desplegat» era la Fase 0 | Dos interruptors explícits, `input_boolean.actuacio_deshumidificador` i `…_ventiladors`, **apagats** per defecte |
> | **Paràmetres** | `initial:` a tots | **Sense `initial:`**, i uns valors de partida que es posen un sol cop. Resol R2, confirmat llegint el codi de la 2026.9.3 |
>
> La resta del document es manté.

> ### 🟢 Revisió del 21/09/2026 — **canvia l'objectiu del projecte**
>
> Aquest document es va escriure amb un objectiu: **documentar les humitats per defensar la
> retenció de 3.000 € que venç el ~09/03/2027.** Tota l'arquitectura en sortia — el segell
> RFC 3161, el CSV diari immutable, el repositori d'arxiu, la congelació de versions.
>
> **L'objectiu passa a ser un altre: optimitzar el consum.** Saber quan val la pena obrir els
> ventiladors en comptes de fer anar el deshumidificador, en tres passos: **veure** (panell
> amb temps real i històric navegable), **decidir** (llindars amb dades pròpies) i **actuar**
> (muntar els S110E). La documentació per a un eventual plet queda **ajornada, amb la porta
> oberta**, i no s'hi inverteix temps ara.
>
> **Queda superat:**
>
> | | |
> |---|---|
> | Segell **RFC 3161** diari | Una peça externa per a una garantia que ara no fa falta |
> | Repositori **`Local-data`** + clau de desplegament | Infraestructura per arxivar el que no s'ha de defensar |
> | **CSV diari immutable** amb SHA-256 i `meta.json` | Igual |
> | **Test de deriva** rèplica contra producció | Existia per demostrar que la lògica no havia canviat pel camí |
> | **Congelació de versions fins al 10/03/2027** | El seu únic motiu era no tenir forats a la finestra probatòria |
> | **«Panell web: no n'hi ha»** | Es reobre. Primer taulers natius; si no hi arriben, panell propi servit per HA des de `config/www/` |
> | Rebuig de **components de tercers** | Fora de la finestra probatòria, una targeta de front-end per HACS deixa de ser un risc |
>
> **Es manté, perquè és gratis i és l'única cosa irreversible:**
>
> - ⚠️ **`purge_keep_days: 730` i gravar les dades crues.** Ja està posat i no costa res. Si
>   algun dia es reprèn la via documental, caldran les dades d'aquest hivern, i **aquest
>   hivern passa un sol cop**. És el que manté la porta oberta a cost zero.
> - **Noms d'entitat fixats** (fets el 21/09/2026): renombrar més tard parteix les sèries.
> - **Còpies de seguretat**, simplificades: sense segells ni repositori a part. Perdre la base
>   de dades costaria també l'optimització, no només el plet.
>   *Precisat el mateix 21/09/2026:* el **tarball xifrat setmanal** (`.storage`,
>   `secrets.yaml`, `matter-data/`, ~1 MB) **segueix sortint del local**, perquè el seu motiu
>   mai no va ser probatori —perdre `matter-data/` obliga a reemparellar, i reemparellar
>   parteix totes les sèries—. Anava a `Local-data`: **destí per decidir**. L'**històric**, en
>   canvi, es queda només al disc USB del local.
>
> **El que això canvia del calendari:** el ~09/03/2027 deixa de governar cada decisió. Segueix
> sent rellevant —l'hivern és quan la disjuntiva ventilar/deshumidificar es juga— però una
> setmana de retard ja no és una pèrdua irreparable.

> ### 🔄 Revisió del 20/09/2026 — maquinari real
>
> El maquinari ja estava comprat quan es va prendre aquesta decisió. Queden **superades** tres
> files de la taula, i la resta es manté:
>
> - **Ràdio: ZHA + SLZB-06 → FORA.** Els sensors són **Tapo T310/T315 amb hub H110**, que
>   parlen per **868 MHz sub-GHz**, amb millor penetració en formigó que el Zigbee de 2,4 GHz.
>   Desapareix la prova de cobertura i la decisió irreversible d'emparellament.
> - **🔴 Revisió del 21/09/2026 — la via al hub és Matter, no `tplink`, i l'stack passa a
>   dos contenidors.** El H110 xifra amb **TPAP**, i la biblioteca que porta HA 2026.9.3
>   (`python-kasa` 0.10.2) només coneix KLAP, AES i XOR: la integració `tplink` el rebutja amb
>   *«Unsupported device»*. És un problema obert d'upstream
>   ([`python-kasa#1590`](https://github.com/python-kasa/python-kasa/issues/1590)), no una
>   configuració nostra. De les tres sortides —esperar upstream (sense data, i el calendari
>   s'acaba al març), un component de tercers per HACS (que aquest document rebutja dins la
>   finestra probatòria) o **Matter**— es tria Matter: el hub l'anuncia a la xarxa, comprovat
>   per mDNS. **Costa un segon contenidor i a canvi l'accés al hub passa a ser completament
>   local:** sense el núvol de Tapo, sense credencials de compte i sense res que caduqui. Per
>   al valor probatori és millor que el pla original. El detall és a la capçalera de
>   `docker-compose.yml`.
> - **Deshumidificador: verificació resolta.** El **Qlima D 825 PA Smart** (470 W, 25 L/dia,
>   bomba de condensats, higròstat 40–80 %) **es reprèn sol després d'un tall de corrent**.
>   L'arquitectura (a) queda confirmada, i **no s'integra per Tuya**: l'higròstat propi regula
>   i el **Tapo P110** el governa i en mesura el consum.
>   🔄 ***21/09/2026 — el «no s'integra per Tuya» es reobre.*** `tuya-local` ja no demana
>   compte de desenvolupador, i el rebuig dels components de tercers ha caigut amb el canvi
>   d'objectiu. Es **prova**; si reconeix el D825, al principi només per llegir-ne l'estat i
>   ajustar-ne el llindar. **El P110 es queda** com a mesura i com a actuador de la lògica.
>   L'arquitectura (a) no canvia.
>
>   ✅ ***21/09/2026, al vespre — la prova 0.2b, superada.*** Tallant l'endoll un minut,
>   l'aparell **recorda el mode, el llindar i la velocitat** i es reprèn sol: **l'arquitectura
>   (a) queda confirmada del tot**. Amb un matís que obliga: **en mode AUTO l'aparell no fa cas
>   del llindar**, o sigui que la configuració de repòs ha de ser **Manual** →
>   [deshumidificador.md](deshumidificador.md).
>
> El detall és a **[inventari.md](inventari.md)**.

> **Aquest document mana.** Recull la decisió presa el **20 de setembre de 2026** després d'un
> procés de tres propostes independents, dues crítiques adversarials (senzillesa i robustesa)
> i una síntesi arbitral.
>
> Quan aquest document contradigui una proposta anterior de `docs/domotica/`, **mana aquest**.
> Les propostes es conserven perquè contenen el raonament, no perquè segueixin vigents.

> Àrbitre. Tot el que segueix és decisió presa, no opció. Prioritat aplicada, en aquest ordre: **(1) que no es perdin dades, (2) que funcioni desatès, (3) gratuït, (4) poc codi.**

**Correcció de premissa que governa tot el document, i accepto la de la Crítica 2:** avui és 20/09/2026 i la retenció venç el ~09/03/2027. Són **5,5 mesos i un sol hivern**. Això inclina totes les decisions ajustades cap a «munta-ho ja i congela-ho», i converteix la política d'actualitzacions en **cap actualització fins al 10 de març de 2027**.

**Resolució del conflicte Fase 0 / grup de control que ningú ha vist:** la clàusula QUINTA obliga que els sistemes de ventilació **romanguin operatius**. Per tant durant la Fase 0 els ventiladors **no s'aturen**: es deixen en el règim actual (continu), es mesura, i el sensor de decisió registra què *hauria* fet sense accionar res. El grup de control i el deure legal coincideixen. No hi havia dilema.

---

## Decisions

| Component | Decisió | Llenguatge/eina | Per què |
|---|---|---|---|
| **Sistema base** | Linux Mint + Docker CE del repo oficial; sense suspensió, *restore on AC power loss*, `systemd-time-wait-sync` actiu, rotació de logs, `unattended-upgrades` només seguretat a les 04:30 excloent `docker-ce*` | config del sistema | És el que ja s'està fent i deixa el host de propòsit general que tot el desplegament necessita |
| **Instal·lació de HA** | **HA Container**, versió fixada, congelada fins al 10/03/2027 | `docker-compose.yml` | Supervised s'actualitza sol i decideix per tu quan reiniciar HA; HA OS et pren el host i amb ell scripts, timers i git |
| **Stack de contenidors** | ~~Un. Només `homeassistant`~~ → **DOS**: `homeassistant` + `matter-server` *(imatge fixada per **digest**, no per etiqueta: no en publica cap de versió i «stable» es mou)* | YAML de compose (174 línies) | Segueix sense Postgres, que és el que estalviava `depends_on`, healthchecks i credencials. El segon contenidor no és una preferència: és l'únic camí local al hub que existeix avui. **Tots dos amb sostre de memòria** (1.536 + 512 MB de 3.716): amb la RAM soldada, el que evita que una fuita mati l'amfitrió és el sostre, no l'ampliació |
| **Base de dades de l'històric** | **SQLite**, `purge_keep_days: 730`, `commit_interval: 30`, `exclude` per **llistes explícites** (mai globs) | recorder d'HA | Amb arxiu CSV diari immutable a git, el motor deixa de ser el dipòsit de la prova i Postgres només compra un mode de fallada silenciós més |
| **Lògica de control** | **HA natiu.** Un **únic** sensor de plantilla `sensor.decisio_del_soterrani` és l'únic que avalua; l'automatisme només hi actua. `\| float` **sense valor per defecte** + `availability:` explícit. *(22/09/2026: la v2 en una macro que el sensor avalua un sol cop, a `packages/control.yaml` — vegeu la revisió de dalt)* | YAML + Jinja2, 1 fitxer `packages/rosada.yaml` | Un sensor de motiu que reavalua ment; un que decideix no pot mentir, i s'estalvia un subprocés cada 60 s i un fitxer d'estat paral·lel |
| **Exportador de dades** | **Un sol script nocturn** a les 03:40 (franja vall): `VACUUM INTO` → guardes → CSV.gz + SHA-256 → segell RFC 3161 → commit+push → disc extern → ping amb estat | Python 3 **stdlib** (`sqlite3`, `csv`, `gzip`, `hashlib`, `urllib`) + `systemd timer` amb `Persistent=true` | La instantània serveix alhora de còpia i de font d'exportació, i l'exportador és el **vigilant** de la base de dades |
| **Allotjament de les dades** | **GitHub `Local-data` privat**, un commit diari, **clau de desplegament SSH** (mai token) | git | Gratuït, fora del local, i un token que caduqués el gener de 2027 seria una fallada silenciosa just abans del venciment |
| **Panell web** | **No n'hi ha.** Dashboards natius d'HA + app Companion per Tailscale | cap | Cobreixen 4,5 dels 5 gràfics amb zero codi, zero allotjament i zero credencials; el mig gràfic que falta no val una pàgina, una llibreria i un esquema de fitxers |
| **Desplegament** | **`desplega.sh` llançat a mà per SSH** des de `main`. Mai `git clean` | bash `set -euo pipefail` (~80 línies) | N=1: Ansible, Makefile i CI són cerimònia; les baranes van al script perquè són el que s'oblida la nit que importen |
| **Còpies de seguretat** | Instantània `VACUUM INTO` + `.storage` + `secrets.yaml` + **`matter-data/`** → **disc extern USB al local** cada nit; **tarball xifrat de `.storage`+`secrets.yaml`+`matter-data/` a `Local-data` cada diumenge** (~1 MB) | `gpg --symmetric` + git | Perdre `.storage` obliga a reemparellar-ho tot, i reemparellar **parteix totes les sèries**: ha de tenir còpia fora del local encara que la BD no la tingui. ⚠️ **`matter-data/` hi entra pel mateix motiu i amb la mateixa urgència:** hi viuen les **claus** dels aparells emparellats. És al `.gitignore` perquè són secrets, cosa que el fa fàcil d'oblidar precisament a la còpia |
| **Supervisió de vida** | **healthchecks.io, dos checks**: `bategada` (host, cada 30 min, marge 3 h) i `nit` (dades, marge 26 h) **amb l'estat al cos del ping** | `curl` | Un sol bit no diu si has d'obrir l'SSH o agafar el cotxe; dos checks i un cos JSON converteixen l'avís en diagnòstic per tres línies |
| *(Accés remot)* | **Tailscale**, expiració de clau desactivada. Única via d'administració i de consulta | paquet `apt` | Ja decidit i correcte; CGNAT elimina la resta per física de xarxa |
| *(Ràdio)* | ~~ZHA + SLZB-06 per TCP~~ → **SUPERADA.** **Hub Tapo H110 + sensors T310/T315 per 868 MHz sub-GHz**, ja comprats i actius | **Matter** (via `matter-server`), no `tplink` | El maquinari ja hi era. El sub-GHz penetra millor el formigó que el Zigbee de 2,4 GHz, i desapareixen la prova de cobertura i l'emparellament irreversible. La via `tplink` va quedar tancada pel xifratge TPAP del hub — vegeu la revisió del 21/09 a dalt |
| *(Sensor que decideix el cas)* | **ESP32 + ESPHome + 2× DS18B20**, compilat **al portàtil de casa**, pujat per OTA | YAML d'ESPHome (~40 línies) | És l'únic sensor que discrimina condensació de capil·laritat i n'hi havia **un de sol** |

---

## Com interactuen

```
   868 MHz sub-GHz                             Wi-Fi — endolls i relés
 ┌────────────────────┐                      ┌────────────────────────────┐
 │ 5× T/HR T310/T315  │                      │ Tapo P110      (deshumid.) │
 │ 1× inundació T300  │                      │ Tapo S110E ×2  (vent.)     │
 └─────────┬──────────┘                      └─────────────┬──────────────┘
           │ sub-GHz                                       │ consulta local per IP
 ┌─────────▼─────────┐                                     │
 │  Hub Tapo H110    │   Matter (IPv6 + multidifusió)      │
 │  (IR + sub-GHz)   │─────────┐                           │
 └───────────────────┘         │                           │
              ┌───────────────▼──────────────┐             │
              │ CONTENIDOR  matter-server    │             │
              │ (digest fixat · ./matter-data│             │
              │  = CLAUS dels emparellats)   │             │
              └───────────────┬──────────────┘             │
                              │ WebSocket local            │
 ESP32 + 2×DS18B20 ── API ESPHome (TCP) ──────┐            │
 (T superfície paret)                         │            │
                              ▼               ▼            ▼
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  CONTENIDOR  homeassistant   (imatge fixada · un dels DOS de l'stack)    │
 │                                                                          │
 │   packages/rosada.yaml   ← YAML + Jinja2, ~566 línies, UN fitxer         │
 │     sensor.soterrani_*_td, sensor.delta_td, sensor.marge_superficie      │
 │     sensor.decisio_del_soterrani   ◀── ÚNIC punt d'avaluació                 │
 │     automation manual:  llegeix la decisió → escriu switch → escriu      │
 │                         input_datetime d'estat   (la UI NO pot           │
 │                         reescriure aquest fitxer)                        │
 │                                                                          │
 │   recorder ──▶ /config/home-assistant_v2.db   (SQLite, WAL)              │
 └──────────────────────────────────┬───────────────────────────────────────┘
                                    │ ① sqlite3 "VACUUM INTO"  (stdlib, 03:40)
                                    ▼
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  nit.py — Python 3 stdlib · systemd timer (Persistent=true)              │
 │                                                                          │
 │  ② GUARDES sobre la instantània (aborten sorollosament):                 │
 │       PRAGMA quick_check · versió d'esquema · max(ts) < 2 h ·            │
 │       min(ts) NO ha saltat endavant (guarda de purga) ·                  │
 │       cap fila al futur, marques monòtones · mostres/hora per sensor     │
 │  ③ SQL (~40 línies) → arxiu/AAAA-MM-DD.csv.gz  (ISO8601+offset i epoch)  │
 │       + SHA256SUMS + meta.json (esquema, versió HA, SHA del commit)      │
 │  ④ openssl ts -query | curl → TSA gratuïta → .tsr   (RFC 3161)           │
 │  ⑤ git commit && push          ⑥ rsync → disc USB   ⑦ curl amb COS       │
 └────────┬─────────────────────────────┬──────────────────────┬────────────┘
          │ git+ssh (clau desplegament) │ SATA/USB             │ HTTPS
          ▼                             ▼                      ▼
   GitHub Local-data (privat)     disc extern al local   healthchecks.io ──▶ correu
   ~20 KB/dia · 1 MB/setmana      14 diàries + 8 setm.   COS = mode, edat de
                                                          l'última fila, disc,
                                                          bateria, deriva rellotge

   bategada.sh (bash, 3 línies, cada 30 min) ── curl ──▶ healthchecks.io #2
   ─────────────────────────────────────────────────────────────────────────
   CONSULTA I OPERACIÓ

   Mòbil/PC fora ── WireGuard (Tailscale) ──▶ 100.x.y.z:8123 ─▶ dashboards natius
   Mòbil/PC fora ── HTTPS ──▶ github.com/…/Local-data ─▶ CSV d'ahir (diagnòstic
                                                          si el local és mort)
   Casa (Windows) ── git push ──▶ GitHub Local ──┐
   Casa (Windows) ── SSH (Tailscale) ──▶ ./scripts/desplega.sh ──┘ git pull --ff-only
```

**`desplega.sh`, en ordre (cada pas és una barana, no una comoditat):**
1 avorta si l'arbre és brut o si l'últim CSV té més de 48 h · 2 anota commit i etiquetes actuals · 3 `git pull --ff-only` · 4 `docker compose config -q` i `pull` · 5 **`check_config` contra la imatge NOVA en un contenidor d'un sol ús** (`docker compose run --rm --entrypoint python …`; fer `exec` valida amb la imatge vella) · 6 verifica que tots els `sensor.`/`input_number.` referenciats al YAML existeixen a `/api/states` · 7 `up -d` · 8 **comprova que `sensor.decisio_del_soterrani` existeix i és fresc** — «esperar que HA respongui» no serveix, HA arrenca perfectament amb un automatisme trencat · 9 escriu una línia al `desplegaments.log` dins de l'arbre de `Local-data` (el commit nocturn se l'endú) · 10 revertir i avisar si falla.

---

## Recompte de peces

| | Peces mòbils | Sintaxis |
|---|---|---|
| Suma de les tres propostes (recompte de la Crítica 1) | **30** | **11–12** |
| Proposta A tota sola | 10 | 8 |
| Mínim de la Crítica 1 | 9 | 5 |
| **AQUESTA DECISIÓ** | **12** | **8** |

**Al local (8):** host Mint+Docker · contenidor HA · **contenidor `matter-server`** · `tailscaled` · **hub Tapo H110** · node ESPHome · timer+`nit.py` · timer+`bategada.sh`.
**Fora (4):** GitHub `Local` · GitHub `Local-data`+clau · healthchecks.io (2 checks) · TSA RFC 3161 (sense compte).

> ℹ️ **D'11 peces a 12, i per què.** El coordinador **SLZB-06 ja no hi és**, però la peça no
> desapareix: la substitueix el **hub H110**, igual de crític —si mor, deixen d'arribar les
> lectures dels sis sensors— i igual de mantenible. La dotzena és el **contenidor
> `matter-server`**, que entra el 21/09/2026 perquè `tplink` rebutja el hub. És una peça que
> no es volia, i es paga a canvi de treure'n una altra que no es comptava: **el núvol de Tapo
> i les credencials del compte**, que eren un punt de fallada fora del local i amb caducitat.

**Sintaxis (8):** Python · bash · YAML d'HA · Jinja2 · YAML de compose (174 línies) · YAML d'ESPHome (40 línies) · SQL (40 línies dins de `nit.py`) · unitat systemd.

**Fitxers que editaràs de debò: disset.** L'estimació original deia cinc i **~635 línies**; el
recompte real, mesurat el **21/09/2026**, és més del triple:

- *Ja escrits (**~7.421 línies**):* `packages/rosada.yaml` (**639**), `packages/consum.yaml` (214), `custom_templates/tarifa.jinja` (91), `packages/control.yaml` (1029), `custom_templates/decisio.jinja` (266), `custom_templates/executors.jinja` (126), `custom_templates/ventiladors.jinja` (29), `custom_templates/calibratge.jinja` (69), `packages/deshumidificador.yaml` (289), `tools/analisi.py` (585), `tools/tarifa.py` (211), `tools/calibratge.py` (1236), `tools/replica.py` (1150), `scripts/comprova.sh` (368), `scripts/prepara-host.sh` (270), `scripts/instala-tuya-local.sh` (87), `tools/valida_xifres.py` (249), `docker-compose.yml` (**174**), `scripts/inicia-serie.sh` (168), `tools/valida_yaml.py` (100), `config/configuration.yaml` (71).
- *Per escriure (**~420**):* `nit.py` (~300), `desplega.sh` (~80), `esphome/soterrani.yaml` (~40).

**~7.841 línies en total.** *(Els tres fitxers del consum i la tarifa, i el de `tuya-local`, hi van entrar el 21/09/2026, després del recompte; els de la lògica v2, el 22/09/2026, quan la decisió i els paràmetres van passar de `rosada.yaml` a `control.yaml` i `rosada.yaml` es va quedar la física.)* La desviació més grossa és de `rosada.yaml`: les ~200 línies
estimades no comptaven ni els comentaris, ni les guardes d'`availability:`, ni els blocs
d'`utility_meter` i `history_stats`. La resta són **eines de verificació i de frontera** que
l'estimació no preveia perquè no preveia que calguessin: comprovar el host, validar el YAML
des de casa i tancar l'experimentació abans que comenci la sèrie que val com a prova.

Sóc **tres** peces i tres sintaxis per sobre del mínim de la Crítica 1: **SQL** (perquè em nego a vigilar la base de dades des d'una API que no la llegeix), **ESPHome** (perquè és el sensor que decideix el cas) i el **`matter-server`** (que no vaig triar: el va imposar el xifratge del hub). Contra la suma de les tres propostes: **−18 peces, −4 sintaxis**.

---

## El que s'ha DESCARTAT i per què

**Base de dades i contenidors**
- **PostgreSQL** (Proposta A, `monitoritzacio.md`) — el seu únic avantatge real és Grafana en viu, i el paga amb vuit artefactes que només existeixen per fer-lo inofensiu.
- **MariaDB** (`monitoritzacio.md`) — tots els costos de Postgres i cap avantatge tret de més receptes copiables.
- **Mosquitto i Zigbee2MQTT** (`desplegament.md`) — segueixen fora: amb el sub-GHz de Tapo no hi ha ni Zigbee ni MQTT a la casa. ⚠️ Però l'argument «i així l'stack és d'un sol contenidor» **ja no val**: el `matter-server` n'és un segon. El que es manté és que MQTT no aportaria res que Matter no doni.
- **Contenidor d'ESPHome al local** (Proposta A) — només cal per compilar; es compila a casa i es puja per OTA.
- **Grafana** (`monitoritzacio.md`, A, C) — fora del pla, no «ajornat»: una peça ajornada que justifica una decisió d'avui no és gratuïta. Si cal per al dossier, viu al portàtil de casa contra els CSV.
- **InfluxDB, VictoriaMetrics, TimescaleDB, `ltss`, Prometheus** — problema equivocat, ja descartats bé al repositori.
- **Portainer, Watchtower, Uptime Kuma, proxy invers** (A els descarta) — subscrit; Watchtower és actiu perjudicial: actualitzacions no planificades = forats a l'històric.
- **HA OS i HA Supervised** (`home-assistant.md`) — el primer et pren el host, el segon decideix ell quan reiniciar HA.

**Lògica**
- **`decisio.py` + `command_line` en producció** (Proposta B) — el pont per `argv` renderitzat és el pitjor punt de tall possible, i el fitxer d'estat paral·lel és una peça nova crítica per a la seguretat d'un compressor. **La funció pura es queda com a eina offline**, que és on era el seu argument fort.
- **Node-RED, AppDaemon, pyscript, servei Python propi** (`control-punt-rosada.md`, B) — contenidor extra, procés que mor en silenci, `custom_component` de tercers dins la finestra probatòria, o fontaneria autoescrita.
- **`input_boolean.mode_prova`** (`control-punt-rosada.md`) — no cal un helper: la Fase 0 és senzillament que l'automatisme d'actuació encara no està desplegat.

**Publicació i panell**
- **Cloudflare R2 + domini propi + Cloudflare Access** (recomanació vigent de `publicacio-dades.md`) — incompleix «gratuït» (Access exigeix domini, ~12 €/any) i fica un tercer que desxifra TLS sobre dades amb valor legal, objecció que el mateix repositori fa servir contra Cloudflare Tunnel. És la sobreenginyeria més cara del conjunt.
- **GitHub Pages** (`acces-remot.md`) — privat amb control d'accés és de pagament; públic és publicar els patrons d'ocupació.
- **GitHub Releases** (`publicacio-dades.md`) — resol un problema que no tenim: tot l'arxiu són ~20–30 MB.
- **Panell estàtic + uPlot + `tailscale serve`** (Proposta C) — es recupera quan hi hagi dolor **mesurat** sobre la SIM, no abans; l'estat de `tailscale serve` a més viu al dimoni i no a git.
- **CDN i qualsevol pas de compilació (`npm`, empaquetador, framework)** (C els prohibeix) — subscrit i és la millor decisió de mantenibilitat del bloc: sense `package.json` no hi ha res que es podreixi.
- **Ritual mensual CSV+SHA-256** (`monitoritzacio.md`) — el substitueix el commit nocturn, cada dia i amb segell.
- **Canal d'ordres per `ordres.json`** (`acces-remot.md`) — mort; Tailscale ja ho resol.
- **Nabu Casa, port forwarding, WireGuard pur** — ja resolts per CGNAT i per Tailscale.

**Operació**
- **`restic` + B2/R2** (Proposta A) — protegiria fora del local una cosa que ja és fora del local; el que quedava per protegir (`.storage`) hi va pel commit setmanal xifrat.
- **Restauració de prova mensual automàtica i `check --read-data-subset` setmanal** (A) — assegurança sobre assegurança; queda **una** restauració manual al principi.
- **GitHub Actions** (A, B) — quatre eines per a dos scripts; les portes reals del desplegament són estrictament més fortes i la CI no les pot executar.
- **Ansible, Makefile, `cron`, `shell_command` d'HA per a l'exportació, contenidor per a l'exportador** — N=1; mnemònics; passades perdudes en silenci; acoblar l'exportació a la salut d'HA just quan menys ho vols.
- **`psql --csv` amb `subprocess` i psycopg** (Proposta C) — cauen amb Postgres; amb SQLite és `sqlite3` de la stdlib i el codi és més curt.
- **Endoll intel·ligent de rearmada del router** (A) — ajornat: un router penjat costa un viatge, no costa dades. I quan es faci, sense el switch no gestionat de 12 € de la Crítica 2 és decoratiu, perquè el **hub** penja del mateix router.

---

## On he donat la raó a la crítica de robustesa per sobre de la de senzillesa

**Peces extra que accepto conscientment perquè el risc ho justifica:**

1. **L'exportador llegeix la base de dades, no l'API REST.** La Crítica 2 troba el forat fatal de la Proposta A: `/api/states` llegeix la màquina d'estats **en memòria**, i si el `recorder` mor el check pitarà verd durant setmanes mentre no s'escriu ni una fila. Això costa mantenir SQL al projecte. El pago sense dubtar: la baula més cara no pot quedar fora de la cadena.
2. **Dos checks en comptes d'un, i estat al cos del ping.** Contra la Crítica 1 i contra el disseny en cadena d'A. Tres línies converteixen «no ha arribat el ping» en «host viu + dades mortes → obre l'SSH» o «tots dos morts → cotxe».
3. **Guarda de `purge_keep_days`.** Cinc línies (`min(last_updated_ts)` que salta endavant) contra l'únic mode de fallada que pot **destruir el projecte sencer** en silenci i sense arreglada. Cap de les cinc peces originals la tenia.
4. **Segell RFC 3161 diari.** Una peça externa més. La datació per commit la posa **el teu portàtil**, i l'esdeveniment de push de GitHub no arriba viu al març de 2027. És un `curl` per nit i és el que fa que l'arxiu aguanti una impugnació.
5. **Tarball xifrat de `.storage` fora del local cada setmana.** La Crítica 2 té raó que la Proposta C aïllada no és autosuficient: una mort del disc sense `.storage` obliga a reemparellar i **parteix totes les sèries**, que és l'esquerda declarada inadmissible.
6. **Segon DS18B20 i ESPHome dins del projecte.** Entra un segon ecosistema i una tercera sintaxi YAML per 3 € de sensor. Ho accepto: era el component que decideix el cas i no tenia redundància.
7. **`systemd-time-wait-sync` abans d'arrencar HA.** Contra un CMOS mort que injectaria un bloc de files datades el 2015 al mig de la sèrie: silenciós, verinós i irreparable sense edició manual.
8. **Automatismes en un fitxer que la interfície no pot reescriure** (`automation manual:`). Sense això, un toc a l'editor visual embruta l'arbre i el pas 1 de `desplega.sh` bloqueja tots els desplegaments futurs.
9. **Cua, reintents i marges generosos.** La fatiga d'alertes és la manera més probable que mori la vigilància: una caiguda de SIM no genera alerta, i el push només falla després de dues nits seguides.

**On sacrifico robustesa per simplicitat — riscos que acceptes conscientment:**

1. **SQLite en comptes de Postgres.** *Risc acceptat:* una apagada bruta amb la bateria morta pot corrompre el fitxer i HA n'obriria un de buit — **sèrie viva partida**, no només un forat. *Per què igualment:* el corpus probatori és el CSV diari immutable a git, i la pèrdua màxima queda acotada a **24 h**; la detecció arriba la nit següent per `quick_check` + frescor. La Crítica 2 té raó que el mode de fallada equivalent existeix als dos motors; un cop el detector està al lloc correcte, l'avantatge de Postgres es redueix a la recuperació neta per WAL, i això es compra millor amb **un SAI de 50 €** que amb un contenidor durant 5,5 mesos.
2. **Cap magatzem d'objectes extern.** *Risc acceptat:* un incendi o robatori al local costa fins a 24 h de dades i la configuració posterior a l'últim diumenge.
3. **Cap panell publicat i cap URL per a tercers.** *Risc acceptat:* cal l'app de Tailscale i no pots passar un enllaç a un pèrit. Quan calgui, es resol amb un correu amb el CSV i un PDF, que és el que un pèrit obrirà.
4. **Cap CI.** *Risc acceptat:* una regressió d'estil arriba al local; les portes del desplegament, que són més fortes, l'aturen abans de reiniciar res.
5. **Cap rearmada elèctrica del router.** *Risc acceptat:* un router 4G penjat = un viatge en cotxe. HA segueix gravant: no costa prova.
6. **Duplicació entre el YAML de decisió i la funció de rèplica offline.** ~3 comparacions escrites dues vegades. *Mitigació que la converteix en invariant comprovable:* la rèplica es passa sobre el període ja gravat i **es compara amb els valors registrats de `sensor.decisio_del_soterrani`**; qualsevol divergència vol dir que les dues implementacions han derivat. ~20 línies de test.
7. **Cap restauració de prova automàtica.** Una de manual al principi, i prou.
8. **Punts únics acceptats sense redundància:** portàtil, disc, **hub Tapo H110**, router de la SIM, compte de Tailscale, compte de GitHub.

---

## Ordre d'implementació

### Bloc 0 — Física i decisions irreversibles (ABANS de comprar res)
1. **Prova de fum del camí de l'aire de reposició.** Si entra per fissures en contacte amb el terreny, **el ventilador pot estar empitjorant les humitats** i el projecte canvia de naturalesa. Costa un paperet i val més que tot el que segueix.
2. Comprovar si el **deshumidificador arrenca sol** després d'un tall de corrent, si desguassa per tub, i la seva placa de característiques.
3. **Paret més freda i humida** amb termòmetre IR de mà → allà van els DS18B20.
4. ~~**Prova de cobertura Zigbee de 48 h** i decidir ZHA vs Z2M.~~ ✅ **SENSE OBJECTE:** no hi ha Zigbee. Els Tapo van per **868 MHz** amb el hub H110 i la integració `tplink` els consulta localment. Queda només **confirmar on és cada sensor** i que el de fora està protegit de la pluja.
5. **Salut del portàtil:** SMART del disc, `energy_full` de la bateria, pila CMOS, si té Ethernet. Si la bateria és morta → **SAI de 50 €**, no Postgres.
6. **Ubicació física del portàtil: planta baixa, aixecat de terra, ventilat.** Mai al soterrani humit.

### Bloc A — ABANS DE CONNECTAR EL PRIMER SENSOR *(res d'això té arreglada a posteriori)*
7. Host: sense suspensió (`logind.conf` **i** l'entorn d'escriptori de Mint, més `systemctl mask sleep.target …`), *restore on AC power loss*, `Europe/Madrid`+NTP, `systemctl enable systemd-time-wait-sync`, rotació de logs de Docker, reserves DHCP per al portàtil i el **hub H110**.
8. **Tailscale amb l'expiració de clau desactivada.**
9. Repos: `Local` (públic, ja existeix) i `Local-data` (privat) + **clau de desplegament SSH**. **`.gitattributes` amb `* text=auto eol=lf`** — codifiques des de Windows i un `desplega.sh` amb CRLF peta amb `bad interpreter: /bin/bash^M`.
10. `docker-compose.yml` amb **versió d'HA fixada** i `recorder` amb **`purge_keep_days: 730`**, `commit_interval` elevat i `exclude` per llistes explícites.
11. **Conveni de noms d'entitat definitiu** (`sensor.soterrani_nord_temperatura`) escrit al repositori abans d'emparellar res.
12. `nit.py` + les dues unitats systemd + els dos checks de healthchecks.io **funcionant en buit**, amb el primer commit d'arxiu fet i **una restauració de prova manual verificada**.
13. `desplega.sh` amb totes les portes.
14. **24 h amb tots els sensors junts a la mateixa habitació** abans d'instal·lar-los: desviació respecte de la mediana → *offset* fix a HA. Cost zero, i baixa el llindar útil de 2,0 a ~1,2 °C.

### Bloc B — Mesurar (setmanes 1–4)
15. Instal·lar sensors, endoll amb mesura i node ESPHome amb els dos DS18B20 (limita la cadència del mesurador de potència o filtra per delta).
16. `packages/rosada.yaml`: Td, ΔTd, marge de superfície, `history_stats` + `utility_meter`, i `sensor.decisio_del_soterrani` **registrant sense actuar**.
17. **Els ventiladors segueixen en el règim actual** (deure de la clàusula QUINTA i grup de control alhora).
18. Dashboards natius + app Companion.

### Bloc C — Actuar (setmana 5+, ~mitjans de novembre)
19. Passar les 4 setmanes gravades per la **rèplica offline** i fixar Δ_ON/Δ_OFF amb dades pròpies; comparar la rèplica amb el sensor registrat (test de deriva).
20. Relés, enclavament dur ventilador/deshumidificador, selector de mode amb caducitat, higròstat propi del deshumidificador (arquitectura (a)) i anti-cicle **també al dispositiu**.
21. **Congelació total de versions fins al 10/03/2027.**

### Bloc D — Dossier (gener–febrer 2027)
22. Gràfics a partir dels CSV arxivats, al portàtil de casa. Grafana només si els natius no basten.

---

## Decisions que NO es poden prendre encara

| Decisió bloquejada | Dada concreta que la desbloqueja | Opció per defecte mentrestant |
|---|---|---|
| Cadència de la còpia setmanal xifrada i si el frontend d'HA per 4G és car | **Límit mensual del pla de dades de la SIM** (encara sense contractar). És la dada que més val la pena obtenir abans de programar res | Setmanal; si el pla és folgat, res canvia |
| Si cal SAI de 50 € | **`energy_full` i cicles de la bateria + SMART del disc.** Tota la defensa de SQLite reposa que el portàtil és el seu propi SAI, i **és un actiu que es deprecia en silenci** | Comprar el SAI si la capacitat és < 60 %; monitoritzar `capacity` al cos del ping en tots els casos |
| Si ESPHome hi entra o basta un Tapo aïllat contra la paret | **Comparació d'un T310/T315 enganxat i tapat contra un termòmetre IR de mà** | ESPHome hi entra: és el sensor que decideix el cas i no s'hi val a estalviar |
| Quina TSA RFC 3161 gratuïta es fa servir | **Comprovar quina està viva i accepta POST sense compte** | Si cap no ho estigués: commit diari + correu mensual del `SHA256SUMS` a l'advocat |
| Marges exactes dels checks i mida del cos del ping | **Límits vigents del pla gratuït de healthchecks.io** | 2 checks, marges 3 h i 26 h, cos JSON curt |
| Si el `restic`/còpia nativa d'HA Container estalvia codi | **Si HA Container té còpia nativa utilitzable després de la reforma de 2025** | No en depenem: `VACUUM INTO` + `tar` cobreix el cas sencer |
| Si cal l'endoll de rearmada i el switch de 12 € | **Si el router SIM té *watchdog* propi i si manté el commutador LAN quan es penja** | No muntar-lo. Un router penjat costa un viatge, no costa prova |
| Mig apartat de la lògica del deshumidificador | **Si arrenca sol després d'un tall de corrent** | Arquitectura (a): higròstat propi, HA només enclavament i horaris |
| Quines entitats i quina resolució entren a l'arxiu | Decisió teva, no dada externa — però ha d'anar a **configuració, mai encastada al codi** | Totes les de clima, potència i estat; resolució crua |
| Si algú haurà d'obrir un panell des de fora | **Si un pèrit o advocat ho demana.** Mentre la resposta sigui «encara no», no s'hi munta infraestructura | Correu amb CSV + PDF |