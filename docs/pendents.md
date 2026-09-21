# Pendents

Llista única de coses obertes. **Actualitzar-la cada cop que entri informació nova.**

## Crític — amb data límit

- [ ] **Determinar l'origen de les humitats abans del ~9 de març de 2027** (venciment de la
      retenció de 3.000 €). → [humitats.md](local/humitats.md)
- [x] ~~Verificar l'estat del subministrament elèctric.~~ ✅ **Contractada Naturgy Tarifa
      Noche.** → [subministraments.md](local/subministraments.md)

## Privacitat del repositori

El repositori és **públic**. La documentació es va anonimitzar el 20/09/2026: adreça,
cadastre, registre, protocol notarial, noms de les parts i imports van a
`docs/privat/identificacio.md` (ignorat per git). Regla completa a
[`CLAUDE.md`](../CLAUDE.md).

- [x] ~~**Comprovar que `docs/privat/` no s'ha commitat mai.**~~ ✅ **Verificat el
      20/09/2026:** `git log --all -- docs/privat/` no retorna res, i la carpeta és al
      `.gitignore`. Cal **tornar-ho a comprovar** si algun dia es força un `git add -f`.
- [ ] Abans de pujar **fotos**, netejar-ne les **metadades EXIF de geolocalització** i
      revisar que no s'hi vegin rètols, plaques, números de portal ni documents.
- [ ] Repassar el `git diff` abans de cada commit buscant adreça, noms propis, referència
      cadastral i imports.
- [ ] Decidir si el compte i la URL de GitHub (que contenen el nom real) s'han de canviar,
      o si el repositori ha de passar a **privat**. L'anonimització del contingut protegeix
      la finca i els tercers, però no desvincula el repositori del seu propietari.

## Documentació del local

- [ ] Confirmar si la **derrama de la façana posterior** (18.639,06 €) es va aprovar i posar
      al cobrament abans del 09/09/2026 → aniria a càrrec del venedor.
- [ ] Obtenir l'**acta de la junta de veïns posterior a desembre de 2024** (junta vigent,
      pressupost definitiu de la façana, estat de les obres).
- [ ] Saber si la comunitat ha obtingut l'**ITE definitiva** i amb quina qualificació.
- [ ] Reclamar els **balanços de 2022, 2023 i 2024** de la comunitat.
- [ ] Obtenir els **estatuts de la comunitat** i el reglament de règim interior, si n'hi ha
      (es van demanar durant la negociació; verificar que no restringeixen l'ús del local).
- [ ] **Fotografiar el local** — la carpeta de fotos és buida i les humitats convé
      documentar-les amb imatges datades.

## Instal·lacions

- [ ] **Inventariar** els 2 sistemes de ventilació forçada i els splits: marca, model,
      ubicació, forma de control. → [inventari.md](domotica/inventari.md)
- [ ] Comprovar l'estat de l'**aigua**.
- [x] ~~**Contractar la SIM de dades.**~~ ✅ **Contractada i en servei** *(21/09/2026)*: tot
      l'estat penja ja del **router de la SIM** —el servidor per **cable** a `enp1s0`, i el
      hub, l'endoll i el mòbil per Wi-Fi—, o sigui que l'assaig general es fa sobre la xarxa
      definitiva i **els emparellaments d'ara ja són els bons**.
- [ ] **Saber el límit mensual de dades de la SIM** i apuntar operadora i pla. No es pot
      triar a cegues: surt de les 72 h de `vnstat` del pas 4 de la llista de sota, que
      **encara no s'han corregut**.

## Domòtica

### 🆕 Requisits definits el 21/09/2026 — [requisits.md](domotica/requisits.md)

Tres coses que el sistema ha de saber fer i que encara **no són decisions preses**. El
raonament sencer, amb el que desbloqueja cadascuna, és a
[requisits.md](domotica/requisits.md). Aquí només hi ha el que s'ha de fer.

- [ ] 🔴 **R2 — Provar si un llindar canviat sobreviu a un reinici d'HA.** Tres minuts al banc
      de casa: posar `input_number.delta_td_on` a 3,0, reiniciar el contenidor i mirar si hi
      segueix. La documentació d'HA diu que amb `initial:` **no** hi segueix, i els nou helpers
      de `rosada.yaml` en porten. Si es confirma, cada reinici esborra l'ajust de tot un
      hivern **sense dir res**.
- [ ] 🔴 **R2 — Garantir que els `input_number` es graven i s'exporten.** Mai a l'`exclude` del
      `recorder`, i sempre a la llista d'entitats de `nit.py`. Sense això, *«quin llindar
      regia el 3 de gener»* no té resposta.
- [ ] **R2 — Detectar paràmetres incoherents** (Δ_OFF ≥ Δ_ON) al sensor de decisió, amb pas a
      `bloquejat` i avís. Un `min:`/`max:` no ho pot impedir.
- [ ] 🔴 **R3 — Gravar la previsió des del primer dia de sèrie.** Des de 2024 les previsions
      ja no són atributs: cal un sensor per disparador que cridi `weather.get_forecasts` i
      deixi el Td previst a +3 h, +12 h i +24 h **com a estat**. El que no es gravi al
      novembre no es podrà reconstruir al gener.
- [ ] **R3 — Avançar el guió de gràfics** de la Fase D a la Fase B, i fer-hi la correlació
      creuada entre el Td del soterrani i el de l'exterior: és la resposta continuada a *per
      on entra l'aire*, i no costa cap maquinari.
- [ ] **R3 — Obrir `docs/domotica/diari-de-la-serie.md`** per anotar els esdeveniments
      externs. Un pic explicat val més que un pic esborrat.
- [ ] **R1 — Mesurar abans de filtrar:** cadència real de report dels Tapo per Matter, soroll
      base de cada sensor i pendent màxima creïble de T i HR. Són els tres números sense els
      quals el filtre s'estaria inventant.
- [ ] **R1 — Escriure el filtratge en paral·lel i sense decidir res**, amb comptador de
      mostres descartades i alerta per taxa de descart. ⚠️ La sèrie crua **no es toca mai**, i
      el filtre `range` d'HA queda **prohibit**: retalla al límit i converteix una lectura
      absurda en una de plausible.

### El portàtil que farà de servidor

Identificat el 20/09/2026: **Acer TravelMate B3 TMB311-32-C4JR**. Veredicte: **suficient**.
→ [home-assistant.md](domotica/home-assistant.md#el-maquinari-del-servidor)

- [x] ~~**Confirmar CPU, RAM i tipus de disc.**~~ ✅ **20/09/2026, llegit per SSH:** Celeron
      **N5100 de 4 nuclis**, **4 GB** soldats (3,6 útils), **SSD NVMe Samsung de 128 GB**,
      Linux Mint 22.3.
- [x] ~~⚠️ Si el disc és eMMC: res de fitxer d'intercanvi, `zram`…~~ ✅ **No aplica: és un
      NVMe.** Cau la reserva principal del veredicte del maquinari, i el disc és substituïble.
- [x] ~~Activar **`F12 Boot Menu`** al BIOS per poder arrencar del pen drive.~~ ✅ **Resolt el
      20/09/2026.** Era això: ve desactivat de fàbrica. Mint arrenca.
- [x] ~~Desactivar la **suspensió** i posar `HandleLidSwitch=ignore`.~~ ✅ Fet i **verificat
      després d'un reinici real**: `sleep`/`suspend`/`hibernate` emmascarats, la tapa ignorada,
      i HA torna sol amb HTTP 200. Queda oberta la meitat de maquinari (BIOS).
- [ ] ⚠️ **Decidir un SAI petit (~40–60 €) per al router i el hub H110.** La bateria del
      portàtil només manté viu el portàtil: en un tall, els sensors deixen d'arribar igualment
      i la sèrie de dades fa un forat.
- [ ] **Col·locar-lo a la planta baixa, no al soterrani** (humitat sobre l'electrònica), en un
      lloc airejat i, si es pot, amb **cable Ethernet**.
- [ ] 🆕 **Aplicar la llista negra del Bluetooth al servidor, i reiniciar — DESPRÉS del
      calibratge.** El pas 6 de `prepara-host.sh` escriu `/etc/modprobe.d/99-sense-bluetooth.conf`,
      però s'hi va afegir el 20/09 a les 22:02, **després** de l'última vegada que el guió es va
      córrer sencer (el `swappiness` del 21/09 es va aplicar a mà), i al servidor **no hi és**.
      L'error que omplia el log ja està aturat des del 21/09/2026 desactivant l'entrada d'HA,
      o sigui que no corre pressa: és la capa que treu l'adaptador del tot. Tornar a córrer el
      guió (és idempotent, demana `sudo`), reiniciar quan el calibratge hagi acabat i
      comprovar que `ls /sys/class/bluetooth` surt buit →
      [runbook](domotica/runbook-servidor.md#-el-bluetooth-omple-el-log)

#### 🔧 Tanda física — mentre el portàtil encara sigui a casa

**Una sola tanda**, amb la màquina apagada i el teclat al davant. Un cop sigui al local,
**cada casella d'aquestes és un viatge**. Com s'entra al BIOS:
[home-assistant.md](domotica/home-assistant.md#entrar-al-bios).

- [ ] ⚠️ **BIOS — *restore on AC power loss*: comprovar si l'opció hi és.**
      `decisio-stack.md` ho dona per fet i **en portàtils sovint no hi és**. Si no hi és,
      decidir la mitigació en aquell moment: apagada ordenada al 20 % de bateria, o
      `Wake on LAN`. És l'única casella d'aquesta llista que pot canviar una decisió
      d'arquitectura.
- [ ] **BIOS — límit de càrrega de bateria**, si existeix: dos hiverns al 100 % la degraden
      i la poden inflar.
- [ ] **BIOS — disc intern a dalt** de l'ordre d'arrencada, perquè un llapis oblidat al local
      no deixi el servidor sense arrencar.
- [ ] **Salut del maquinari** (tasca 0.5 de [fases.md](domotica/fases.md)): SMART del disc,
      capacitat real de la bateria i **prova de la pila del CMOS** — apagada llarga i, en
      tornar, mirar `hwclock -r` **abans** que l'NTP ho dissimuli.
- [ ] Confirmar **visualment el port RJ-45** i que dona enllaç: la fitxa el dona per bo, però
      no s'ha vist mai amb un cable posat, i el servidor no hauria de dependre del Wi-Fi.

### ⏭️ El pas a la SIM — el següent moviment

Decidit el 20/09/2026: **es fa aviat, no s'ajorna.** Fins que HA i el hub H110 no comparteixin
xarxa no es grava ni una lectura, i el rellotge dels 28 dies de la Fase B no ha començat.
Llista completa i ordre a
[home-assistant.md](domotica/home-assistant.md#el-pas-a-la-sim--lassaig-general-de-debò).

**Per fibra, abans de desendollar:**

- [ ] `apt full-upgrade` + instal·lar **`vnstat`**, `smartmontools`, `rsync`, `gnupg`, `jq`,
      `sqlite3`. Sense `vnstat` no hi ha manera de saber què gasta la SIM.
- [ ] Confirmar que la imatge d'HA **ja és al disc** (`docker image ls`).

**Amb el portàtil al davant:** la [🔧 tanda física](#-tanda-física--mentre-el-portàtil-encara-sigui-a-casa)
de més amunt — BIOS, SMART, bateria, CMOS i RJ-45. **Es fa abans de moure la màquina.**

**Un cop a la SIM:** reserva DHCP → `tailscale ping` (mirar si va **directe o per DERP**) →
72 h de `vnstat` → emparellar el hub → **i només llavors** afegir-lo a HA **per Matter**
(no per `tplink`: el rebutja pel xifratge TPAP).

### Muntatge

- [x] ~~Acabar d'instal·lar **Linux Mint** al portàtil secundari.~~ ✅ **Mint 22.3 instal·lat**
      el 20/09/2026.
- [x] ~~**Decidir el mètode d'instal·lació** de Home Assistant.~~ ✅ **HA Container sobre
      Docker**, ja en marxa amb la versió **2026.9.3** fixada.
      → [home-assistant.md](domotica/home-assistant.md)
- [ ] Decidir **on viu físicament el servidor** dins del local (planta baixa, aixecat de
      terra i ventilat). L'**accés remot ja està resolt**: Tailscale.
- [x] ~~Configurar la **retenció llarga de l'històric**.~~ ✅ **Feta:** `purge_keep_days: 730`
      i `commit_interval: 30` sobre **SQLite**, a `config/configuration.yaml`. Queda la
      verificació **en calent** (casella de sota) i les **còpies de seguretat**, que estan
      decidides però pendents d'escriure `nit.py`.
- [ ] Confirmar si la **càmera Tapo C200** que es va investigar era per al local.
- [x] ~~**Decidir on viu la lògica de control** del punt de rosada.~~ ✅ **HA natiu**, i ja
      **escrita**: `config/packages/rosada.yaml` (665 línies), amb un únic punt d'avaluació,
      `sensor.decisio_del_soterrani`. Node-RED, AppDaemon, pyscript i el servei propi en
      Python queden **descartats**. → [decisio-stack.md](domotica/decisio-stack.md)
- [x] ~~**Decidir la base de dades i l'eina de visualització.**~~ ✅ **SQLite** i els
      **dashboards natius d'HA** per Tailscale. **PostgreSQL, MariaDB, InfluxDB i Grafana
      estan descartats**, no ajornats: el dipòsit de la prova és el CSV diari immutable a
      git, i un segon motor només compraria un mode de fallada silenciós més.
      *(⚠️ 21/09/2026: **el CSV diari ha caigut** amb el canvi d'objectiu, i per tant la base
      de dades passa a ser l'única còpia de l'històric. El descart dels motors no s'ha
      revisat; el motiu que s'hi donava, sí que ha desaparegut.)*
      → [decisio-stack.md](domotica/decisio-stack.md)
- [ ] ⚠️ **Verificar `purge_keep_days: 730` contra la instància EN CALENT**, no contra el
      fitxer. Ja és a `configuration.yaml` i `check_config --info recorder` el llegeix, però
      això encara és el fitxer: falta `/api/config` amb el testimoni. És l'única línia del
      projecte que **no té arreglada a posteriori**.
- [ ] ⚠️ **Convertir l'estat dels ventiladors en sensors numèrics** (`history_stats` +
      `utility_meter`). Els binaris no generen estadístiques a llarg termini, i per tant la
      prova que la ventilació estava operativa **s'esborra** amb la purga. *Estat: el
      mecanisme ja funciona per al deshumidificador a `rosada.yaml`; els blocs dels
      ventiladors hi són escrits però **comentats a posta** fins a la Fase C, perquè fins que
      els S110E no estiguin instal·lats quedarien `unavailable` i embrutarien l'històric.*
- [ ] 🔬 **Fer el calibratge creuat dels cinc sensors** (fase A.13). 🟡 **Primera tanda feta
      el 21/09/2026**, franja 49–59 %: dispersió de Td **0,95 → 0,24 °C**, temperatura sense
      correcció, i desplaçaments d'HR entre −1,2 i +2,2 punts. **No aplicats**: falta la franja
      humida. Següent pas, una **caixa tancada amb sal de cuina** (75,3 % d'HR, absolut i amb
      pujada lenta) → [calibratge.md](domotica/calibratge.md#segona-tanda-proposada--la-franja-humida).
      ⚠️ **I encendre el marcador aquesta vegada**: la primera tanda es va fer sense.
      *Preparat des del 21/09/2026:* hi ha el marcador `input_boolean.mode_calibratge` —que posa
      la decisió a `calibratge` i impedeix que cap automatisme actuï—, el forat dels
      desplaçaments a les cinc plantilles de `rosada.yaml` (avui identitat, no corregeixen
      res) i `tools/calibratge.py` per ajustar-ho. ⚠️ **Són rampes lentes en els dos sentits,
      no 24 h quiets**: amb l'HR en enters, un replà mort no deixa baixar de ±0,5 %, i amb una
      sola rampa el retard del hub no es distingeix del calibratge.
      → [calibratge.md](domotica/calibratge.md)
- [ ] 🔋 **Les bateries dels cinc Tapo no arriben a Home Assistant.** Comprovat el
      21/09/2026: l'HA no té cap entitat de bateria dels sensors —pel que sembla, el hub H110
      no les passa per Matter—, tot i que el conveni de noms en preveu la magnitud `bateria`.
      Avui l'**únic símptoma** d'una bateria que es mor és que el sensor passi a
      `unavailable`, i per a llavors ja hi ha un forat a la sèrie. De moment es miren a l'app
      de Tapo. Cal valorar un avís quan un sensor porti massa hores sense reportar, que és
      l'únic senyal que sí que tenim.
- [ ] 🔁 **Repetir el calibratge al soterrani a l'hivern.** El primer es farà a casa a 22–28 °C
      i el soterrani al gener serà de 8 a 15 °C. Els números porten el **rang de validesa**
      escrit al costat precisament per poder-los comparar quan hi hagi els dos.
- [x] ~~Fixar els **noms d'entitat definitius** abans de posar cap sensor en producció.~~ ✅
      **Aplicats als sis sensors del hub** (verificat al registre d'entitats el 21/09/2026:
      `soterrani_fons`, `soterrani_centre`, `soterrani_gran`, `baixa`, `exterior` i
      `soterrani_inundacio`). ⏳ **Queden els de l'endoll** —`switch.deshumidificador` i els
      seus dos sensors—, que es posen **just després d'emparellar-lo** i abans que gravi res.
      → [noms-entitats.md](domotica/noms-entitats.md)
- [x] ~~Muntar el **ritual mensual** d'exportació CSV + SHA-256 fora del local.~~ ✅
      **Descartat i substituït:** el fa el **commit nocturn**, cada dia i amb segell RFC 3161,
      no un cop al mes i a mà. → [decisio-stack.md](domotica/decisio-stack.md)
      *(⚠️ 21/09/2026: el commit nocturn a `Local-data` i el segell també han caigut, amb el
      canvi d'objectiu.)*
- [ ] Valorar un **sensor de temperatura superficial de paret** (DS18B20 via ESPHome) a cada
      punt humit: és l'únic que discrimina directament condensació de capil·laritat.
- [x] ~~**Decidir el mètode d'accés remot.**~~ ✅ **Tailscale, instal·lat i connectat** el
      20/09/2026, amb l'**expiració de clau desactivada**. Connexió directa entre nodes.
      → [acces-remot.md](domotica/acces-remot.md)
- [x] ~~Decidir si cal SSH.~~ ✅ **Sí: Tailscale.** El flux és casa → GitHub → portàtil del
      local, i desplegar necessita shell. → [desplegament.md](domotica/desplegament.md)
- [x] ~~Crear un **repositori separat i privat només per a les dades** (`Local-data`), amb una
      **clau de desplegament SSH** amb permís d'escriptura.~~ ✅ **Sense objecte** des del
      21/09/2026: el canvi d'objectiu deixa les còpies «sense repositori a part» →
      [decisio-stack.md](domotica/decisio-stack.md). *(La lliçó de fons segueix valent per a
      qualsevol pujada automàtica que es munti: **clau de desplegament, mai un token**, perquè
      un token caduca i atura la pujada en silenci.)*
- [x] ~~**Decidir si les dades del panell web seran privades o públiques.**~~ ✅ **La
      pregunta desapareix: no hi haurà panell web.** Dashboards natius d'HA i app Companion
      per Tailscale. *(⚠️ 21/09/2026: el **panell es reobre**
      —[decisio-stack.md](domotica/decisio-stack.md)—, però **la pregunta segueix resolta**:
      el serviria **HA mateix** des de `config/www/`, darrere de Tailscale, i per tant les
      dades continuen sense sortir a cap pàgina pública.)* Amb això les dades no surten mai a cap pàgina, i el dilema del token
      dins d'una web s'evapora. **Cloudflare R2 + domini propi + Cloudflare Access queden
      descartats**: incompleixen «gratuït» (~12 €/any) i fiquen un tercer que desxifra TLS
      sobre dades amb valor legal. **GitHub Pages** també: privat és de pagament i públic
      seria publicar els patrons d'ocupació.
- [x] ~~**Decidir la via de l'arxiu de dades:** GitHub Releases o R2/B2.~~ ✅ **Cap de les
      dues:** un commit diari al repositori privat `Local-data`, amb SHA-256 i **segell
      RFC 3161**, més còpia a disc USB al local. GitHub Releases resolia un problema que no
      tenim —tot l'arxiu són ~20–30 MB. *(⚠️ **Superat el 21/09/2026:** cauen el repositori,
      el SHA-256 diari i el segell; es queda la còpia a disc USB al local.)*
- [x] ~~Fixar l'**estructura de fitxers del panell**.~~ ✅ **Sense objecte**: es referia al
      panell estàtic a GitHub Pages que llegia l'arxiu, i aquell arxiu ja no existeix.
      *(⚠️ 21/09/2026: el panell **es reobre**, però servit per HA i llegint l'històric
      directament; no li cal cap estructura de fitxers. I **el CSV diari també ha caigut**.)*
      El que **sí** es manté és el requisit de fons: les marques de temps de qualsevol
      exportació van en **ISO 8601 amb zona horària** i, si porten epoch, totes dues.
- [x] ~~⚠️ **Comprovar si els 4 GB de RAM aguanten el segon contenidor de Matter.**~~ ✅
      **Mesurat el 21/09/2026:** sí, i de llarg. HA 436 MB (pic 609) + `matter-server` 88 MB
      (pic 89) = **19 %** de 3.716 MB, sense pressió de memòria. *(Tornar-ho a mirar després
      d'emparellar el hub: s'ha mesurat amb la xarxa Matter buida.)*
- [x] ~~⚠️ **Posar sostre de memòria als contenidors.**~~ ✅ **21/09/2026:** corrien tots dos
      amb `mem_limit=0`, o sigui que una fuita s'enduia l'amfitrió i, amb ell, l'històric.
      Posats `mem_limit` **1.536 MB** (HA) i **512 MB** (`matter-server`) amb `mem_reservation`
      de 512 i 128. Sumen 2.048 dels 3.716: encara que tots dos toquin sostre alhora, a
      l'amfitrió li queden **~1.660 MB**. `comprova.sh` ho verifica.
      → [home-assistant.md](domotica/home-assistant.md#-el-sostre-de-memòria--perquè-una-fuita-no-sendugui-la-màquina)
- [x] ~~**Decidir `vm.swappiness`.**~~ ✅ **21/09/2026: baixat de 60 a 10**, aplicat per
      `prepara-host.sh` a `/etc/sysctl.d/99-memoria.conf`. Es pot perquè el disc és NVMe.
- [x] ~~🐛 **`comprova.sh` donava un fals verd sobre els contenidors.**~~ ✅ **21/09/2026:**
      mirava `docker compose ps … | head -1`, o sigui **un** contenidor d'un stack que en té
      **dos**. I com que `ps` sense `-a` amaga els aturats, si queia el primer agafava l'estat
      del segon i l'imprimia com si fos del primer: HA mort i «Tot correcte» a la pantalla.
      Ara va servei per servei amb `-a`, distingeix `Exited (137)` i canta si al compose hi ha
      un servei que ningú no comprova.
      → [runbook-servidor.md](domotica/runbook-servidor.md#-docker-compose-ps-amaga-els-contenidors-aturats)
- [x] ~~🔁 **Desplegar els sostres al local i comprovar-los.**~~ ✅ **Desplegat el
      21/09/2026.** El servidor anava 15 commits enrere. `check_config` net, `docker compose
      up -d` (recrear és l'únic que aplica `mem_limit`), i **HA responent al cap de 15 s**.
      Sostres verificats a la màquina: HA **1.536 MB** (en consumeix 432) i `matter-server`
      **512 MB** (87). `comprova.sh` **tot verd**, i per fi corregut contra la màquina de
      debò, no contra escenaris simulats.
- [ ] 🔁 **Reiniciar la màquina per buidar l'intercanvi.** ✅ El `vm.swappiness=10` **ja està
      aplicat** (`/etc/sysctl.d/99-memoria.conf`, 21/09/2026) i `comprova.sh` el veu. Però és
      la política d'ara endavant: **queden 442 MB al swap** que no es mouran sols. Sense
      pressa —el PSI marca `0.00`— i es pot ajuntar amb el pas a `multi-user.target`.
- [ ] 📝 **Que un OOM deixi rastre permanent.** ⚠️ **No al `desplegaments.log`:** aquell fitxer
      l'escriu `desplega.sh` i només quan despleguem; un OOM a les 04:00 no hi cauria mai. Va
      al **guió nocturn `nit.py`** (que corre cada dia) i, com a avís, al **cos del ping de
      `bategada`**. Cap dels dos guions no existeix encara — quan s'escriguin, han de portar-hi
      el recompte d'OOM del kernel i els reinicis dels dos contenidors. *(Des del canvi
      d'objectiu del 21/09/2026, `nit.py` ja no escriu a `Local-data`: va amb la còpia al
      disc USB del local.)*
- [ ] 🔁 **Revisar els sostres després d'emparellar el hub.** Els 512 MB del `matter-server`
      es van triar sobre un pic mesurat amb la **xarxa Matter buida**. El marge és de 5,7× i
      hauria de sobrar, però és una xifra per confirmar, no per donar per bona.
- [ ] 🖥️ **Passar el servidor a `multi-user.target`** (sense entorn gràfic). S'administra per
      SSH i Tailscale, i l'escriptori Cinnamon costa **374 MB** que no fan res. De pas
      s'acaba el risc que hi quedi un navegador obert: el 21/09 hi havia **Firefox amb
      1.576 MB**, el 42 % de la màquina.
- [ ] 🔴 **`matter-data/` ha d'entrar a la còpia de seguretat.** Hi viuen les **claus** dels
      aparells emparellats per Matter. És al `.gitignore` perquè són secrets, i per això és
      fàcil oblidar-la justament a la còpia: perdre-la obliga a **reemparellar**, i
      reemparellar **parteix totes les sèries**. Va al mateix sac que `config/.storage` —al
      `nit.py` i al tarball xifrat setmanal.
- [ ] 📦 **Decidir on va el tarball xifrat setmanal** (`.storage`, `secrets.yaml`,
      `matter-data/`, ~1 MB). Anava a `Local-data`, que el canvi d'objectiu del 21/09/2026
      deixa sense objecte. **L'exigència de treure'l del local es manté**, perquè el seu motiu
      no era probatori: és el de just a sobre. L'històric, en canvi, es queda només al disc
      USB. → [decisio-stack.md](domotica/decisio-stack.md)
- [x] ~~**Emparellar el hub H110 per Matter** i comprovar que apareixen els sis sensors.~~ ✅
      **Fet.** Verificat al registre d'HA el **21/09/2026**: el hub hi és com a **node 1** amb
      subscripció activa, i hi pengen els **sis** aparells —tres T315, dos T310 i el T300
      d'inundació—, **amb els noms del conveni ja aplicats**
      (`sensor.soterrani_fons_temperatura`, `binary_sensor.soterrani_inundacio`…).
      Microprogramari: hub **1.3.1**, T315 **1.12.0**, T310 **1.6.0**, T300 **1.9.0**.
      ⚠️ Va **per Matter**, no per `tplink`, que el rebutja pel xifratge TPAP
      ([`python-kasa#1590`](https://github.com/python-kasa/python-kasa/issues/1590)).
- [x] ~~🆕 ❓ **Confirmar si l'endoll és un `P110M` o un `P110`.**~~ ✅ **És un P110M**
      *(21/09/2026)*: s'anuncia a la xarxa com a dispositiu **Matter** (`DN=Smart Wi-Fi Plug`,
      `DT=266`, fabricant TP-Link). Els documents deien «P110» **i** font Matter, que no podia
      ser; ara el model quadra amb la via.
- [x] ~~🆕 🔴 **Microprogramari de l'endoll a ≥ 1.3.0 ABANS d'emparellar-lo.**~~ ✅ **1.4.3**,
      llegida a l'app de Tapo el 21/09/2026 — per damunt de l'1.3.0 que cal perquè el consum
      surti per Matter, i **feta abans d'emparellar**, que és l'ordre que estalvia haver de
      reemparellar.
- [x] ~~🆕 🔴 **L'emparellament de l'endoll falla.**~~ ✅ **Resolt el 21/09/2026 a les 03:45.**
      Cinc intents morien amb `PASESession timed out` —l'aparell no contestava— amb la xarxa
      ja descartada (s'anunciava amb `CM=2` i responia als pings). La causa que hi encaixava:
      l'amfitrió té **quatre interfícies amb adreça `fe80::`** i l'endoll s'anuncia amb una
      d'enllaç local, o sigui que el servidor sortia per on no tocava. Amb
      `--primary-interface enp1s0` desplegat (03:34), **va entrar a la primera** com a node 9.
      ⚠️ No és una prova controlada —també es va desendollar l'endoll—, però era l'única cosa
      canviada al servidor.
      → [emparellar-matter.md](domotica/emparellar-matter.md#-com-va-acabar-21092026-0345)
- [x] ~~🆕 **Un cop emparellat, veure si surt l'energia.**~~ ✅ **Surt** *(21/09/2026)*. El
      P110M publica per Matter `switch.deshumidificador`, `sensor.deshumidificador_potencia`
      (W) i `sensor.deshumidificador_energia` (kWh), més tensió i corrent. Renombrades al
      conveni el mateix dia i, després del reinici, el `utility_meter` i el `history_stats`
      de `rosada.yaml` s'hi han enganxat: els comptadors diari i mensual ja no diuen
      `unknown`. **Els kWh/dia de la Porta B tenen font**, en local i sense compte de Tapo.
- [ ] 🆕 ⚠️ **Verificar si l'energia acumulada depèn d'Internet.** Es reporta que potència,
      tensió i corrent van en local però que els **kWh** necessiten que l'endoll sincronitzi
      l'hora pel núvol. Prova a casa: una hora sense sortida a Internet i mirar les dues
      entitats. Importa perquè la SIM del local caurà algun dia.
- [ ] 🆕 ❓ **Decidir què es fa amb tensió i corrent de l'endoll:** a l'`exclude.entities` del
      `recorder` (mai per glob) o acceptades. **Mesurat el 21/09/2026 amb un portàtil endollat:
      ~150 files/hora cadascuna**, o sigui unes 3.600 al dia i, a 730 dies de retenció,
      **milions de files per no res**. No és urgent —el disc té 99 GB lliures— però és una
      decisió que val més prendre **abans** que comenci la sèrie, no després.
- [x] ~~Registrar el **període tarifari com a entitat** a HA per calcular el cost real.~~ ✅
      **Escrit el 21/09/2026:** `packages/consum.yaml` + `custom_templates/tarifa.jinja` donen
      el tram i el preu d'ara, i el **cost en euros** i els **kWh per tram** acumulats, amb una
      mostra del comptador de l'endoll cada 5 minuts. Al tauler, vista *Consum* i watts a
      *Històric*. El calendari de festius, verificat hora per hora de 2026 a 2036.
      → [subministraments.md](local/subministraments.md#el-cost-a-home-assistant)
- [x] ~~🆕 **Desplegar el consum.**~~ ✅ **Desplegat el 21/09/2026 a les 17:10** sense reiniciar
      HA, i verificat: `check_config` net, el tram i el preu d'ara correctes, **48.216 instants de
      2026 a 2036 sense cap discrepància** amb el calendari ja importat des del fitxer
      (`tools/tarifa.py --prova-ha`) i `comprova.sh` tot verd.
- [ ] 🆕 **Desplegar la mostra cada 5 minuts i veure'n les dues primeres.** La primera només
      posa la referència (o continua la que ja hi hagi); **la següent en què el comptador s'hagi
      mogut ja ha de donar euros**. També es recarrega sense reiniciar.
- [ ] 🆕 **Contrastar el cost amb la primera factura real:** els tres preus, l'impost
      elèctric (5,11269632 %) i l'IVA (21 %), i que les **hores de cada tram** que dona la
      factura quadrin amb el calendari. *(Que l'IVA és cost ja no és dubte: confirmat el
      21/09/2026, sempre es paga i no es dedueix.)*
      ⚠️ Lligat amb el de més amunt: si els kWh de l'endoll depenen d'Internet, el cost també
      —no se'n perd res, però mentre la SIM estigui caiguda quedarà quiet i en tornar
      repartirà el forat com a consum uniforme.
- [x] ~~**Congelar també el `matter-server`** fins al 10/03/2027.~~ ✅ **Sense objecte** des del
      21/09/2026: la congelació de versions va caure amb el canvi d'objectiu. El que **es
      manté** és que va **fixat per digest** i no per etiqueta, perquè la imatge no publica
      versions i `stable` es mou sota els peus; s'actualitza només a posta.
- [ ] Escriure el **script de desplegament** amb validació de configuració abans del reinici.
- [x] ~~**Fixar les versions** al `docker-compose.yml` — res de `:latest`.~~ ✅ **2026.9.3**,
      fixada. *(Deia també «congelada fins al 10/03/2027»: la congelació va caure el
      21/09/2026; la versió fixada es manté i s'actualitza només a posta.)*
- [x] ~~Definir els **helpers i automatismes en YAML**, no per interfície.~~ ✅ **Fets**, tots
      a `config/packages/rosada.yaml`: `input_number`, `input_select`, `timer` i els
      automatismes sota `automation:` amb la clau **`manual`**, que és el que impedeix que
      l'editor visual reescrigui el fitxer i bloquegi els desplegaments futurs.
- [ ] Muntar un **avís de caiguda** (Healthchecks.io / UptimeRobot). Sense això l'accés
      remot no serveix de res. *(Hi deia també «i una còpia de l'històric fora del local»:
      decidit el 21/09/2026 que **no** —l'històric es queda al disc USB del local—. El que sí
      surt del local és el tarball xifrat dels secrets; vegeu el pendent del seu destí.)*
- [ ] Valorar un **endoll intel·ligent de rearmada** per al portàtil i el router,
      independent de Home Assistant.
- [ ] ⏸️ **Ajornat el 21/09/2026**, amb la via documental —«amb la porta oberta»,
      [decisio-stack.md](domotica/decisio-stack.md)—. No és sense objecte: si es reprèn, és
      el primer que caldrà. **Consultar amb un professional el valor probatori** d'un
      històric autogenerat: pot caldre exportació segellada temporalment o un enregistrador
      independent. Això condiciona tota l'estratègia de les humitats.
- [x] ~~Verificar si hi ha IP pública o CGNAT.~~ Internet per **SIM** → CGNAT quasi segur:
      port forwarding i WireGuard directe queden descartats.
- [x] ~~**Decidir el protocol dels sensors** (Zigbee + coordinador SLZB-06).~~ ✅ **Superat
      pel maquinari real:** els sensors **ja estan comprats i actius**. Són **Tapo T310/T315
      amb hub H110** per **868 MHz sub-GHz**, que penetra el formigó millor que el Zigbee de
      2,4 GHz. ⚠️ **La via cap al hub és Matter, no `tplink`** (el rebutja pel xifratge TPAP).
      → [inventari.md](domotica/inventari.md)
- [x] ~~**Prova de cobertura de ràdio** al soterrani, 48 h.~~ ✅ **Sense objecte:** no hi ha
      Zigbee i els sensors ja donen lectures des del soterrani. Queda només confirmar **on és
      cada sensor** i que el de fora està protegit de la pluja.
- [ ] **Definir exactament quines dades es registren** (l'usuari ho ha ajornat conscientment).
- [x] ~~Inventariar el **deshumidificador**.~~ ✅ **Fet:** **Qlima D 825 PA Smart**, 470 W,
      25 L/dia, bomba de condensats i higròstat propi 40–80 %. El manual oficial n'ha resolt
      el rang (5–35 °C), el desgebratge automàtic i la protecció de compressor de 5 min, que
      **ja és a l'aparell**. → [inventari.md](domotica/inventari.md)
- [ ] 🆕 ▶️ **Provar `tuya-local` amb el deshumidificador** *(obert el 21/09/2026; en marxa el
      mateix vespre)*. ✅ **Endollat al P110M** a les 18:15 i ✅ **ja és a la Wi-Fi del router
      SIM** —s'anuncia a la xarxa local—, o sigui que el pas 1 no demana reemparellar.
      ✅ Instal·lació **sense HACS**, amb la versió **2026.9.1 fixada per suma**
      (`scripts/instala-tuya-local.sh`). ⏳ Queden: reiniciar HA, la configuració assistida
      (**tu**, amb el codi d'usuari i el QR de l'app Smart Life), veure quina configuració
      proposa i **renombrar al conveni** abans que gravi res. ✅ **Reserva DHCP feta** al
      router SIM (`192.168.1.104`, confirmat per l'usuari el 21/09/2026).
      *Com estava escrit el matí:* Ja
      no cal compte de desenvolupador de Tuya: la *local key* s'extreu un cop amb l'app Smart
      Life. El D825 no és a la llista, però pot encaixar amb la configuració del D820A. Donaria
      el **llindar d'HR des d'HA** i l'estat (**P1** desgebrant, P2, HR pròpia). ⚠️ Emparellar-lo
      **a la Wi-Fi del router SIM**: cada reemparellament canvia la clau. El **P110 es queda**.
      *(Tasca B.1c de [fases.md](domotica/fases.md).)* → [inventari.md](domotica/inventari.md#decisió-no-integrem-el-deshumidificador-per-tuya--es-reobre-provar-tuya-local)
- [ ] 🆕 **Mirar els cicles del compressor quan el deshumidificador sigui al soterrani.** El
      21/09/2026 a casa feia **~2 min de compressor i 5–6 min aturat** (el ventilador segueix a
      ~15 W): els 5 min d'aturada són la protecció que porta l'aparell; els 2 min en marxa, el
      seu higròstat tocant el llindar en una habitació ja seca. El disseny demana tandes de
      **20–30 min** ([control-punt-rosada.md](domotica/control-punt-rosada.md)). Al soterrani,
      amb molta més humitat, probablement no passarà; si passa, és un argument per governar-lo
      per `tuya-local` amb histèresi pròpia.

## Verificacions físiques al local (abans de gastar diners)

- [x] ~~⚠️ **El deshumidificador arrenca sol després d'un tall de corrent?**~~ ✅ **Sí.** El
      control per endoll intel·ligent és viable i queda confirmada l'arquitectura (a):
      l'higròstat propi regula, i el **Tapo P110** el governa i en mesura el consum.
- [ ] 🔴 **Però: recorda el llindar d'humitat** després d'un cicle d'alimentació? Desendollar
      i tornar a endollar amb l'higròstat al 45 %. Si torna a fàbrica, l'arquitectura del
      deshumidificador canvia. *(Tasca 0.2b de [fases.md](domotica/fases.md).)* La sortida,
      en aquest cas, seria `tuya-local` (vegeu la prova de més amunt).
- [ ] ⚠️ **Per on entra l'aire de reposició** quan els extractors funcionen? (Prova de fum.)
      Si entra per fissures en contacte amb el terreny, **el ventilador pot estar empitjorant
      les humitats** i el projecte canvia de naturalesa.
- [ ] Els ventiladors estan **endollats o cablejats**? Hi ha interruptor de paret?
- [x] ~~Placa del deshumidificador: potència, L/dia, temperatura mínima, desguàs per tub.~~
      ✅ **Resolt pel manual oficial:** 470 W, 25 L/dia, 5–35 °C i **bomba de condensats** amb
      4 m d'altura de bombeig. ⚠️ El desguàs continu és **obligatori**: el dipòsit s'omple en
      ~4 h. → [inventari.md](domotica/inventari.md)
- [ ] Quina és la **paret més freda i humida** (termòmetre IR de mà) → allà va el sensor de
      temperatura superficial.
- [ ] Rang de temperatura del soterrani a l'hivern (per sota de 15 °C un deshumidificador per
      compressor rendeix malament).
- [ ] Horaris de soroll admissibles per als veïns.
