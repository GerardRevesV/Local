# Arquitectura — índex d'estat

> ⚠️ **Aquest document ja no decideix res.** Totes les decisions estan preses i viuen a
> **[decisio-stack.md](decisio-stack.md)**. Això només és l'índex de per on queda cada cosa.

| Bloc | Estat | On mirar |
|---|---|---|
| Sistema base i instal·lació de HA | ✅ Decidit: Mint + Docker, **HA Container** amb versió fixada | [decisio-stack.md](decisio-stack.md) |
| Stack de contenidors | ⚠️ **Dos** des del 21/09/2026: `homeassistant` + `matter-server`. Es volia un de sol; el segon el va imposar el xifratge del hub | [decisio-stack.md](decisio-stack.md) |
| Base de dades de l'històric | ✅ Decidit: **SQLite**, `purge_keep_days: 730` | [decisio-stack.md](decisio-stack.md) |
| Lògica de control | ✅ Decidit: **HA natiu**, un únic sensor de decisió | [decisio-stack.md](decisio-stack.md) · [control-punt-rosada.md](control-punt-rosada.md) |
| Exportació i arxiu | ✅ Decidit: **`nit.py`** en Python stdlib, commit nocturn amb segell | [decisio-stack.md](decisio-stack.md) |
| Allotjament de dades | ✅ Decidit: **`Local-data` privat a GitHub** | [decisio-stack.md](decisio-stack.md) |
| Panell web | ✅ Decidit: **no n'hi ha.** Dashboards natius per Tailscale | [decisio-stack.md](decisio-stack.md) |
| Accés remot | ✅ Decidit: **Tailscale**, única via | [acces-remot.md](acces-remot.md) |
| Desplegament | ✅ Decidit: **`desplega.sh`** a mà per SSH | [desplegament.md](desplegament.md) |
| Còpies i supervisió | ✅ Decidit: disc USB + tarball xifrat setmanal + 2 checks | [decisio-stack.md](decisio-stack.md) |
| Ràdio | ✅ **868 MHz sub-GHz**, hub **Tapo H110** + sensors T310/T315. ⚠️ La via cap al hub és **Matter**, no `tplink`: el hub xifra amb TPAP i `python-kasa` el rebutja. *ZHA i l'SLZB-06 van quedar superats pel maquinari ja comprat.* | [inventari.md](inventari.md) · [decisio-stack.md](decisio-stack.md) |
| Maquinari | ✅ **Comprat i actiu**, no proposat: hub, endoll amb mesura, 5 sensors T/HR, sensor d'inundació i 2 relés. ⏳ Els relés, sense instal·lar fins a la Fase C | [inventari.md](inventari.md) |
| Noms d'entitat | ✅ Conveni **escrit**. ⏳ Falta **aplicar-lo** en emparellar el hub per Matter: renombrar després parteix la sèrie. ⚠️ El conveni diu «font: integració `tplink`», que ja no val | [noms-entitats.md](noms-entitats.md) |
| Refer el servidor de zero | ✅ Escrit: ordres, versions i paranys | [runbook-servidor.md](runbook-servidor.md) |
| Fases i portes de test | ✅ [fases.md](fases.md) | |
| Filtratge d'espuris, paràmetres per la web i correlació | 🔸 **Requisits oberts**, definits el 21/09/2026: dissenyats, no decidits | [requisits.md](requisits.md) |

## El que encara no es pot decidir

Vegeu l'apartat final de [decisio-stack.md](decisio-stack.md): cada decisió bloquejada hi té
la dada concreta que la desbloqueja i una opció per defecte mentrestant.

I [requisits.md](requisits.md) per als requisits que encara no han arribat a ser decisions:
cadascun hi porta la dada que el desbloqueja i la fase on toca.
