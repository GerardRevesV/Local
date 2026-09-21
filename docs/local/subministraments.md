# Subministraments

## Electricitat — Naturgy Tarifa Noche ✅ contractada

Contractada. És la modalitat amb **discriminació horària en tres trams** de Naturgy, sobre
els períodes regulats estàndard de la tarifa 2.0TD.

### Franges horàries

| Període | Horari | Preu energia |
|---|---|---|
| 🟢 **Vall (P3)** | **00:00 – 08:00** de dilluns a divendres<br>**24 h els caps de setmana i festius nacionals** *(vegeu quins, a sota)* | **0,0739 €/kWh** |
| 🟡 **Pla (P2)** | 08:00 – 10:00 · 14:00 – 18:00 · 22:00 – 00:00, de dilluns a divendres feiners | 0,1092 €/kWh |
| 🔴 **Punta (P1)** | 10:00 – 14:00 · 18:00 – 22:00, de dilluns a divendres feiners | 0,1822 €/kWh |

> *(21/09/2026)* Les dues últimes files deien «tots els dies», que contradeia la primera: el
> cap de setmana és vall sencer. Corregit segons el text de la circular (vegeu a sota), que
> diu «lunes a viernes laborables».

### Quins festius són vall — la regla, que serveix per a qualsevol any

La **Circular CNMC 3/2020, art. 7.3**, que és la que fixa els períodes de la 2.0TD
([BOE-A-2020-1066](https://www.boe.es/buscar/act.php?id=BOE-A-2020-1066), sense canvis en
aquest punt per la Circular 1/2025):

> «Se consideran como horas del periodo 3 (valle) todas las horas de los sábados, domingos,
> el 6 de enero y los días festivos de ámbito nacional, definidos como tales en el calendario
> oficial del año correspondiente, con exclusión tanto de los festivos sustituibles como de
> los que no tienen fecha fija.»

Creuat amb el **RD 2001/1983, art. 45.1** —que diu quins festius nacionals són no
substituïbles (apartats a, b i c) i quins pot canviar cada comunitat (apartat d)—, surten
**nou dates fixes, cada any les mateixes**:

**1/1 · 6/1 · 1/5 · 15/8 · 12/10 · 1/11 · 6/12 · 8/12 · 25/12**

Com que la regla és de data fixa, **no cal cap llista per any**: el codi la té escrita com a
regla i val fins que canviï la llei. Els paranys, que és on s'equivoquen els calculadors:

| No és vall | Per què |
|---|---|
| **Divendres Sant** | És festiu nacional no substituïble, però **no té data fixa**. Alguns calculadors (la biblioteca `aiopvpc`, per exemple) el posen en vall; la circular l'exclou |
| El **dilluns de trasllat** d'un festiu que cau en diumenge | Ni és data fixa ni és un festiu nacional: és un descans traslladat |
| **Dijous Sant, Sant Josep, Sant Jaume** | Substituïbles (apartat d) |
| **Sant Joan, la Diada, Sant Esteve, Dilluns de Pasqua, la Mercè** | Autonòmics o locals, no nacionals |

**Els que de debò mouen la factura** són els que cauen entre setmana (en cap de setmana ja
eren vall). Surten de [`tools/tarifa.py --festius`](../../tools/tarifa.py):

| Any | Festius en vall que cauen entre setmana | Divendres Sant (**no** és vall) |
|---|---|---|
| 2026 | 6: dj 1/1 · dt 6/1 · dv 1/5 · dl 12/10 · dt 8/12 · dv 25/12 | 3/4 |
| 2027 | 6: dv 1/1 · dc 6/1 · dt 12/10 · dl 1/11 · dl 6/12 · dc 8/12 | 26/3 |
| 2028 | 8: dj 6/1 · dl 1/5 · dt 15/8 · dj 12/10 · dc 1/11 · dc 6/12 · dv 8/12 · dl 25/12 | 14/4 |
| 2029 | 7: dl 1/1 · dt 1/5 · dc 15/8 · dv 12/10 · dj 1/11 · dj 6/12 · dt 25/12 | 30/3 |
| 2030 | 6: dt 1/1 · dc 1/5 · dj 15/8 · dv 1/11 · dv 6/12 · dc 25/12 | 19/4 |
| 2031 | 6: dc 1/1 · dl 6/1 · dj 1/5 · dv 15/8 · dl 8/12 · dj 25/12 | 11/4 |
| 2032 | 6: dj 1/1 · dt 6/1 · dt 12/10 · dl 1/11 · dl 6/12 · dc 8/12 | 26/3 |
| 2033 | 6: dj 6/1 · dl 15/8 · dc 12/10 · dt 1/11 · dt 6/12 · dj 8/12 | 15/4 |
| 2034 | 8: dv 6/1 · dl 1/5 · dt 15/8 · dj 12/10 · dc 1/11 · dc 6/12 · dv 8/12 · dl 25/12 | 7/4 |
| 2035 | 7: dl 1/1 · dt 1/5 · dc 15/8 · dv 12/10 · dj 1/11 · dj 6/12 · dt 25/12 | 23/3 |
| 2036 | 5: dt 1/1 · dj 1/5 · dv 15/8 · dl 8/12 · dj 25/12 | 11/4 |

**Com s'ha verificat (21/09/2026):** el calendari de HA
([`tarifa.jinja`](../../config/custom_templates/tarifa.jinja)) s'ha avaluat amb els filtres
de la mateixa versió d'HA, dins del contenidor, a **cada hora de 2026 a 2036** —al minut 0, al
30 i al 59 de cada franja, **289.296 instants**— contra una implementació independent en
Python: **cap discrepància**. Surten 22.392 hores de punta, 22.392 de pla i 51.648 de vall.

**Què el pot fer fallar en deu anys, i res més:**

- **Un canvi de llei**: una circular nova de la CNMC o un canvi al RD 2001/1983. Es llegeix a
  la factura —les hores de cada tram hi surten— i es corregeix a `tarifa.jinja`.
- **Si la UE abandona el canvi d'hora**, les hores locals canvien i HA només ho sabrà si la
  seva imatge porta la base de dades de zones nova. Amb la versió fixada, vol dir
  **actualitzar HA** aquell any.
- **Un canvi de contracte** a una tarifa que no segueixi els períodes regulats.

### Terme de potència

| Període | Horari | Preu |
|---|---|---|
| Punta | 08:00 – 00:00 de dilluns a divendres | 0,123030 €/kW·dia |
| Vall | 00:00 – 08:00 de dilluns a divendres + caps de setmana | 0,061562 €/kW·dia |

> Preus **sense impostos**, vigents a data de consulta (setembre de 2026) segons la pàgina
> oficial de Naturgy i Selectra. **S'actualitzen periòdicament: cal rellegir-los abans de
> fer servir les xifres per a res que importi.** Sense permanència, preus fixos per franja
> durant 12 mesos.

### Què vol dir això per al codi

**La punta és 2,47 vegades la vall.** Això és molt, i canvia el disseny del control:

- **El deshumidificador hauria de treballar preferentment en vall**, és a dir de matinada
  entre setmana i **tot el cap de setmana sencer**. Un compressor de 300–700 W en punta
  costa gairebé dues vegades i mitja el mateix en vall.
- **Els ventiladors**, en canvi, consumeixen poc (30–150 W) i el criteri que els governa és
  físic, no econòmic: si l'aire de fora asseca, ventilar surt a compte sempre. El preu no
  hauria de vetar una finestra de ventilació bona.
- Això **es combina bé amb la física**: la finestra de ventilació gratuïta a Barcelona és
  sobretot de **nit**, que és justament la franja vall. Les dues lògiques empenyen en la
  mateixa direcció.
- ✅ **El període tarifari ja és una entitat a Home Assistant** *(21/09/2026)*, i amb ell el
  cost real i no només els kWh. És la xifra que dirà si l'automatisme val la pena → a
  sota, *El cost a Home Assistant*.

> ⚠️ **A verificar:** la potència contractada del local i si el contracte és el domèstic de
> Tarifa Noche o una variant per a negocis. Amb ≤ 15 kW la 2.0TD aplica igual.

### El cost a Home Assistant

Des del 21/09/2026, l'endoll dona **watts, kWh i euros** al tauler del soterrani (vista
*Consum*, i els watts també a *Històric*). Codi:
[`packages/consum.yaml`](../../config/packages/consum.yaml); calendari i preus, **en un sol
lloc**: [`custom_templates/tarifa.jinja`](../../config/custom_templates/tarifa.jinja).

**D'on surt cada número:**

| | Font | Per què així |
|---|---|---|
| **W** | L'endoll, tal com la dona | — |
| **kWh** | El **comptador del mateix endoll** (`sensor.deshumidificador_energia`) | L'endoll integra la potència per dins, molt més sovint del que HA la veu. Integrar-la a HA (Riemann sobre els W) seria pitjor: HA només rep la potència quan canvia i Matter té un interval mínim d'informe |
| **€** | Una lectura d'aquell comptador **cada 5 minuts** (al segon 59 del minut 4, 9… 59), multiplicada pel preu del tram | Vegeu a sota |

**Per què és exacte:** totes les fronteres de tram de la 2.0TD —les 8, les 10, les 14, les 18,
les 22 i les 00— **cauen en hora en punt**, i per tant també en múltiple de 5 minuts. Cada bloc
de 5 minuts és sencer d'un sol tram, o sigui que el delta del comptador té **un sol preu**.

**Per què cada 5 minuts i no cada hora:** una hora també seria exacta, i és com es va
desplegar primer el 21/09/2026. Però els euros anaven fins a **una hora tard** i, després de
desplegar, no n'hi havia fins al cap de dues hores. Amb 5 minuts el cost es veu gairebé en viu i
quadra amb les estadístiques de 5 minuts d'HA. **Si el comptador no s'ha mogut, no s'escriu
res**: amb 8 W l'endoll avança 1 Wh cada 7,5 minuts, i la majoria de mostres no porten res.
Com a molt són ~600 files al dia; les de tensió i corrent en fan 3.600 cadascuna.

**Per què al :x4:59 i no al :x5:00:** perquè la lectura caigui **dins** de la seva franja
d'estadístiques. Al :00, els últims 5 minuts de cada hora sortirien a la barra de l'hora
següent.

**L'error que queda:** a cada frontera, el que l'endoll encara no hagi reportat. El comptador
va de 0,001 kWh en 0,001 kWh: **menys d'1 Wh mal repartit per frontera**. Amb unes 1.500
fronteres l'any i 0,14 €/kWh de diferència màxima entre trams, el pitjor cas són **uns 20
cèntims l'any**, i com que l'error va tant cap a un costat com cap a l'altre, en la pràctica
molt menys.

**Si hi ha un forat** —HA aturat, l'endoll sense resposta a l'hora de la mostra, o el
comptador quiet una estona—, no es perd res: la mostra següent cobreix tot l'interval, i si
creua trams el reparteix **suposant consum uniforme**, que és el millor que es pot dir sense
dades. La referència
es guarda als atributs del sensor de cost i HA la restaura en arrencar.

**Què inclou el preu:** el terme d'energia de cada tram, amb **l'impost especial sobre
l'electricitat (5,11269632 %)** i, damunt, **l'IVA (21 %)**: ×1,2719. Queda:

| Tram | Sense impostos | **Amb impostos** |
|---|---|---|
| Vall | 0,0739 €/kWh | **0,0940 €/kWh** |
| Pla | 0,1092 €/kWh | **0,1389 €/kWh** |
| Punta | 0,1822 €/kWh | **0,2317 €/kWh** |

**Què NO inclou, a posta:** el **terme de potència**, el **lloguer del comptador** i el
**bo social**. Són fixos per dia i no canvien pel que s'endolli, o sigui que atribuir-los a
un aparell seria inventar un repartiment.

> ✅ **L'IVA és cost** *(confirmat el 21/09/2026)*: sempre es paga, no es dedueix. Per això
> és dins del ×1,2719.
>
> ⚠️ **A contrastar amb la primera factura real** → [pendents.md](../pendents.md): que els
> preus i els dos impostos quadrin.
>
> ⚠️ **Quan canviïn els preus** (cada 12 mesos), es canvien a `tarifa.jinja` en un commit
> datat. **El cost ja acumulat no es recalcula**, i és correcte: aquells kWh es van pagar al
> preu vell.

**Les entitats** són al [conveni de noms](../domotica/noms-entitats.md#derivades--consum-i-tarifa-les-calcula-packagesconsumyaml).

## Internet — router amb targeta SIM

L'accés a Internet del local serà per **router amb targeta SIM** (dades mòbils).

### Conseqüències, i n'hi ha de grosses

**1. CGNAT pràcticament garantit.** Les connexions mòbils gairebé sempre van darrere CGNAT
i amb IP dinàmica. Això **resol per si sol** la comparativa d'[accés remot](../domotica/acces-remot.md):

- ❌ **Port forwarding + reverse proxy: impossible.** Descartat definitivament, no per
  preferència sinó per física de xarxa.
- ❌ **WireGuard pur amb el servidor al local: impossible** sense un VPS intermediari.
- ✅ **Tailscale: funciona.** És exactament el seu cas d'ús. Farà *hole punching* i, si no
  pot, caurà a relé xifrat.
- ✅ **Nabu Casa / Cloudflare Tunnel: funcionen**, perquè la connexió la inicia el local cap
  enfora.

**2. El consum de dades passa a comptar.** Fins ara no era una variable; ara sí:

- El registre de sensors i les automatitzacions són **locals**: gasten zero dades.
- El que gasta és l'**accés remot** (cada cop que obres l'app), les **actualitzacions** de
  Home Assistant i dels contenidors, i sobretot **qualsevol càmera** — el vídeo es menja una
  tarifa de dades en dies.
- Si Tailscale no aconsegueix connexió directa i cau a relé, **tot el trànsit passa dues
  vegades** per la xarxa mòbil.
- Les **còpies de seguretat fora del local** (que la proposta de
  [monitorització](../domotica/monitoritzacio.md) considera imprescindibles) han de tenir en
  compte el volum: una base de dades d'1 GB pujada cada nit no és viable per SIM. Solució:
  còpies **incrementals** i **exportacions CSV mensuals comprimides** (~10–15 MB l'any
  sencer), que és precisament el que ja es recomanava.

**3. Fiabilitat.** Un router 4G/5G pot penjar-se i necessitar un cicle d'alimentació. Això
reforça l'argument de l'**endoll intel·ligent de rearmada** alimentant el router,
independent de Home Assistant.

### Per decidir

- [ ] Operadora, pla de dades i **límit mensual**.
- [ ] Model de router: si té Ethernet (cal per a un coordinador Zigbee en xarxa i per a un
      ESP32 amb PoE), i si té *watchdog* de reconnexió.
- [ ] Cobertura mòbil al local — i especialment **al soterrani**, on probablement no n'hi
      haurà: el router ha d'anar a la planta baixa.
- [ ] Si l'operadora ofereix IP pública fixa com a extra (algunes ho fan per pocs euros).
      No és necessari amb Tailscale, però simplifica.

## Aigua

Sense dades. **Pendent de verificar** l'estat del comptador i del contracte.
