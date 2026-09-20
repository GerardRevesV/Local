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
- [ ] Crear el compte d'HA i un testimoni de llarga durada.
- [ ] **Verificar `purge_keep_days: 730` contra la instància en calent** (Porta A).
- [ ] Emparellar el hub H100 al **router SIM** i després afegir la integració `tplink`.
- [ ] Decidir la ubicació física definitiva dins del local.

### On és cada cosa ara mateix

Tot el maquinari és **a casa**, no al local: s'hi està fent l'assaig general abans de
portar-ho. La idea és muntar-ho tot sobre el **router SIM** —el mateix que hi haurà al
local— perquè el que es provi aquí sigui exactament el que hi correrà: CGNAT, Tailscale,
reserves DHCP i el Wi-Fi del hub, tot igual.

> ⚠️ **Les descàrregues grosses es fan per la fibra de casa, no per la SIM.** La imatge d'HA
> sola són **3,43 GB**. Es va baixar abans de passar el portàtil al router SIM, i per això
> allà l'arrencada no gastarà dades.

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
[l'stack decidit](decisio-stack.md) és deliberadament petit: **un sol contenidor**, SQLite,
sense Postgres, sense Grafana i sense panell web.

| Recurs | El que hi ha | El que demana l'stack decidit | Veredicte |
|---|---|---|---|
| **CPU** | Celeron **N5100, 4 nuclis**, 6 W | 1 contenidor d'HA amb ~40 entitats + un script de Python de pocs minuts cada nit | ✅ **Sobra** |
| **RAM** | 4 GB (3,6 útils) | HA Container en repòs: 400–700 MB. Mint amb Xfce: ~700 MB | ✅ **Suficient** — *precisament perquè* no hi ha Postgres, ni InfluxDB, ni Grafana |
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
És un argument més a favor de l'stack d'un sol contenidor, no una limitació nova.

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
| **Hub Tapo H100** | ❌ Mor a l'instant → **deixen d'arribar lectures dels sensors** |
| **Router de la SIM** | ❌ Mor a l'instant → sense Tailscale, sense avís i sense pujada a GitHub |

Per tant, avui, el que la bateria compra **no** és continuïtat de dades: és que la màquina no
s'apagui de cop —cosa que protegeix la base de dades— i que segueixi viva quan torni el
corrent, sense ningú al local. Que hi hagi un **forat** a les sèries durant el tall és
inevitable sense un SAI petit per al router i el hub (~40–60 €). **Queda com a pendent.**

⚠️ I la lletra petita de la lletra petita: una bateria de liti **endollada al 100 % de manera
permanent durant dos anys** es degrada i es pot inflar. Convé buscar al BIOS un límit de
càrrega (vegeu sota).

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
sudo sed -i 's/^#*HandleLidSwitch=.*/HandleLidSwitch=ignore/' /etc/systemd/logind.conf
sudo systemctl restart systemd-logind
```

I desactivar la suspensió automàtica i l'apagada de pantalla per inactivitat des de la
configuració d'energia de Mint. **Un servidor que es suspèn és un servidor que no registra
res** — i, en aquest projecte, una sèrie de dades amb un forat.

## Decisió pendent: com instal·lar Home Assistant

Hi ha quatre maneres i **no són equivalents**. Com que la base és Linux Mint, això
condiciona:

| Mètode | Add-ons | Notes |
|---|---|---|
| **HA OS** (bare metal) | Sí | El sistema operatiu *és* Home Assistant. Es menja tot el disc: incompatible amb tenir Mint a sota. |
| **HA Supervised** | Sí | Oficialment només sobre **Debian** net. Linux Mint **no** és una base suportada. |
| **HA Container** (Docker) | **No** | Suportat i senzill sobre qualsevol Linux, Mint inclòs. Sense add-ons: cada servei extra (Mosquitto, Zigbee2MQTT, base de dades) es munta com a contenidor a part. |
| **HA Core** (venv de Python) | No | El més manual. Poc recomanable. |

**Camí recomanat amb Mint: HA Container sobre Docker.** Es perd la botiga d'add-ons, però
tot el que els add-ons donen es pot muntar com a contenidors amb `docker compose`, que a més
és més fàcil de versionar en aquest repositori.

> Si el que es vol és l'experiència completa amb add-ons, l'alternativa és instal·lar
> **Debian** al portàtil en comptes de Mint i fer-hi **HA Supervised**, o dedicar el portàtil
> sencer a **HA OS**. Val la pena decidir-ho *abans* d'instal·lar Mint.

⚠️ Aquesta taula s'ha de **verificar contra la documentació oficial actual** abans de
decidir res: els mètodes d'instal·lació de Home Assistant canvien.

## Coses a tenir resoltes abans de començar a codificar

- **On viu el servidor.** Si el que es vol monitoritzar és el local, el servidor (o com a
  mínim els sensors i un gateway) ha de ser **al local**, amb Internet i alimentació estable.
- **Alimentació.** El portàtil té bateria pròpia: fa de SAI improvisat davant talls de llum,
  i pot **registrar el tall**, cosa rellevant per demostrar que la ventilació estava operativa.
- **Arrencada automàtica.** El portàtil ha d'arrencar sol després d'un tall (BIOS: *restore
  on AC power loss*) i no suspendre's en tancar la tapa.
- **Accés remot.** Sense obrir ports a Internet. Opcions: VPN (WireGuard/Tailscale) o Nabu
  Casa. **Pendent de decidir.**
- **Còpies de seguretat.** Les dades històriques són el motiu del projecte; perdre-les és
  perdre'l. Còpia automàtica fora del portàtil.
- **Retenció de l'històric.** El `recorder` de Home Assistant purga per defecte al cap de
  **10 dies**. Per a l'ús d'aquest projecte cal **allargar-ho molt** (mesos o anys) i
  probablement moure la base de dades a PostgreSQL o afegir **InfluxDB**. És un dels primers
  ajustos que caldrà fer, no un detall posterior.

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
