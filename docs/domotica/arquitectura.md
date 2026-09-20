# Arquitectura — índex d'estat

> ⚠️ **Aquest document ja no decideix res.** Totes les decisions estan preses i viuen a
> **[decisio-stack.md](decisio-stack.md)**. Això només és l'índex de per on queda cada cosa.

| Bloc | Estat | On mirar |
|---|---|---|
| Sistema base i instal·lació de HA | ✅ Decidit: Mint + Docker, **HA Container** amb versió fixada | [decisio-stack.md](decisio-stack.md) |
| Stack de contenidors | ✅ Decidit: **un de sol** | [decisio-stack.md](decisio-stack.md) |
| Base de dades de l'històric | ✅ Decidit: **SQLite**, `purge_keep_days: 730` | [decisio-stack.md](decisio-stack.md) |
| Lògica de control | ✅ Decidit: **HA natiu**, un únic sensor de decisió | [decisio-stack.md](decisio-stack.md) · [control-punt-rosada.md](control-punt-rosada.md) |
| Exportació i arxiu | ✅ Decidit: **`nit.py`** en Python stdlib, commit nocturn amb segell | [decisio-stack.md](decisio-stack.md) |
| Allotjament de dades | ✅ Decidit: **`Local-data` privat a GitHub** | [decisio-stack.md](decisio-stack.md) |
| Panell web | ✅ Decidit: **no n'hi ha.** Dashboards natius per Tailscale | [decisio-stack.md](decisio-stack.md) |
| Accés remot | ✅ Decidit: **Tailscale**, única via | [acces-remot.md](acces-remot.md) |
| Desplegament | ✅ Decidit: **`desplega.sh`** a mà per SSH | [desplegament.md](desplegament.md) |
| Còpies i supervisió | ✅ Decidit: disc USB + tarball xifrat setmanal + 2 checks | [decisio-stack.md](decisio-stack.md) |
| Ràdio | ✅ Decidit: **ZHA + SLZB-06 per TCP** *(a confirmar abans d'emparellar)* | [decisio-stack.md](decisio-stack.md) |
| Maquinari | 🔸 Proposat, pendent de les verificacions físiques | [control-punt-rosada.md](control-punt-rosada.md) |
| Fases i portes de test | ✅ [fases.md](fases.md) | |

## El que encara no es pot decidir

Vegeu l'apartat final de [decisio-stack.md](decisio-stack.md): cada decisió bloquejada hi té
la dada concreta que la desbloqueja i una opció per defecte mentrestant.
