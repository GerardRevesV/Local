# Flux de desenvolupament i desplegament

> ⚠️ **PARCIALMENT SUPERAT** per [decisio-stack.md](decisio-stack.md), la decisió del 20/09/2026.
>
> **Canvis:** l'stack és **un sol contenidor** (`homeassistant`): res de Postgres, Mosquitto ni Zigbee2MQTT. El desplegament és `desplega.sh` amb portes dures, llançat a mà per SSH. El que segueix vigent i reforçat: pull i no push, versions fixades, validació abans de reiniciar, i el parany de `.storage`.
> Aquest document es conserva pel raonament, no com a guia vigent.

> **Estat: decidit a grans trets, detalls oberts.**

## El flux

```
   Portàtil de casa            GitHub              Portàtil del local
   ┌──────────────┐         ┌─────────┐          ┌──────────────────┐
   │  editar codi │─ push ─▶│  repo   │◀─ pull ──│  Home Assistant  │
   │  i config    │         │         │          │  + Postgres      │
   └──────────────┘         └─────────┘          └──────────────────┘
          │                                               ▲
          └──────────── SSH per Tailscale ────────────────┘
                    (desplegar, depurar, arreglar)
```

**Tailscale confirmat.** Amb aquest flux l'SSH no és un luxe: és la via per llançar el
desplegament, mirar logs, reiniciar contenidors i arreglar el que es trenqui. Cap de les
altres opcions d'accés remot ([acces-remot.md](acces-remot.md)) dona shell.

## Els dos repositoris

| Repositori | Què hi va | Visibilitat |
|---|---|---|
| **`Local`** (aquest) | Documentació, configuració de Home Assistant, `docker-compose.yml`, scripts | Públic ara mateix |
| **`Local-data`** (per crear) | Exportacions de sensors, panell de GitHub Pages | **Privat** |

Separats perquè el de dades rebrà commits automàtics cada dia i git no oblida: barrejar-los
faria créixer sense fre el repositori de documentació.

## Pull, no push

Hi ha dues maneres de fer arribar el codi al local, i la diferència importa:

| | **Pull** (el local fa `git pull`) | **Push** (des de casa, `rsync` per SSH) |
|---|---|---|
| Font de veritat | GitHub — sempre saps què hi ha desplegat | El teu portàtil de casa |
| Si Tailscale falla | El local pot actualitzar-se igualment | Bloquejat |
| Traçabilitat | Cada desplegament és un commit | Cap rastre |
| Risc | Cal evitar que desplegui coses a mitges | Fàcil desincronitzar-se |

**Recomanació: pull.** El local clona el repositori i el desplegament és, essencialment,
`git pull && docker compose up -d`. Llançat **per SSH quan tu vulguis**.

### ⚠️ Però no automàtic per temporitzador

La temptació és posar un `cron` que faci `git pull` cada X minuts. **No ho facis**, i el
motiu és específic d'aquest projecte:

> **Un commit dolent que reiniciï Home Assistant deixa un forat a l'històric.** I l'històric
> és la prova per al cas de les [humitats](../local/humitats.md). Un desplegament
> desatès que falli un divendres a la nit i no es noti fins dilluns són tres dies de dades
> perdudes que no tornen.

Els desplegaments han de ser **deliberats, observats i registrats**. Si mai vols
automatitzar-ho, fes-ho amb una porta: que el local només desplegui el que hi hagi a una
branca `deploy` o a una etiqueta, no a `main`.

## Què viatja per git i què no

| | Va a git? | Nota |
|---|---|---|
| `docker-compose.yml` | ✅ | **Amb versions fixades**, no `:latest` — vegeu sota |
| `configuration.yaml` i els YAML inclosos | ✅ | El nucli de la configuració |
| Automatitzacions i sensors de plantilla | ✅ | **Si els defineixes en YAML** — vegeu el parany |
| `secrets.yaml` | ❌ | Ja bloquejat al `.gitignore`. Viu només al local |
| `.storage/` | ❌ | Estat intern d'HA, no versionable |
| La base de dades | ❌ | Va per la via de còpies, no per git |

### ⚠️ El parany de `.storage`

Tot el que crees des de la **interfície** de Home Assistant —helpers, automatitzacions fetes
amb l'editor visual, integracions— **no viu en fitxers YAML: viu a `.storage/`**, en JSON
intern que no s'ha de versionar ni editar a mà.

Conseqüència pràctica: si vols que els llindars i els automatismes del
[control per punt de rosada](control-punt-rosada.md) estiguin a git —i els vols, perquè és
la lògica del projecte— **els has de definir en YAML**, no clicant-los a la interfície.

El terme mitjà raonable:

- **En YAML, a git:** els `input_number` de llindars, els sensors de plantilla del punt de
  rosada, les automatitzacions de control. És la lògica que vols revisar, comparar i poder
  revertir.
- **Per interfície, fora de git:** les integracions i els dispositius (emparellar un Zigbee
  per YAML no té cap sentit), i els panells.

## Fixa les versions

Al `docker-compose.yml`, **res de `:latest`**. Fixa la versió exacta de Home Assistant, de
Postgres i de la resta:

```yaml
image: ghcr.io/home-assistant/home-assistant:2026.9.1   # no :latest
```

Dos motius. El primer és el de sempre: una actualització automàtica trencada et deixa el
sistema caigut sense que hagis tocat res. El segon és específic: **actualitzar és un
desplegament, i un desplegament és un forat a l'històric.** Que l'actualització sigui una
decisió teva, amb data, i no una sorpresa d'un dimarts.

Actualitzar passa a ser un commit que canvia l'etiqueta de la imatge — cosa que a més et
dona el registre de quan vas actualitzar i a quina versió, i un `git revert` per tornar
enrere.

## Valida abans de reiniciar

Un YAML mal format fa que Home Assistant no arrenqui. Amb HA Container no hi ha el botó de
*Check configuration* del Supervisor, però es pot fer igual:

```bash
docker compose exec homeassistant python -m homeassistant --script check_config -c /config
```

**Posa-ho al script de desplegament abans del reinici**, i que avorti si falla. Costa cinc
minuts escriure-ho i evita el mode de fallada més comú: desplegar, marxar de casa, i
assabentar-te tres dies després que no havia arrencat.

## Esquema del script de desplegament

Res d'això està escrit encara; és l'esquelet acordat.

```
1. git pull                        (a la branca o etiqueta de desplegament)
2. validar la configuració         → si falla, aturar-se i no tocar res
3. docker compose up -d            (només els serveis que hagin canviat)
4. esperar que HA respongui        → si no respon en N segons, avisar
5. registrar el desplegament       (data, commit, resultat)
```

El pas 5 val la pena: quan d'aquí a un any hi hagi un forat a les dades i calgui explicar-lo,
voldràs poder dir *«el 14 de novembre a les 22:10 vaig desplegar el commit `abc123` i HA va
estar 90 segons aturat»*. Això és el contrari d'un buit sospitós.

## Per decidir

- [ ] Nom i creació del repositori privat de dades.
- [ ] Branca o etiqueta de desplegament (`main` directament, o una `deploy` com a porta).
- [ ] On viu el `docker-compose.yml` i quins serveis inclou (HA, Postgres, Mosquitto,
      Zigbee2MQTT).
- [ ] Usuari i claus SSH al portàtil del local. *(Tailscale SSH pot gestionar l'autenticació
      per identitat, sense distribuir claus — cal verificar-ho.)*
- [ ] Si val la pena un `git hook` o un `Makefile` per no recordar la seqüència de memòria.
