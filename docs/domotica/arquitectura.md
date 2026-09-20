# Arquitectura — decisions obertes

> **Estat: en definició.** Aquest document recull les preguntes que cal respondre abans
> d'escriure codi. Ara mateix és un tema de **definició d'eines**, no de programació.
> Les propostes s'hi aniran incorporant a mesura que es tanquin.

## Les tres peces

```
        SENSORS  ──────────┐
   (T, HR interior,        │
    exterior, consum)      ▼
                    ┌──────────────┐        ┌───────────────┐
                    │ HOME         │───────▶│ MONITORITZACIÓ │
                    │ ASSISTANT    │        │ i visualització │
                    │ (al local)   │        └───────────────┘
                    └──────┬───────┘                │
                           │                        │
        ACTUADORS ◀────────┘                        │
   (ventiladors, deshumi-                           ▼
    dificador, splits)                      ACCÉS REMOT
                                          (PC i mòbil, fora)
```

## 1. Control automàtic

**Pregunta:** on viu la lògica del punt de rosada?

→ **Hi ha proposta: [control-punt-rosada.md](control-punt-rosada.md).** Recomanació:
**automatitzacions natives de Home Assistant**, traient les matemàtiques cap a sensors de
plantilla. pyscript com a següent graó si la lògica creix.

| Decisió | Estat |
|---|---|
| Llenguatge i entorn de la lògica de control | **Proposat: HA natiu** → [control-punt-rosada.md](control-punt-rosada.md) |
| Patró de llindars ajustables | **Proposat: helpers `input_number`** |
| Patró de mode manual / forçat | **Proposat: `input_select` + `timer` que caduca** |
| Fórmula del punt de rosada | **Proposat: Magnus (Alduchov & Eskridge)** |
| Histèresi i proteccions del relé | **Proposat: Δ_ON 2,0 °C / Δ_OFF 0,8 °C** |

## 2. Monitorització i visualització

**Pregunta:** on es guarden les dades i com es miren?

→ **Hi ha proposta: [monitoritzacio.md](monitoritzacio.md).** Recomanació: **PostgreSQL des
del dia 1** amb `purge_keep_days: 730`, dashboards natius per al dia a dia i **Grafana més
endavant** per al dossier. **InfluxDB descartat.** I dues coses que s'han de fer *abans* del
primer sensor, perquè després ja no tenen arreglada.

| Decisió | Estat |
|---|---|
| Base de dades de l'històric | **Proposat: PostgreSQL** → [monitoritzacio.md](monitoritzacio.md) |
| Retenció i resolució | **Proposat: 730 dies, cadència de 5 min** |
| Eina de visualització (dashboards natius d'HA vs Grafana) | **Proposat: natius ara, Grafana per al dossier** |
| Còpies de seguretat i exportació | **Proposat: còpia nocturna + ritual CSV/SHA-256 mensual** |
| Quines dades es registren exactament | **A definir més endavant** (decisió explícita de l'usuari) |

## 3. Accés remot

**Pregunta:** com s'arriba a Home Assistant des de fora, per PC i per mòbil?

→ **Hi ha proposta: [acces-remot.md](acces-remot.md).** Recomanació: **Tailscale** com a
columna vertebral (gratuït, immune al CGNAT, dona accés a tota la màquina) **+ Nabu Casa**
com a segon camí independent. Port forwarding descartat.

| Decisió | Estat |
|---|---|
| Mètode d'accés remot | **Proposat** → [acces-remot.md](acces-remot.md) |
| Si l'operadora del local dona IP pública o hi ha CGNAT | **Resolt de fet: Internet per SIM → CGNAT quasi segur** |
| Interfície al mòbil (app d'HA vs navegador) | **Obert** |
| Publicació de dades i còpia externa | **Proposat** → [publicacio-dades.md](publicacio-dades.md) |
| Flux de desenvolupament i desplegament | **Decidit: casa → GitHub → local, amb SSH per Tailscale** → [desplegament.md](desplegament.md) |

## Maquinari encara per decidir

→ **Hi ha proposta: [control-punt-rosada.md](control-punt-rosada.md), apartat D.**
Pressupost del nucli funcional: **~220–240 €**.

| Decisió | Estat |
|---|---|
| Protocol dels sensors | **Proposat: Zigbee amb coordinador en xarxa al soterrani** |
| Sensors de T i HR: quants i on | **Proposat: 3 interiors + 1 exterior, mateix model i lot** |
| Endoll amb mesura per al deshumidificador | **Proposat: Shelly Plug S Gen3** |
| Commutació dels ventiladors | **Proposat: relé darrere l'interruptor, mode *detached*** |
| Cobertura de ràdio al soterrani | **Per verificar amb una prova de 48 h** |
