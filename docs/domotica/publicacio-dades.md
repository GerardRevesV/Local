# Publicació de dades — com pugen, i on

> **Estat: proposta.** Respon a la pregunta de si cal `git push` o hi ha alternatives que no
> toquin el repositori.

## La resposta curta

**No cal que sigui `git push` al repositori, i hi ha tres vies netes.** Però abans convé
desfer un malentès: **git no és el problema; la freqüència i la forma dels fitxers sí.**

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

El mateix volum amb el patró dolent —un CSV mensual que creix i es commiteja cada 5 minuts—
passaria de **desenes de gigabytes**. La diferència no és la quantitat de dades: és el patró.

> **Conclusió:** si el que et preocupava era embrutar el repositori, **amb un commit diari
> d'un fitxer immutable no l'embrutes.** Git és una opció vàlida.

## Les tres vies, i quan fer servir cadascuna

### 1. `git push` a un repositori de dades separat

Un fitxer per dia, un commit diari.

- ✅ Gratis, senzill, i **datació per un tercer** (el servidor de GitHub) amb historial
  immutable — el que dona valor probatori.
- ✅ Alimenta directament **GitHub Pages**.
- ⚠️ Cal disciplina amb el patró de fitxers.

### 2. **GitHub Releases** — dades fora de l'historial de git

Aquesta és la que respon literalment la teva pregunta: **els fitxers adjunts d'una *release*
no viuen a l'historial de git.** S'emmagatzemen a part i es poden substituir.

```bash
gh release upload dades-2026-11 soterrani-2026-11.csv.gz --clobber
```

- ✅ **El repositori no creix gens**, facis les pujades que facis.
- ✅ Cada *release* té data de servidor → segueix valent com a datació.
- ✅ Fins a 2 GB per fitxer.
- ⚠️ Menys convencional, i GitHub Pages no els llegeix directament (però es poden descarregar
  per URL).

**Encaix natural: l'arxiu mensual complet.** Un fitxer al mes, 24 objectes en tot el projecte.

### 3. Emmagatzematge d'objectes — **cap git**

**Cloudflare R2** o **Backblaze B2**, amb `rclone` des del portàtil. Un directori de fitxers
al núvol, sense repositori pel mig.

- ✅ Capa gratuïta folgada (R2: ~10 GB) i, a R2, **sense costos de sortida**.
- ✅ **Immutabilitat de debò:** tots dos suporten *object lock* / versionat. Un objecte amb
  retenció bloquejada és, per a un tercer, **més sòlid que un commit de git** — ni tu el pots
  modificar.
- ✅ Ideal per a volcats grans i per a còpies de la base de dades.
- ⚠️ Cal un compte i unes credencials al portàtil. Sense interfície web decent per mirar-ho.

### Què **no** recomano

- **InfluxDB Cloud / Grafana Cloud gratuïts:** la retenció de la capa gratuïta sol ser de
  l'ordre de **30 dies**. Per a un registre de dos anys amb valor probatori, inservible com
  a arxiu. Com a panell bonic, potser; com a magatzem, no.
- **Una base de dades allotjada** (Supabase, Neon) com a destí principal: afegeix una
  dependència i un esquema per no guanyar res que un fitxer no doni. El magatzem de treball
  ja és el Postgres **local**.

## Recomanació: repartir-ho en dues capes

Cada cosa té una feina diferent i convé no forçar-ne una a fer les dues:

```
  RESUM ACTUAL              →  repositori de dades (o branca gh-pages)
  últims 30 dies, reduït       petit, es reescriu, alimenta el panell web
  ~100–300 KB

  ARXIU MENSUAL COMPLET     →  GitHub Release  o  R2/B2
  CSV comprimit + SHA-256      no toca l'historial; 24 objectes en tot el projecte
  ~1 MB/mes
```

Amb això obtens alhora:

- **Un panell consultable des del mòbil** sense VPN (GitHub Pages llegint el JSON de resum).
- **Còpia fora del local**, que era un requisit imprescindible.
- **Datació per un tercer** de l'arxiu complet.
- **Un repositori que no creix.**

## El consum de dades importa

Amb Internet per SIM ([subministraments.md](../local/subministraments.md)), el volum de
pujada compta:

| Què | Quan | Volum |
|---|---|---|
| Resum reduït | Cada hora | Uns quants KB |
| Arxiu diari | Un cop al dia | ~30–50 KB comprimit |
| Arxiu mensual | Un cop al mes | ~1 MB |
| Còpia de la base de dades | **Mai sencera per SIM** | Incremental, o disc extern al local |

> ⚠️ **Una base de dades d'1 GB pujada cada nit no és viable per SIM.** La còpia completa va
> a disc extern al local; el que viatja per la xarxa és el CSV, que és tres ordres de
> magnitud més petit.

## Seguretat

- El repositori o el *bucket* de dades ha de ser **privat**: publicar les dades dels sensors
  és publicar els patrons d'ocupació del local.
- Les credencials viuen al portàtil del local. **Fine-grained token** amb permís només sobre
  el repositori de dades, o claus de R2/B2 limitades a un sol *bucket*. Si algú s'endú el
  portàtil, s'endú la clau — que no serveixi per a res més.

## Per decidir

- [ ] Via per a l'arxiu: **GitHub Releases** o **R2/B2**. *(Releases si vols zero comptes
      nous; R2/B2 si vols immutabilitat forta amb *object lock*.)*
- [ ] Cadència del resum: cada hora, o cada 15 minuts.
- [ ] Quins sensors i quina resolució entren al resum públic i quins només a l'arxiu.
- [ ] Verificar límits vigents de les capes gratuïtes i l'ús acceptable de GitHub per a
      aquest volum.
