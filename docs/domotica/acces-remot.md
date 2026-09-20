# Accés remot — proposta

> **Estat: proposta.** Actualitzat amb dos fets nous: Internet serà per **SIM** i s'ha
> plantejat fer servir **GitHub** com a intermediari.

## Fet nou que decideix mitja comparativa: Internet per SIM

L'accés a Internet del local serà per **router amb targeta SIM**. Les connexions mòbils van
gairebé sempre darrere **CGNAT** i amb IP dinàmica, i això elimina opcions per física de
xarxa, no per preferència:

- ❌ **Port forwarding + reverse proxy** — impossible. Descartat definitivament.
- ❌ **WireGuard pur amb el servidor al local** — impossible sense un VPS intermediari.
- ✅ **Tailscale** — és exactament el seu cas d'ús.
- ✅ **Nabu Casa / Cloudflare Tunnel** — la connexió la inicia el local cap enfora.

A més, **el consum de dades passa a comptar**. Vegeu [subministraments.md](../local/subministraments.md).

## La proposta de GitHub: el portàtil puja dades i tu les mires al web

**Sí, funciona — per a la meitat del problema.** I aquesta meitat la fa millor que
qualsevol de les altres opcions.

### Què resol bé

| | |
|---|---|
| **Monitorització** | ✅ El portàtil fa `git push` d'un CSV o un JSON cada X minuts. Tu ho mires des de qualsevol lloc, sense instal·lar res, des del mòbil o del PC |
| **Travessar el CGNAT** | ✅ Perfectament. És trànsit **sortint**. No cal obrir res |
| **Consum de dades** | ✅ **Excel·lent.** Uns quants KB per pujada. Molt millor que una VPN oberta |
| **Cost** | ✅ Zero |
| **Còpia fora del local** | ✅ **De regal.** Resol el requisit de còpia externa que la proposta de [monitorització](monitoritzacio.md) marca com a imprescindible |
| **Datació per un tercer** | ✅ **De regal, i té valor real.** Els commits els data el servidor de GitHub, no el teu portàtil. Per al cas de les humitats, això és molt millor que una marca de temps local |
| **Interfície** | ✅ Amb **GitHub Pages** pots servir un panell HTML estàtic que llegeixi els JSON del repositori. Gratuït i sense servidor |

Aquesta última part és important: **per al cas de les humitats, GitHub no és un apany, és
una millora.** Una sèrie de dades amb commits datats per un tercer i historial immutable és
substancialment més sòlida que una base de dades SQLite en un portàtil teu.

### Què NO resol

| | |
|---|---|
| **Control** | ⚠️ Només amb un apany (vegeu sota), amb latència i sense confirmació immediata |
| **Canviar llindars** | ⚠️ Igual: editar un fitxer al mòbil és molt pitjor que moure un lliscador |
| **Arreglar coses quan es trenquen** | ❌ **Aquest és el problema seriós.** Si Home Assistant no aixeca, o el contenidor de Postgres peta, o el `git push` falla, **no tens cap manera d'entrar-hi**. Has d'agafar el cotxe |
| **Veure l'estat ara mateix** | ❌ Veus l'última pujada, no el present |

### L'apany per al control, i per què no és suficient

Es pot fer un canal de control **per sondeig**: el portàtil fa `git pull` cada minut i llegeix
un `ordres.json` del repositori; tu l'edites des del web de GitHub i, al cap d'un minut,
l'ordre s'executa.

Funciona. Però:

- **Latència d'un cicle de sondeig**, i sense confirmació fins a la pujada següent.
- **Editar JSON al mòbil** és una experiència pèssima comparada amb un lliscador a l'app.
- **Cap realimentació**: no saps si l'ordre s'ha aplicat fins que arriba el proper informe.
- **Sondeig constant** = trànsit constant per la SIM i commits de soroll.

> ⚠️ **GitHub no és un bus de missatges.** Fer commits cada pocs segons és abusar-ne i acabarà
> malament. Un sondeig cada 1–5 minuts és raonable; més sovint, no.

## No són alternatives: són les dues meitats

```
   MONITORITZACIÓ  ────▶  GitHub  ────▶  excel·lent, i de regal
   (publicar dades)                      dona còpia externa i datació

   ADMINISTRACIÓ   ────▶  Tailscale ──▶  imprescindible quan
   (entrar i arreglar)                   alguna cosa es trenca
```

**La pregunta correcta no és «Tailscale o GitHub».** És: *quan el portàtil es pengi un
dijous de novembre i el `git push` deixi de funcionar, com ho arreglo sense conduir fins al
local?* GitHub no té resposta per a això. Tailscale sí, i a més et dona **SSH a tota la
màquina**, no només l'accés a Home Assistant.

Tailscale és **gratuït** i es munta en deu minuts. El cost d'afegir-lo és tan baix que no
cal triar.

## Recomanació actualitzada

1. **Tailscale** com a via d'administració. Gratuït, travessa CGNAT, dona SSH i accés a tot.
   ⚠️ **Desactiva l'expiració de clau** al node del local: per defecte caduca als ~180 dies i
   et desconnectaria el servidor a mig projecte.
2. **GitHub com a canal de publicació i còpia**, amb un panell a **GitHub Pages**. Puja
   resums cada hora i l'exportació completa cada dia. Doble benefici: consulta còmoda sense
   VPN **i** compleixes de cop el requisit de còpia externa i de datació per tercer.
3. **Nabu Casa: opcional.** Amb Tailscale + GitHub ja tens administració i consulta. La
   justificació que li queda és la comoditat al mòbil i poder passar una URL a un pèrit — i
   això segon ja ho fa GitHub Pages. **Comença sense.**
4. **Control des de fora: per Tailscale**, amb l'app de Home Assistant. No muntis el canal
   d'ordres per GitHub si tens Tailscale: afegeix complexitat per resoldre una cosa ja
   resolta.

> **Nota:** el detall de com pugen les dades —i que **no cal** que sigui `git push` al
> repositori— és a [publicacio-dades.md](publicacio-dades.md). El flux de desplegament és a
> [desplegament.md](desplegament.md).

## ⚠️ Condicions per a la via de GitHub

- **El repositori de dades ha de ser PRIVAT.** Aquest repositori de documentació és públic;
  publicar-hi dades de sensors seria publicar els patrons d'ocupació del local.
- **El token d'escriptura viu al portàtil del local.** Fes servir un *fine-grained token* amb
  permís només sobre aquest repositori, o millor un **repositori separat només de dades**.
  Si algú s'endú el portàtil, s'endú la clau.
- **Compte amb l'historial de git.** Un CSV nou cada 5 minuts infla el repositori per sempre
  —git no oblida— i acabarà sent lent. Patró correcte: **un fitxer per dia**, afegint-hi
  línies, i **un sol commit diari**. Si vols resolució fina, publica un resum freqüent
  (petit, sobreescrit) i l'històric complet un cop al dia.
- **Separa el repositori de dades del de documentació.** Aquest repositori és per a
  documentació i codi; no el barregis amb milers de commits automàtics.

## La resta d'opcions, per si es reobre el debat

| Opció | CGNAT | Cost | Exposa el login | Dona accés a la màquina |
|---|---|---|---|---|
| **Tailscale** | ✅ | 0 € | ❌ No | ✅ Sí |
| **GitHub + Pages** | ✅ | 0 € | ❌ No | ❌ No |
| **Nabu Casa** | ✅ | ~78 €/any | ⚠️ Sí | ❌ Només HA |
| **Cloudflare Tunnel** | ✅ | Domini ~12 €/any | ⚠️ Sí | ❌ Només HA |
| **WireGuard pur** | ❌ sense VPS | 0 € o ~50 €/any | ❌ No | ✅ Sí |
| **Port forwarding** | ❌ | 0 € | ⚠️ Sí | ❌ Només HA |

**Nabu Casa** — fricció mínima i pots passar una URL a un tercer, però exposa el login de HA
a Internet (2FA obligatori). Cal verificar el preu vigent i si les seves còpies al núvol
funcionen amb HA Container.

**Cloudflare Tunnel** — cal domini propi; **Cloudflare desxifra el TLS** i veu el trànsit en
clar (un tercer més a la cadena, amb dades de valor legal), i **l'app mòbil de HA encaixa
malament amb Cloudflare Access**.

## El que cap opció d'accés remot resol, i cal igualment

- **Vigilància de vida (*dead-man switch*)** tipus Healthchecks.io: que avisi **en hores** si
  el local es queda sense línia o HA cau. Amb la via de GitHub això surt quasi gratis:
  *si fa més de N hores que no arriba un commit, alguna cosa va malament.*
- **Rearmada elèctrica fora de banda:** endoll intel·ligent amb núvol propi alimentant el
  portàtil **i el router SIM** (un router 4G penjat es recupera amb un cicle d'alimentació),
  independent de Home Assistant.
- **Higiene del portàtil:** no suspendre en tancar la tapa, encesa automàtica després d'un
  tall (BIOS), SAI petit, i **no deixar actualitzacions automàtiques de HA** en una màquina
  amb missió probatòria.

## Per verificar

- [ ] Operadora de la SIM, pla de dades i límit mensual.
- [ ] Si el router SIM té Ethernet i *watchdog* de reconnexió.
- [ ] Límits actuals del pla gratuït de Tailscale.
- [ ] Límits de mida i de freqüència raonables de GitHub per a aquest ús.

## Advertiment sobre el valor probatori

Un històric autogenerat pot no aguantar una impugnació. **La via de GitHub hi ajuda
notablement** (datació per tercer, historial immutable), però convé consultar amb un
professional si cal, a més, un segell de temps RFC 3161 o un enregistrador independent,
**abans** de basar tota l'estratègia de les humitats en aquestes dades.
