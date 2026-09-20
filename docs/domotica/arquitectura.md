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

Opcions sobre la taula: automatitzacions natives de Home Assistant amb plantilles Jinja,
**Node-RED**, **AppDaemon**, **pyscript**, o un servei propi en Python que parli amb HA per
API.

Criteris que importen:
- Poder canviar llindars **sense tocar codi** (helpers `input_number` / `input_boolean`).
- Poder **forçar** un aparell a mà sense que l'automatisme hi lluiti.
- Depurabilitat: veure per què una decisió s'ha pres.
- Robustesa: què passa si el component que porta la lògica cau.

| Decisió | Estat |
|---|---|
| Llenguatge i entorn de la lògica de control | **Obert** |
| Patró de llindars ajustables | **Obert** |
| Patró de mode manual / forçat | **Obert** |
| Fórmula i implementació del punt de rosada | **Obert** |
| Histèresi i proteccions del relé | **Obert** |

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
| Si l'operadora del local dona IP pública o hi ha CGNAT | **Per verificar** |
| Interfície al mòbil (app d'HA vs navegador) | **Obert** |

## Maquinari encara per decidir

| Decisió | Estat |
|---|---|
| Protocol dels sensors (Zigbee, Z-Wave, Wi-Fi, ESPHome/ESP32) | **Obert** |
| Sensors de T i HR: quants i on | **Obert** |
| Sensor exterior | **Obert** |
| Endoll o relé amb **mesura de consum** per al deshumidificador | **Obert** |
| Commutació dels dos ventiladors cap a l'exterior | **Obert** |
| Cobertura de ràdio al soterrani | **Per verificar** |
