# Publicació de dades — com pugen, on, i com les llegeix el web

> ⚠️ **PARCIALMENT SUPERAT** per [decisio-stack.md](decisio-stack.md), la decisió del 20/09/2026.
>
> **Canvis:** **no hi haurà panell web propi** ni allotjament a R2/Cloudflare Access (incompleix «gratuït» i fica un tercer que desxifra TLS sobre dades amb valor legal). Les dades van a un repositori privat `Local-data` amb un commit nocturn, i es consulten amb els dashboards natius d'HA per Tailscale. El que segueix vigent: el raonament sobre el patró de fitxers de git, ISO 8601 amb zona horària, i els forats explícits.
> Aquest document es conserva pel raonament, no com a guia vigent.
>
> 🟢 **21/09/2026 — canvi d'objectiu:** queden superats, a més, el repositori `Local-data`, i «no hi haurà panell web» es reobre. Allà on aquest
> document digui el contrari, mana [decisio-stack.md](decisio-stack.md).

> **Estat: proposta.** Respon a dues preguntes lligades: si cal `git push`, i com de fàcil
> serà que el panell web llegeixi les dades.

## La resposta curta

**No cal que sigui `git push`, i hi ha tres vies netes.** Però abans convé desfer un
malentès: **git no és el problema; la freqüència i la forma dels fitxers sí.**

I hi ha una restricció que condiciona tota la tria i que apareix a l'apartat
[«El web ha de poder llegir-les»](#el-web-ha-de-poder-llegir-les): **si les dades són
privades, un panell estàtic no hi pot arribar sense credencials.**

## El matís que decideix tot: com engreixa un repositori de git

Git **no guarda diferències, guarda el fitxer sencer** a cada commit en què canvia. D'aquí
surt la regla:

| Patró | Què passa | Veredicte |
|---|---|---|
| **Un fitxer per dia, immutable, un commit diari** | Cada commit afegeix només el fitxer nou | ✅ **Perfectament sa** |
| **Un fitxer que va creixent, commitejat cada 5 min** | Cada commit torna a guardar **tot** el fitxer. Creixement quadràtic | ❌ **Mata el repositori** |

Amb números reals d'aquest projecte: 12 sensors a 5 minuts ≈ **150 KB/dia** de CSV. Un
fitxer diari durant dos anys són ~110 MB de text pla, que git empaqueta a uns **20–30 MB**.
Això **no és cap problema** per a un repositori de GitHub.

El mateix volum amb el patró dolent passaria de **desenes de gigabytes**. La diferència no és
la quantitat de dades: és el patró.

## Les tres vies

### 1. `git push` a un repositori de dades separat

Un fitxer per dia, un commit diari.

- ✅ Gratis, senzill, i **datació per un tercer** amb historial immutable.
- ✅ **Si el panell viu al mateix repositori, llegir les dades és trivial** — vegeu més avall.
- ⚠️ Cal disciplina amb el patró de fitxers.

### 2. **GitHub Releases** — dades fora de l'historial de git

Els fitxers adjunts d'una *release* **no viuen a l'historial de git**: s'emmagatzemen a part.

```bash
gh release upload dades-2026-11 soterrani-2026-11.csv.gz --clobber
```

- ✅ **El repositori no creix gens.** Fins a 2 GB per fitxer. Data de servidor a cada release.
- ❌ **Dolent per al panell web:** no hi ha llistat de directori, i l'accés per `fetch` des
  del navegador depèn de redireccions i capçaleres CORS que no controles. **Per a l'arxiu,
  no per a la consulta.**

### 3. Emmagatzematge d'objectes — **cap git**

**Cloudflare R2** o **Backblaze B2**, amb `rclone` des del portàtil.

- ✅ Capa gratuïta folgada (R2: ~10 GB) i, a R2, **sense costos de sortida**.
- ✅ **Immutabilitat de debò:** *object lock* / versionat. Un objecte amb retenció bloquejada
  és, per a un tercer, **més sòlid que un commit de git** — ni tu el pots modificar.
- ✅ **Per al web és la millor opció**: CORS configurable, domini propi, i control d'accés.
- ⚠️ Cal un compte i credencials al portàtil.

### Què **no** recomano

- **InfluxDB Cloud / Grafana Cloud gratuïts:** la retenció de la capa gratuïta sol ser de
  l'ordre de **30 dies**. Inservible com a arxiu de dos anys.
- **Una base de dades allotjada** (Supabase, Neon) com a destí principal: una dependència i
  un esquema més per no guanyar res que un fitxer no doni. El magatzem de treball ja és el
  Postgres **local**.

---

## El web ha de poder llegir-les

Aquí és on la tria d'emmagatzematge deixa de ser indiferent.

### ⚠️ El problema: dades privades + panell estàtic

Un panell a **GitHub Pages** és HTML i JavaScript que s'executa **al navegador del visitant**.
Per llegir les dades ha de fer `fetch` d'una URL. I això xoca amb la privacitat:

| Situació | Funciona? |
|---|---|
| Repositori **públic**, dades al mateix repo que el panell | ✅ Trivial: URL relativa, zero CORS |
| Repositori **privat**, Pages amb control d'accés | ⚠️ **Funcionalitat de pagament** (GitHub Pro/Team) |
| Repositori **privat**, llegir per `raw.githubusercontent.com` | ❌ Cal un token. **Un token dins d'una pàgina web és un token públic** |
| Dades a **R2/B2 amb domini propi** + Cloudflare Access | ✅ Funciona i és gratuït, amb una mica de muntatge |
| Panell servit **des del portàtil del local**, per Tailscale | ✅ Privat de debò — però llavors cal VPN, i perds el «consultable sense instal·lar res» |

> **Decisió que cal prendre, i no és tècnica:** les dades de sensors del local revelen
> **patrons d'ocupació**. Publicar-les en obert no és neutre.
>
> **Recomanació: R2 amb domini propi darrere Cloudflare Access.** Gratuït, les dades no són
> públiques, i hi arribes des del mòbil amb un codi per correu, sense VPN. La via barata i
> dolenta —repositori públic amb una URL difícil d'endevinar— és seguretat per obscuritat i
> no la recomano per a dades d'aquest tipus.

### Format: dos formats per a dues feines

No facis que un sol fitxer serveixi per a tot.

| Ús | Format | Per què |
|---|---|---|
| **Panell web** | **JSON** | `fetch` + `JSON.parse` i llest, sense llibreria de parsing |
| **Arxiu probatori** | **CSV comprimit** | Més petit, i és el format que un pèrit obrirà |

> ⚠️ **No publiquis `.json.gz` per al web.** El navegador hauria de descomprimir-lo a mà en
> JavaScript. Publica JSON pla i deixa que el servidor apliqui la compressió — Pages i R2 ho
> fan sols per a text.

### Estructura de fitxers pensada per al navegador

El panell no ha de descarregar dos anys de dades per ensenyar un gràfic de les últimes 48 h.
Patró de tres capes:

```
latest.json              Valors actuals + últimes 48 h, ja reduït.    ~50 KB
                         Actualitzat cada hora. NO s'ha de cachejar.

index.json               Manifest: quins dies hi ha disponibles.      ~5 KB
                         Perquè el panell sàpiga què pot demanar.

daily/2026-11-14.json    Un per dia, immutable, resolució horària.    ~15 KB
                         Es pot cachejar per sempre.
```

Amb això:

- **Vista per defecte = una sola petició** de 50 KB. Obre ràpid al mòbil, i amb dades mòbils.
- **Ampliar el rang** = demanar només els dies que falten, i queden cachejats.
- **Els fitxers diaris no canvien mai**, així que el navegador no els torna a baixar.

### Pre-agrega al portàtil, no al navegador

No enviïs 3,5 milions de files a un telèfon. **El portàtil calcula min/mitjana/màx per hora i
publica això**; les dades crues es queden per a l'arxiu. Un any de dades horàries de 12
sensors són ~100.000 punts: manejable. Un any de dades a 5 minuts en són 1,2 milions: no.

### Què ha de mostrar el panell

Els gràfics que importen per al [cas de les humitats](../local/humitats.md):

1. **Punt de rosada interior vs exterior** — la decisió de ventilar, feta visible.
2. **Temperatura superficial de la paret vs punt de rosada interior** — el marge de
   condensació. **És el gràfic que decideix el cas.**
3. **Hores de ventilació per dia** — la prova que la ventilació ha estat operativa.
4. **Consum i litres/dia del deshumidificador** — el diagnòstic i el cost.
5. **Humitat relativa per punt**, amb la pluja superposada.

### Detalls que fan mal si no s'hi pensa abans

- **Cache de `latest.json`.** `raw.githubusercontent.com` cacheja uns minuts i Pages també.
  Afegeix un paràmetre de cache-busting (`?t=<marca de temps>`) o publica-hi la capçalera
  adequada des de R2.
- **Marques de temps en ISO 8601 amb zona horària** (`2026-11-14T03:12:00+01:00`). Mai
  «hores locals» sense zona: l'horari d'estiu et partirà els gràfics dos cops l'any, i per a
  ús probatori una sèrie amb ambigüitat horària és atacable.
- **Un `meta` a cada fitxer:** versió de l'esquema, quan es va generar, quins sensors conté.
  D'aquí a un any el format haurà canviat i voldràs poder llegir els fitxers vells.
- **Forats explícits.** Si falten dades, que el JSON ho digui (`null`, no absència), perquè
  el gràfic dibuixi un tall en comptes d'una línia recta que s'inventa el que no hi va haver.

---

## Recomanació: dues capes, dos destins

```
  PANELL WEB                →  R2 amb domini propi  (o repositori de Pages)
  latest.json + daily/*.json   JSON reduït, pensat per al navegador
  ~50 KB + 15 KB/dia

  ARXIU PROBATORI           →  GitHub Release  o  R2 amb object lock
  CSV comprimit + SHA-256      no toca l'historial; 24 objectes en tot el projecte
  ~1 MB/mes
```

Amb això obtens alhora un panell que obre de pressa des del mòbil, còpia fora del local,
datació per un tercer, i cap repositori que creixi.

## El consum de dades importa

Amb Internet per SIM ([subministraments.md](../local/subministraments.md)):

| Què | Quan | Volum |
|---|---|---|
| `latest.json` | Cada hora | ~50 KB → ~35 MB/mes |
| Fitxer diari | Un cop al dia | ~15 KB |
| Arxiu mensual | Un cop al mes | ~1 MB |
| Còpia de la base de dades | **Mai sencera per SIM** | Incremental, o disc extern al local |

> ⚠️ **Una base de dades d'1 GB pujada cada nit no és viable per SIM.** La còpia completa va
> a disc extern al local; el que viatja per la xarxa és el JSON i el CSV.

## Seguretat

- El destí de les dades ha de ser **privat**: publicar les dades dels sensors és publicar els
  patrons d'ocupació del local.
- Les credencials viuen al portàtil del local. **Fine-grained token** limitat al repositori de
  dades, o claus de R2/B2 limitades a un sol *bucket*. Si algú s'endú el portàtil, que la clau
  no serveixi per a res més.

## Per decidir

- [ ] ⚠️ **Les dades del panell seran privades o públiques?** Condiciona tota la resta.
      Recomanació: privades, a R2 darrere Cloudflare Access.
- [ ] Via per a l'arxiu: **GitHub Releases** o **R2/B2 amb object lock**.
- [ ] Cadència de `latest.json`: cada hora, o cada 15 minuts.
- [ ] Quins sensors i quina resolució entren al panell i quins només a l'arxiu.
- [ ] Verificar límits vigents de les capes gratuïtes i si Pages amb repositori privat
      requereix pla de pagament.
