# Home Assistant — muntatge del servidor

## Estat actual (20 de setembre de 2026, vespre)

**Home Assistant ja corre.** El servidor està muntat i s'hi entra des de fora del local.

- [x] Decidit: el servidor serà un portàtil que ja es té, no un Raspberry Pi ni un NUC nou.
- [x] Decidit: sistema operatiu base **Linux Mint**.
- [x] Pen drive gravat i **Mint 22.3 instal·lat** al portàtil.
- [x] **Docker CE** del repositori oficial.
- [x] **HA Container 2026.9.3** en marxa, amb la versió fixada.
- [x] `check_config` net.
- [x] **SSH amb clau** des del portàtil de casa.
- [x] **Tailscale connectat**, amb l'**expiració de clau desactivada**.
- [x] **Compte d'HA creat** i **dos testimonis de llarga durada** emesos.
- [ ] **Verificar `purge_keep_days: 730` contra la instància en calent** (Porta A).
      *Estat 20/09/2026: `check_config --info recorder` el llegeix com a `730 [source
      /config/configuration.yaml:29]`. Això és el fitxer tal com el llegeix HA, no la
      instància en calent: falta la comprovació per `/api/config` amb el testimoni.*
- [ ] **Esborrar la integració `bluetooth` d'HA** — vegeu el parany del
      [runbook](runbook-servidor.md#-el-bluetooth-omple-el-log).
- [ ] Emparellar el hub H110 al **router SIM** i després **emparellar-lo per Matter**. ⚠️ **No per `tplink`**: el rebutja amb *«Unsupported device»* pel xifratge TPAP. Cal el contenidor `matter-server`, que ja és al `docker-compose.yml`.
- [ ] Decidir la ubicació física definitiva dins del local.

> **Auditoria del 20/09/2026, feta per SSH contra la màquina en marxa.** El que ja hi és:
> Mint 22.3 amb **0 paquets per actualitzar**, la imatge d'HA de 3,43 GB **al disc**, HA
> responent **HTTP 200** per LAN i per Tailscale, **45 entitats** registrades i el paquet
> `rosada` carregat sencer (hi són `sensor.decisio_del_soterrani`, els cinc punts de rosada,
> `input_select.mode_soterrani` i els dos `input_number`). **No falta res de gros per
> instal·lar**: el que falta és el que encara no hem escrit (`nit.py`, `desplega.sh`), el
> repositori `Local-data`, i quatre eines petites — vegeu la llista de sota.

### On és cada cosa ara mateix

Tot el maquinari és **a casa**, no al local: s'hi està fent l'assaig general abans de
portar-ho. La idea és muntar-ho tot sobre el **router SIM** —el mateix que hi haurà al
local— perquè el que es provi aquí sigui exactament el que hi correrà: CGNAT, Tailscale,
reserves DHCP i el Wi-Fi del hub, tot igual.

> ⚠️ **Les descàrregues grosses es fan per la fibra de casa, no per la SIM.** La imatge d'HA
> sola són **3,43 GB**. Es va baixar abans de passar el portàtil al router SIM, i per això
> allà l'arrencada no gastarà dades.

## El pas a la SIM — l'assaig general de debò

> Escrit el **20/09/2026**, amb el servidor ja en marxa sobre la fibra de casa.

Passar el portàtil al router de la SIM no és un tràmit administratiu: és **la porta que
desbloqueja la Fase B**, i alhora la prova de tres coses que avui no estan provades —que
Tailscale entra per darrere del **CGNAT**, que hi ha **cobertura** on anirà el router, i
**quantes dades gasta tot plegat al mes**.

Per això es fa **aviat**. El que s'ha de fer abans és, només, el que després surt car: les
descàrregues i tot el que obligui a tenir el portàtil al davant.

### Per què no es pot ajornar

| | |
|---|---|
| **HA no veu cap sensor fins que no comparteix xarxa amb el hub** | La via és **Matter**, que va per **IPv6 i multidifusió a la xarxa local**: encara més exigent que una consulta per IP, perquè sense xarxa del host no es descobreix ni s'empara res. Mentre el hub i Home Assistant siguin a xarxes diferents no es grava ni una lectura, i el rellotge dels **28 dies de la Fase B encara no ha començat** |
| **La integració es configura un cop i es guarda la IP** | Afegir-la sobre la xarxa de casa obliga a refer-la després. Per això el [runbook](runbook-servidor.md) diu de no tocar-la fins que el hub sigui al **Wi-Fi definitiu** |
| **El calendari** | Del 20/09/2026 al 09/03/2027 hi caben els 28 dies de la Fase B, la Fase C i el dossier: **un cop cadascun**. Cada setmana que s'ajorna la SIM és una setmana d'hivern que no es mesura |

### Abans de desendollar la fibra

#### 1. El que s'ha de baixar per fibra

```bash
ssh -t local-ha "sudo apt update && sudo apt full-upgrade -y && sudo apt install -y vnstat smartmontools rsync gnupg jq sqlite3"
```

| Paquet | Per a què |
|---|---|
| **`vnstat`** | **Comptar les dades de la SIM** per dia i per mes des del propi servidor. Sense això només queda el comptador del router, que es perd a cada reinici |
| `smartmontools` | SMART del disc — tasca **0.5** de [fases.md](fases.md) |
| `rsync` | La còpia nocturna al disc USB |
| `gnupg` (+ `openssl`, ja present) | El tarball xifrat setmanal i el segell RFC 3161 |
| `jq`, `sqlite3` | Mirar `/api/states` i la base de dades sense muntar res |

I confirmar que la imatge d'HA ja és al disc, perquè cap arrencada la torni a baixar:

```bash
ssh local-ha "docker image ls | grep home-assistant"
```

> ⚠️ **`unattended-upgrades` seguirà baixant seguretat cada nit, ja sobre la SIM.** Són
> desenes de MB al mes, no GB, però compten contra el pla. El primer mes de `vnstat` dirà
> la xifra real.

#### 2. El que demana tenir el portàtil al davant

Hi ha coses que no es poden fer per SSH: el BIOS es toca amb el teclat de la màquina. Un cop
el portàtil sigui al local, **cada una d'aquestes comprovacions és un viatge**, i n'hi ha una
—*restore on AC power loss*— que **pot canviar una decisió d'arquitectura**: si l'opció no hi
és, el pla d'arrencada desatesa de [decisio-stack.md](decisio-stack.md) s'ha de refer amb una
mitigació, i això val més saber-ho al setembre.

Es fa tot en **una sola tanda**, amb la màquina apagada al davant. La llista viva, per anar-la
marcant, és a **[pendents.md → 🔧 Tanda física](../pendents.md)**; aquí només hi ha el perquè,
i com s'entra al BIOS és més avall, a [Entrar al BIOS](#entrar-al-bios).

#### 3. Les caselles de la Porta A que no depenen de la xarxa

- [x] ~~Crear el **compte d'HA** i un **testimoni de llarga durada**.~~ ✅ **Fet el
      20/09/2026:** compte creat i **dos** testimonis de llarga durada emesos.
- [ ] ⚠️ **Verificar `purge_keep_days: 730` contra la instància en calent**, no contra el fitxer. És l'única línia del projecte que no té arreglada a posteriori.
- [ ] **Fixar els noms d'entitat** de [noms-entitats.md](noms-entitats.md) **abans** d'emparellar el hub per Matter: renombrar després parteix la sèrie.

### I un cop a la SIM, en aquest ordre

| # | Pas | Què s'hi comprova |
|---|---|---|
| 1 | Portàtil al router de la SIM, **per cable** si el router té RJ-45 | Que el servidor no depengui del Wi-Fi |
| 2 | **Reserva DHCP** per al portàtil i per al hub | Que una IP nova no trenqui la integració ni l'àlies d'SSH |
| 3 | `tailscale status` i `tailscale ping local-ha` des de casa | **Si diu `via DERP` en comptes de directe**, el CGNAT està relegant el trànsit: funciona, però amb latència i consum |
| 4 | Deixar-ho **72 h** i llegir `vnstat -d` i `vnstat -m` | El consum en repòs, abans d'afegir-hi sensors. És el número que decideix el pla de dades |
| 5 | Emparellar el **H110 al Wi-Fi de la SIM** | — |
| 6 | **Només llavors**, emparellar el hub per **Matter** i renombrar les entitats | A partir d'aquí comença a gravar-se l'històric: els noms ja no es toquen |

## El maquinari del servidor

> Identificat el **20/09/2026** a partir de les etiquetes de la base del portàtil.
> **Els números de sèrie no són aquí**: van a `docs/privat/identificacio.md`.

**Acer TravelMate B3 — TMB311-32-C4JR**, plataforma **N20Q14**, fabricat el **29/06/2022**.
És un portàtil de gamma educativa d'11,6": reforçat, **sense ventilador** i de consum molt
baix. És un perfil que, sense pretendre-ho, encaixa bé amb fer de servidor permanent.

### El que diu l'etiqueta — confirmat

| Camp | Valor |
|---|---|
| Sèrie | TravelMate B3 (l'etiqueta és compartida amb la TravelMate Spin B3) |
| Referència | **TMB311-32-C4JR** |
| Plataforma | **N20Q14** |
| Alimentació | **19 V ⎓ 2,37 A** *o* **20 V ⎓ 2,25 A per USB-C** — 45 W en tots dos casos |
| Ràdio | **Intel AX201NGW** → **Wi-Fi 6** (802.11ax) + Bluetooth 5 |
| Data de fabricació | **29/06/2022** |

> **Detall que val la pena:** admet **càrrega per USB-C PD de 45 W**. Un carregador USB-C
> genèric és molt més fàcil de reemplaçar a corre-cuita que un connector propietari d'Acer, i
> per a un aparell que ha d'estar endollat 24/7 durant un hivern sencer, això és una peça de
> recanvi menys de la qual preocupar-se.

### La configuració real — ✅ confirmada el 20/09/2026

L'etiqueta no diu processador, memòria ni disc: dins d'un mateix `TMB311-32` Acer va vendre
configuracions diferents. Llegit per SSH des de la màquina ja instal·lada:

| Camp | Valor real | Vs. el que s'esperava |
|---|---|---|
| Processador | **Intel Celeron N5100** — 4 nuclis, 1,1 GHz base (Jasper Lake, 6 W) | 🎉 Millor: se'n temia un N4500 de 2 nuclis |
| Memòria | **4 GB** (3,6 GiB útils), soldada — **no ampliable** | Com es preveia |
| Disc | 🎉 **SSD NVMe Samsung MZVLQ128HCHQ (PM991), 119,2 GB** | **No és eMMC.** Era la incògnita que més condicionava |
| Sistema | Linux Mint 22.3 (base Ubuntu *noble*) | — |
| Pantalla | 11,6" HD 1366 × 768 | — |
| Ports | 2× USB-A, 1× USB-C (dades + PD + DisplayPort), HDMI, **RJ-45 gigabit**, lector microSD, jack | ⏳ A confirmar visualment |
| Bateria | **42,5 Wh reals** de 53 Wh de disseny → **80 % de salut** | Desgast de 4 anys; segueix servint |
| Disc lliure | 99 GB de 117 | — |

**Com es torna a comprovar**, si mai cal:

```bash
lscpu | grep -E 'Model name|^CPU\(s\)'
free -h
lsblk -d -o NAME,SIZE,MODEL,TRAN
```

La línia que decidia era la darrera: `mmcblk0` hauria estat eMMC soldada; `nvme0n1` és un
**SSD M.2 substituïble**. Va sortir `nvme0n1`.

### Serveix per a Home Assistant?

**Sí, i amb marge.** La raó no és que el portàtil sigui potent —no ho és— sinó que
[l'stack decidit](decisio-stack.md) és deliberadament petit: SQLite, sense Postgres, sense
Grafana i sense panell web. Des del 21/09/2026 són **dos** contenidors —hi entra
`matter-server`—, i això ja **no** és una estimació: s'ha mesurat amb els dos en marxa.

| Recurs | El que hi ha | El que demana l'stack decidit | Veredicte |
|---|---|---|---|
| **CPU** | Celeron **N5100, 4 nuclis**, 6 W | HA amb ~40 entitats + `matter-server` + un script de Python de pocs minuts cada nit | ✅ **Sobra** — càrrega mesurada: **0,07** de mitjana |
| **RAM** | **3.716 MB** útils | **Mesurat el 21/09/2026:** HA **436 MB** (pic **609**) + `matter-server` **88 MB** (pic **89**) = **~700 MB de pic entre els dos** | ✅ **Sobra** — són el **19 %**. El segon contenidor de Matter costa **89 MB**: no és el problema que semblava |
| **Disc** | **SSD NVMe de 128 GB** | Mint + Docker ≈ 20 GB. SQLite a 730 dies amb ~40 entitats ≈ **2–4 GB** | ✅ **De sobres**, i amb escriptura ràpida |
| **Xarxa** | Wi-Fi 6 **+ RJ-45 gigabit** | Hub Tapo per IP local + Tailscale | ✅ I el **cable** evita que el servidor depengui del Wi-Fi |
| **Alimentació** | 45 W màx.; en repòs amb la pantalla apagada, **8–12 W** | 24/7 | ✅ ≈ 7 kWh/mes → **menys d'1 €/mes** amb la [tarifa contractada](../local/subministraments.md) |

> La comparació justa: el Raspberry Pi 4 que arreu es fa servir per a això té 4 nuclis lents,
> 4 GB de RAM i arrenca d'una microSD. Aquest portàtil hi juga a la mateixa lliga **i a sobre
> porta pantalla, teclat, bateria i port Ethernet**. Per a aquest projecte, comprar maquinari
> nou no compraria res.

#### ~~Les dues reserves reals~~ → només en queda una

**1. ~~Si el disc és eMMC, no hi pot haver *swap*.~~** ✅ **Resolta: el disc és un SSD NVMe.**
La preocupació era que una eMMC soldada, lenta en escriptures petites i amb menys cicles,
s'anés gastant amb el trànsit del `recorder` i sobretot amb el *swap*. Amb un NVMe Samsung
desapareix: no cal `zram`, ni vigilar la vida del disc, i a sobre és **substituïble** obrint
la tapa. Queda com a bona pràctica mantenir `vm.swappiness` baix, però ja no és crític.

**2. La memòria està soldada.** No hi ha camí d'ampliació: si un dia s'hi volgués afegir
Postgres, InfluxDB i Grafana, la decisió no seria «instal·lar-ho» sinó «canviar de màquina».
És un argument més a favor de mantenir l'stack petit, no una limitació nova.

### 🔬 La RAM, mesurada — i la sorpresa no és Matter

> Mesurat per SSH contra la màquina en marxa el **21/09/2026, 01:06**, amb 3 h 25 min
> d'*uptime* i els dos contenidors actius.

Quan va entrar el segon contenidor semblava raonable témer pel marge de memòria. **No és
aquí.** El repartiment real dels 3.716 MB:

| Qui | RAM | % |
|---|---|---|
| 🦊 **Firefox** — 14 processos, obert a l'escriptori del servidor | **1.576 MB** | **42 %** |
| 🖥️ **Escriptori Cinnamon** (`cinnamon` + `Xorg` + `lightdm`) | **374 MB** | 10 % |
| 🏠 Home Assistant | 436 MB *(pic 609)* | 12 % |
| 🔗 `matter-server` | **88 MB** *(pic 89)* | **2 %** |

**La feina de debò —els dos contenidors— són ~700 MB de pic: el 19 %.** El que ocupa la
meitat de la màquina és **un navegador i un escriptori gràfic**, que no tenen cap paper a
l'stack decidit.

- ✅ **Matter no és el problema.** 89 MB de pic, i pràcticament sense variació. La reserva que
  s'havia obert en afegir el segon contenidor **queda tancada**.
- ⚠️ **Però la màquina arrenca a `graphical.target`.** Amb `multi-user.target` —s'administra
  per SSH i Tailscale, la pantalla no fa res— s'alliberen els **374 MB** de l'escriptori i
  desapareix el risc que algú hi torni a deixar un navegador obert.
- 📌 **Firefox, tancat.** No és una fuita ni un error de disseny: és una sessió que algú va
  deixar oberta. Però en una màquina de 3,6 GB que ha de gravar sense interrupció durant un
  hivern, 1,5 GB en un navegador és exactament el tipus de cosa que **ningú recorda el dia que
  peta**.
- 🟢 **Ara mateix no hi ha pressió.** El PSI de memòria marca `0.00` a 10 s, 60 s i 300 s, i
  queden **1.473 MB disponibles**. Els 667 MB al *swap* són `vm.swappiness=60` —el valor per
  defecte d'escriptori— fent la seva feina, no un senyal d'ofec.

> ⚠️ **Amb una reserva honesta:** els 89 MB del `matter-server` s'han mesurat **abans** de
> tenir la xarxa Matter poblada. Creixerà en emparellar el hub i els sis sensors. L'estat per
> aparell de Matter és petit i no canvia el veredicte, però **la xifra s'ha de tornar a mirar
> després d'emparellar**, no donar-la per bona.

### 🧱 El sostre de memòria — perquè una fuita no s'endugui la màquina

Que avui sobri RAM no vol dir que en sobri sempre. El 21/09/2026 els dos contenidors corrien
**sense cap sostre** —`docker inspect` retornava `mem_limit=0` per tots dos—, i això vol dir
que una fuita de memòria a Home Assistant, o al `matter-server`, no s'atura enlloc: creix fins
que el kernel comença a matar processos **de tota la màquina**, triats per ell i no per
nosaltres. Amb els 4 GB **soldats** d'aquest portàtil no hi ha camí d'ampliació: el marge es
defensa posant-hi sostre, no comprant memòria.

I el que hi ha en joc no és la comoditat, és l'històric. ⚠️ Això es va escriure quan
l'objectiu era defensar la retenció, i deia «pèrdua de valor probatori». Amb el
[canvi d'objectiu del 21/09/2026](decisio-stack.md) **l'argument no cau, canvia de motiu**:
les dades crues i `purge_keep_days: 730` es mantenen expressament —són «l'única cosa
irreversible»— i un forat es paga igual, perquè sense sèrie no hi ha llindars amb dades
pròpies i **aquest hivern passa un sol cop**.

| Servei | Pic mesurat | `mem_limit` | `mem_reservation` | Marge sobre el pic |
|---|---|---|---|---|
| `homeassistant` | 609 MB | **1.536 MB** | 512 MB | 2,5× |
| `matter-server` | 89 MB | **512 MB** | 128 MB | 5,7× |
| | | **2.048 MB sumats** | | **de 3.716 MB** |

**La propietat que importa no és cap dels dos números per separat: és la suma.** Encara que
els dos contenidors toquessin sostre alhora, a l'amfitrió li quedarien **~1.660 MB**. Dit
d'una altra manera: el kernel no ha de triar mai entre matar Home Assistant i matar-se ell.
Un contenidor mort i reiniciat costa un forat d'un minut; un amfitrió mort costa el forat que
trigui algú a arribar al local.

Els sostres són **generosos a posta**. No hi són per estrènyer el consum —no hi ha cap
problema de consum— sinó per posar un terra sota el pitjor cas. El `mem_reservation`, en
canvi, va **just per sobre del règim normal**: és el que el kernel intenta respectar quan
l'amfitrió va just, i marca qui ha de cedir primer.

#### El que NO s'hi ha posat, i per què

- **`memswap_limit`** — sense declarar-lo, Docker deixa el contenidor arribar a **2× el
  sostre** comptant l'intercanvi. Això és el que volem: un pic puntual s'aguanta al swap en
  comptes de morir, i la RAM de l'amfitrió **ja queda protegida pel `mem_limit` tot sol**, que
  és l'objectiu de tot plegat. Matar HA per un pic de trenta segons seria pagar un forat a
  l'històric a canvi de res.
- **`oom_kill_disable`** — mai. En comptes de matar el contenidor el **congela**: HA deixaria
  de gravar sense arribar a sortir, i per tant `restart: unless-stopped` no el rescataria. És
  exactament el mode de fallada silenciosa que aquest projecte no es pot permetre.

### Quan el sostre es toca

La seqüència, quan un contenidor arriba al seu `mem_limit`:

1. El kernel mata el procés més gros **de dins del cgroup del contenidor**. La resta de la
   màquina no se n'assabenta: aquest és tot el propòsit del sostre.
2. Si el mort és el procés principal, el contenidor **surt amb codi 137**.
3. `restart: unless-stopped` el torna a aixecar tot sol. HA torna a respondre en ~30 s, que és
   el que va trigar a la primera arrencada.
4. A l'històric hi queda **un forat de la durada de l'aturada**.

El pas 4 és el que fa que això no pugui quedar sense rastre.

#### 🪤 El parany: `OOMKilled` s'esborra sol

La temptació és comprovar-ho amb `docker inspect -f '{{.State.OOMKilled}}'`. **No n'hi ha
prou.** Amb `restart: unless-stopped` el contenidor es torna a aixecar sol, i en aixecar-se
l'estat es renova: un OOM de matinada pot marcar `false` a les nou del matí. Serveix si el
trobes aturat; **no serveix com a registre**.

El rastre que dura és el del **kernel**, i el journal el guarda —amb sostre de 200 MB, o sigui
setmanes:

```bash
journalctl -k --since "-7 days" | grep -iE 'oom-kill:|Out of memory: Killed process'
```

#### On ha de quedar escrit

| On | Qui ho escriu | Cada quan | Estat |
|---|---|---|---|
| **`scripts/comprova.sh`** | el mateix guió | quan el llances | ✅ **Fet.** Verifica que tots dos sostres hi siguin i **quadrin amb el `docker-compose.yml`**, i llegeix el journal del kernel dels últims 7 dies |
| **Cos del ping de `bategada`** | `bategada.sh` | cada 30 min | ⏳ El guió **encara no existeix** (fase A.11). Quan s'escrigui, el cos ha de portar-hi el recompte d'OOM i els reinicis dels dos contenidors |
| **El guió nocturn** | `nit.py` | cada nit | ⏳ `nit.py` **encara no existeix**. És l'únic dels tres que dona un registre **permanent i datat**. ⚠️ Ja **no** va a `Local-data`, que [va quedar superat el 21/09/2026](decisio-stack.md): va amb la còpia nocturna al disc USB del local |

⚠️ **Aquí hi havia un error de plantejament que val la pena deixar escrit.** El lloc natural
semblava el **`desplegaments.log`**, però aquell fitxer és un **registre de desplegaments**:
l'escriu `desplega.sh` (pas 9) i només corre quan despleguem. Un OOM a les 04:00 no és un
desplegament i **no hi cauria mai**. Per això el registre permanent va al **guió nocturn**,
que sí que corre cada dia passi el que passi, i el `desplegaments.log` es queda amb la feina
que li toca: explicar els forats que **provoquem nosaltres** desplegant.

> ⚠️ **Actualitzat amb el canvi d'objectiu.** El pas 9 original deixava el `desplegaments.log`
> dins de l'arbre de `Local-data`, que [va quedar superat](decisio-stack.md). El fitxer segueix
> tenint sentit i el raonament de sobre no canvia gens —un OOM continua sense ser un
> desplegament—; el que canvia és que **es queda al local**, com la resta de còpies.

Els tres tenen papers diferents i cap no substitueix els altres: `comprova.sh` és el
diagnòstic **quan vas a mirar**, el ping és l'avís **que et fa anar a mirar**, i el guió
nocturn és el que d'aquí a un any **encara hi serà**.

### 🔽 `vm.swappiness`: de 60 a 10

El valor de fàbrica, **60**, és un valor d'escriptori: assumeix que hi ha algú davant la
pantalla i que canviar de finestra pot esperar una mica de disc. Aquí no hi ha ningú davant la
pantalla —i si tot va bé, aviat no hi haurà ni pantalla—; hi ha un `recorder` escrivint a
SQLite cada pocs segons durant dos anys.

Es pot baixar perquè **la reserva que ho impedia ja va caure**: el 20/09/2026 el disc va
resultar ser un **SSD NVMe** i no una eMMC soldada. Amb eMMC, tocar l'intercanvi era gastar
cicles d'escriptura d'un disc no substituïble; amb NVMe, no.

Queda a **10**, aplicat per `scripts/prepara-host.sh` a `/etc/sysctl.d/99-memoria.conf`, de
manera que un servidor refet de zero el torna a tenir sense que ningú se'n recordi.

⚠️ **Dos matisos, que és el que sol fallar:**

- **No és treure l'intercanvi.** Els 4 GB de swap segueixen sent la xarxa de seguretat sota els
  sostres del `docker-compose.yml`. Amb `swappiness=10` el kernel hi recorre **menys**, no
  deixa de recórrer-hi.
- **No buida el que ja hi ha a dins.** Els 667 MB que hi havia el 21/09 no es mouran sols:
  `swappiness` és la política d'ara endavant. Es netegen amb un **reinici** —no amb
  `swapoff -a`, que exigeix encabir-ho tot a la RAM i aquí val més no jugar-hi.

### El que aquest portàtil NO ha de fer

| Cosa | Per què no |
|---|---|
| **Frigate o qualsevol NVR** | La detecció d'objectes en vídeo demana CPU, RAM i un flux d'escriptura constant que es menjaria la màquina i el disc. Les càmeres Tapo es queden a la seva app, gravant a la seva pròpia microSD |
| **Escriptori d'ús diari** | Cada cop que s'hi obrís un navegador «per mirar una cosa» es competiria amb el servidor per la RAM |
| **Actualitzacions automàtiques** | Ja decidit: `unattended-upgrades` només de seguretat, i **cap actualització d'HA fins al 10/03/2027** |

### ⚠️ On ha de viure: a la planta baixa, no al soterrani

El soterrani és, per definició del projecte, l'espai **humit**: les lectures del 20/09/2026 hi
donen 62–66 % d'HR, i a l'hivern pujaran. L'electrònica de consum no està feta per viure-hi
de manera permanent: corrosió dels contactes, i condensació damunt dels components quan la
màquina està freda i hi entra aire més càlid.

Que sigui **sense ventilador** hi juga a favor —no aspira aire, i per tant no aspira humitat
ni pols—, però també vol dir que es refreda per la carcassa: no ha d'estar tapat ni tancat
dins d'un armari.

→ **El servidor va a la planta baixa**, en un lloc airejat i, si es pot, connectat per
**cable Ethernet**. Al soterrani només hi han de viure els sensors, que sí que estan pensats
per estar-hi.

### La bateria és un SAI, però amb lletra petita

Que el servidor tingui bateria pròpia és un avantatge real i ja recollit: davant d'un tall de
llum **Home Assistant no cau i pot registrar el tall**, cosa que té valor per a l'expedient de
les humitats. La bateria dona **42,5 Wh reals** —el 80 % dels 53 Wh de disseny, que són
quatre anys de desgast— i amb ~10 W de consum surten **unes 4 hores** de marge.

⚠️ **Però el servidor és l'únic aparell de la cadena que té bateria.** En un tall de corrent:

| Aparell | Què passa |
|---|---|
| Portàtil | ✅ Segueix viu 4–5 h |
| **Hub Tapo H110** | ❌ Mor a l'instant → **deixen d'arribar lectures dels sensors** |
| **Router de la SIM** | ❌ Mor a l'instant → sense Tailscale, sense avís i sense pujada a GitHub |

Per tant, avui, el que la bateria compra **no** és continuïtat de dades: és que la màquina no
s'apagui de cop —cosa que protegeix la base de dades— i que segueixi viva quan torni el
corrent, sense ningú al local. Que hi hagi un **forat** a les sèries durant el tall és
inevitable sense un SAI petit per al router i el hub (~40–60 €). **Queda com a pendent.**

⚠️ I la lletra petita de la lletra petita: una bateria de liti **endollada al 100 % de manera
permanent durant dos anys** es degrada i es pot inflar. Convé buscar al BIOS un límit de
càrrega (vegeu sota).

> **Comprovat el 20/09/2026:** per Linux **no hi ha cap camí**. A
> `/sys/class/power_supply/BAT*/` no hi ha cap fitxer `charge_control_*_threshold`, que és el
> que exposen els portàtils on el límit de càrrega es pot posar per programari. Si aquest
> límit existeix, és **només al BIOS**; si tampoc no hi és, l'única mitigació real és
> assumir-ho i vigilar que la bateria no s'infli. Estat de la bateria avui: **42,5 Wh de 53
> Wh de disseny, 80 % de salut, «fully-charged»**.

## Entrar al BIOS

El d'aquest Acer és un **InsydeH2O**. Cal per a tres coses d'aquest projecte: arrencar del pen
drive, mirar la configuració real de la màquina, i deixar-la preparada per fer de servidor.

### Com s'hi entra

1. **Apagar del tot** el portàtil (no suspendre'l).
2. Prémer el botó d'engegada i, **immediatament**, anar picant **`F2`** repetidament fins que
   aparegui el BIOS. La finestra és d'un segon o dos.
3. Per triar d'on arrenca **només aquesta vegada**: la tecla és **`F12`**, picada igual.

> **Si `F12` no fa res**, és que ve desactivada de fàbrica: s'entra amb `F2` i, a la pestanya
> **Main**, es posa **`F12 Boot Menu` → `Enabled`**.
>
> **Si `F2` tampoc no enganxa** perquè Windows arrenca massa de pressa, s'hi pot entrar des
> del sistema: *Configuració → Sistema → Recuperació → Inici avançat → Reinicia ara →*
> *Resoldre problemes → Opcions avançades → **Configuració del microprogramari UEFI***.
>
> ⚠️ **`Alt`+`F10`** és la recuperació d'Acer, que **esborra el disc**. No és aquesta.

Per sortir desant els canvis: **`F10`**.

### Què s'hi ha de mirar i tocar

| Pestanya | Opció | Què fer-hi |
|---|---|---|
| **Information** | CPU, System Memory, HDD/SSD | **Llegir-ho i apuntar-ho.** Aquí surten el processador, els GB de RAM i el model de disc reals — les tres dades pendents de la taula de dalt |
| **Main** | `F12 Boot Menu` | **Enabled** — necessari per arrencar del pen drive |
| **Boot** | Ordre d'arrencada | Posar-hi **`USB HDD`** per damunt mentre es fa la instal·lació, i tornar-ho enrere quan estigui feta |
| **Boot** | `Secure Boot` | **Linux Mint arrenca amb Secure Boot activat**: no cal tocar-ho. Només caldria desactivar-lo si algun dia es passés a HA OS o a un nucli sense signar |
| **Security** | `Set Supervisor Password` | ⚠️ A Acer, `Secure Boot` està **en gris** fins que no es posa una contrasenya de supervisor. Si es posa, **apuntar-la al gestor de contrasenyes**: sense ella no es pot tornar a entrar al BIOS |
| **Main / Power** | `Power On by AC`, *AC Recovery*, `Wake on LAN` | ⏳ **Comprovar si hi són.** Vegeu l'avís de sota |
| **Main** | Límit de càrrega / `Battery Calibration` | ⏳ Comprovar si hi és, per no tenir la bateria al 100 % dos anys seguits |

### ⚠️ Una premissa de `decisio-stack.md` que s'ha de verificar aquí

[`decisio-stack.md`](decisio-stack.md) dona per fet que el sistema base tindrà **arrencada
automàtica després d'un tall de corrent** (*restore on AC power loss*). En **plaques
d'escriptori** aquesta opció hi és sempre; **en portàtils sovint no hi és**, perquè el
fabricant assumeix que la bateria ja fa aquesta funció.

- Si **hi és** → activar-la i llestos.
- Si **no hi és** → el risc real és un tall **més llarg que la bateria**: la màquina s'apaga,
  torna el corrent i **es queda apagada** fins que algú vagi al local a prémer el botó. Un
  endoll intel·ligent de rearmada **no ho resol**, perquè no pot prémer cap botó.

En aquest segon cas hi ha dues mitigacions, i totes dues s'han de decidir:

1. **Apagada ordenada** per bateria baixa (a ~20 %), perquè almenys la base de dades no es
   corrompi, i assumir la visita presencial.
2. **`Wake on LAN`**, si el BIOS el suporta amb la màquina apagada — cosa que en portàtils
   alimentats només per bateria és poc habitual.

### Mentre el portàtil faci de servidor

Dues coses que no són al BIOS sinó al sistema, però que van aquí perquè s'obliden:

```bash
# Que tancar la tapa NO suspengui la màquina
sudo mkdir -p /etc/systemd/logind.conf.d
sudo tee /etc/systemd/logind.conf.d/99-servidor.conf >/dev/null <<'CONF'
[Login]
HandleLidSwitch=ignore
HandleLidSwitchDocked=ignore
HandleLidSwitchExternalPower=ignore
IdleAction=ignore
CONF
sudo systemctl restart systemd-logind
```

> ⚠️ **Va en un *drop-in*, no editant `/etc/systemd/logind.conf`.** És el que fa
> `scripts/prepara-host.sh` i és **l'únic lloc on mira `scripts/comprova.sh`**: si es toca el
> fitxer principal, la tapa queda ben configurada però el verificador dirà que **suspèn**. El
> drop-in, a més, sobreviu a una actualització del paquet `systemd`.

I desactivar la suspensió automàtica i l'apagada de pantalla per inactivitat des de la
configuració d'energia de Mint. **Un servidor que es suspèn és un servidor que no registra
res** — i, en aquest projecte, una sèrie de dades amb un forat.

## Per què HA Container — decisió tancada

> ✅ **Decidit i en marxa:** **HA Container** sobre Docker, versió **2026.9.3** fixada i
> congelada fins al **10/03/2027**. Mana [decisio-stack.md](decisio-stack.md). La taula es
> conserva perquè explica **per què** van caure les altres tres vies, no perquè quedi res
> per triar.

| Mètode | Add-ons | Per què no — o per què sí |
|---|---|---|
| **HA OS** (bare metal) | Sí | El sistema operatiu *és* Home Assistant i es menja el disc sencer: incompatible amb tenir Mint a sota, i amb Mint se'n anirien els scripts, els *timers* i el git de què depèn tot el desplegament |
| **HA Supervised** | Sí | Oficialment només sobre **Debian** net, i Mint no és base suportada. Pitjor encara: **decideix ell quan reiniciar HA**, i una actualització no planificada és un forat a l'històric |
| ✅ **HA Container** (Docker) | **No** | Suportat sobre qualsevol Linux i deixa el host de propòsit general. Es perd la botiga d'add-ons, i això s'ha notat el 21/09: el servidor Matter, que amb Supervised seria un add-on d'un clic, aquí és un **segon servei al compose**. Es paga de bon grat per no cedir el control del host |
| **HA Core** (venv de Python) | No | Tot manual, i sense l'aïllament ni la reproductibilitat d'una imatge fixada |

## Les premisses de partida — on ha quedat cadascuna

La llista amb què es va començar el projecte, amb l'estat real a **20/09/2026**. Cap d'elles
no és ja una decisió oberta: totes remeten a [decisio-stack.md](decisio-stack.md).

| Premissa | On ha quedat |
|---|---|
| **On viu el servidor** | ✅ **Al local**, amb Internet per SIM i alimentació pròpia. ⏳ Queda la **ubicació exacta** dins del local — planta baixa, mai al soterrani |
| **Alimentació** | ✅ El portàtil té bateria: fa de SAI per a ell mateix i **registra el tall**, cosa rellevant per demostrar que la ventilació estava operativa. ⚠️ No cobreix ni el hub ni el router — vegeu la lletra petita de la bateria, més amunt |
| **Arrencada automàtica** | ✅ La meitat de **programari**, verificada amb un reinici real: tornen sols `ssh`, `docker`, `tailscaled` i HA. ⏳ La de **maquinari** (*restore on AC power loss*) és una casella de la tanda física al BIOS |
| **Accés remot** | ✅ **Tailscale**, connectat el 20/09/2026 amb l'expiració de clau desactivada, i **única via**. Nabu Casa, el *port forwarding* i el WireGuard pur queden descartats pel CGNAT → [acces-remot.md](acces-remot.md) |
| **Còpies de seguretat** | ✅ Decidides: instantània `VACUUM INTO` + disc USB al local cada nit, i tarball xifrat de `.storage`+`secrets.yaml` a `Local-data` cada diumenge. ⏳ Falta escriure `nit.py` |
| **Retenció de l'històric** | ✅ Resolta **sense canviar de motor**: `purge_keep_days: 730` sobre **SQLite**, amb `commit_interval: 30` i `exclude` per llistes explícites |

> ⚠️ **PostgreSQL, MariaDB i InfluxDB estan descartats**, no ajornats. El dipòsit de la prova
> no és el motor de la base de dades sinó el **CSV diari immutable a git**, amb SHA-256 i
> segell RFC 3161; un segon motor només compraria un mode de fallada silenciós més. El que
> **sí** queda obert és verificar `purge_keep_days: 730` **contra la instància en calent** —
> és la Porta A, i és l'única línia del projecte que no té arreglada a posteriori.

## Registre d'instal·lació

Aquí s'anirà anotant què s'ha fet realment, amb data.

| Data | Què |
|---|---|
| 20/09/2026 | Preparant el pen drive amb Linux Mint |
| 20/09/2026 | **Maquinari del servidor identificat:** Acer TravelMate B3 TMB311-32-C4JR (N20Q14), fabricat el 29/06/2022. Veredicte: suficient per a l'stack decidit. Pendent de confirmar CPU, RAM i tipus de disc a la pestanya *Information* del BIOS |
| 20/09/2026 | **El pen drive no arrencava.** Causa: al BIOS d'Acer cal tocar l'arrencada — `F12 Boot Menu` ve desactivat de fàbrica i l'ordre del `Boot` apunta al disc intern. Resolt: **Mint arrenca** |
| 20/09/2026 | **Esquelet de la instal·lació escrit al repositori** (fase A.5/A.6/A.7): `.gitattributes`, `docker-compose.yml` amb la versió per fixar i `config/configuration.yaml` amb `purge_keep_days: 730` i `commit_interval: 30` |
| 20/09/2026 | **`scripts/prepara-host.sh`** (fase A.2): SSH, zona horària i NTP, cap suspensió, tapa ignorada, Docker CE oficial i sostre al journal. Existeix perquè **només calgui teclejar una línia al portàtil**: a partir de l'SSH, tot es fa des de casa |
| 20/09/2026 | **SSH obert des de casa amb clau dedicada**, i maquinari real llegit per fi: Celeron **N5100 de 4 nuclis**, **4 GB**, **SSD NVMe Samsung de 128 GB**, Mint 22.3. Cau la reserva de l'eMMC |
| 20/09/2026 | **Docker CE instal·lat** i imatge d'HA **2026.9.3** baixada (3,43 GB) per la fibra de casa, per no gastar dades de la SIM |
| 20/09/2026 | **Home Assistant arrencat per primer cop.** Port 8123 obert al cap de ~30 s |
| 20/09/2026 | 🐛 **Error trobat a la primera arrencada:** `history_stats` estava escrit com a clau de primer nivell a `packages/rosada.yaml`. HA fusiona els paquets per domini, i això **feia caure el paquet sencer** —tota la lògica del punt de rosada— en silenci. Va sota `sensor:` amb `platform: history_stats`. Corregit |
| 20/09/2026 | `purge_interval` tret: obsolet a la 2026.9.3. `check_config` queda **net** |
| 20/09/2026 | **Tailscale connectat**, connexió directa entre els dos nodes i **expiració de clau desactivada**. L'accés al servidor ja no depèn de compartir xarxa |
| 21/09/2026 | **`matter-server` en marxa** com a segon contenidor, fixat per digest. `tplink` rebutja el hub H110 pel xifratge TPAP (`python-kasa#1590`), i Matter és la via local |
| 21/09/2026 | **RAM mesurada per SSH amb els dos contenidors actius:** HA 436 MB (pic 609), `matter-server` 88 MB (pic 89) — **19 %** dels 3.716 MB. Sense pressió (PSI `0.00`). La sorpresa: **Firefox 1.576 MB i l'escriptori Cinnamon 374 MB**, que no pinten res en un servidor. Queda obert passar a `multi-user.target` |
| 21/09/2026 | **Sostre de memòria posat als dos contenidors** (`mem_limit` 1.536 MB i 512 MB, `mem_reservation` 512 MB i 128 MB): corrien amb `mem_limit=0`, i una fuita s'hauria endut la màquina sencera. La suma dels sostres deixa **~1.660 MB** a l'amfitrió encara que tots dos toquin sostre alhora. `comprova.sh` ara verifica que hi siguin i que quadrin amb el compose |
| 21/09/2026 | **`vm.swappiness` baixat de 60 a 10** a `prepara-host.sh` (`/etc/sysctl.d/99-memoria.conf`). Es pot fer perquè el disc és un **NVMe** i no una eMMC. ⚠️ No buida el que ja hi ha a l'intercanvi: això demana un reinici |
| 21/09/2026 | 🐛 **Fals verd corregit a `comprova.sh`.** Mirava l'estat dels contenidors amb `docker compose ps … | head -1`: des que l'stack en té dos, en comprovava un i callava sobre l'altre. I com que `ps` **sense `-a` amaga els aturats**, si queia el primer el `head -1` agafava l'estat del segon i l'imprimia com si fos del primer — HA mort i el guió dient «Tot correcte». Ara va servei per servei amb `-a`, distingeix `Exited (137)` (mort per memòria) i es queixa si al compose hi ha un servei que no es comprova |
| 20/09/2026 | **Prova de reinici superada.** Després d'un reinici complet tornen sols `ssh`, `docker`, `tailscaled` i **Home Assistant** (HTTP 200 al cap de ~36 s), i Tailscale es reconnecta sense intervenció. Bluetooth desactivat, suspensió emmascarada, `unattended-upgrades` només seguretat amb Docker exclòs i passada a les 04:30. Això verifica la meitat de **programari** de l'arrencada desatesa; la de **maquinari** (BIOS, *AC power loss*) segueix oberta |
