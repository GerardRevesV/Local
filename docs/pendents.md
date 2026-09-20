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

- [ ] **Comprovar que `docs/privat/` no s'ha commitat mai**: `git log --all -- docs/privat/`
      ha de ser buit.
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
- [ ] **Contractar la SIM de dades:** operadora, pla i límit mensual; model de router (cal
      Ethernet per al coordinador Zigbee) i cobertura al local.

## Domòtica

### El portàtil que farà de servidor

Identificat el 20/09/2026: **Acer TravelMate B3 TMB311-32-C4JR**. Veredicte: **suficient**.
→ [home-assistant.md](domotica/home-assistant.md#el-maquinari-del-servidor)

- [ ] **Confirmar CPU, RAM i tipus de disc** a la pestanya *Information* del BIOS, o amb
      `lscpu` / `free -h` / `lsblk -d -o NAME,SIZE,MODEL,TRAN` un cop hi hagi Mint.
- [ ] ⚠️ **Si el disc és eMMC** (`mmcblk0`): **res de fitxer d'intercanvi** — `zram` i
      `vm.swappiness` baix. Si són només 64 GB, vigilar l'espai des del primer dia.
- [ ] ⚠️ **Verificar al BIOS si existeix *restore on AC power loss*.** `decisio-stack.md` ho
      dona per fet, i **en portàtils sovint no hi és**. Si no hi és, decidir la mitigació
      (apagada ordenada al 20 % de bateria, o `Wake on LAN`).
- [x] ~~Activar **`F12 Boot Menu`** al BIOS per poder arrencar del pen drive.~~ ✅ **Resolt el
      20/09/2026.** Era això: ve desactivat de fàbrica. Mint arrenca.
- [ ] Un cop Mint estigui instal·lat, **tornar a posar el disc intern a dalt** de l'ordre
      d'arrencada, perquè un llapis oblidat al local no deixi el servidor sense arrencar.
- [ ] Buscar al BIOS un **límit de càrrega de bateria**: dos anys al 100 % la degraden i la
      poden inflar.
- [ ] Desactivar la **suspensió** i posar `HandleLidSwitch=ignore` abans de deixar-lo tancat.
- [ ] ⚠️ **Decidir un SAI petit (~40–60 €) per al router i el hub H100.** La bateria del
      portàtil només manté viu el portàtil: en un tall, els sensors deixen d'arribar igualment
      i la sèrie de dades fa un forat.
- [ ] **Col·locar-lo a la planta baixa, no al soterrani** (humitat sobre l'electrònica), en un
      lloc airejat i, si es pot, amb **cable Ethernet**.

### Muntatge

- [ ] Acabar d'instal·lar **Linux Mint** al portàtil secundari.
- [ ] **Decidir el mètode d'instal·lació** de Home Assistant (Docker sobre Mint vs. Debian +
      Supervised vs. HA OS). Decidir-ho *abans* d'instal·lar Mint si es vol canviar de base.
      → [home-assistant.md](domotica/home-assistant.md)
- [ ] Decidir **on viu físicament el servidor** i com s'hi accedeix de forma remota.
- [ ] Configurar la **retenció llarga de l'històric** (el `recorder` purga als 10 dies per
      defecte) i les còpies de seguretat.
- [ ] Confirmar si la **càmera Tapo C200** que es va investigar era per al local.
- [ ] **Decidir on viu la lògica de control** del punt de rosada (HA natiu, Node-RED,
      AppDaemon, pyscript o servei propi en Python). → [arquitectura.md](domotica/arquitectura.md)
- [ ] **Decidir la base de dades i l'eina de visualització.** Hi ha proposta: PostgreSQL +
      dashboards natius, Grafana més tard. → [monitoritzacio.md](domotica/monitoritzacio.md)
- [ ] ⚠️ **Configurar `purge_keep_days: 730` ABANS del primer sensor.** No té arreglada a
      posteriori: el `recorder` purga als 10 dies per defecte.
- [ ] ⚠️ **Convertir l'estat dels ventiladors en sensors numèrics** (`history_stats` +
      `utility_meter`). Els binaris no generen estadístiques a llarg termini, i per tant la
      prova que la ventilació estava operativa **s'esborra** amb la purga.
- [ ] Fixar els **noms d'entitat definitius** abans de posar cap sensor en producció.
- [ ] Muntar el **ritual mensual** d'exportació CSV + SHA-256 fora del local.
- [ ] Valorar un **sensor de temperatura superficial de paret** (DS18B20 via ESPHome) a cada
      punt humit: és l'únic que discrimina directament condensació de capil·laritat.
- [ ] **Decidir el mètode d'accés remot.** Proposta actualitzada: **Tailscale** per
      administrar + **GitHub/Pages** per publicar dades i fer còpia externa.
      → [acces-remot.md](domotica/acces-remot.md)
- [x] ~~Decidir si cal SSH.~~ ✅ **Sí: Tailscale.** El flux és casa → GitHub → portàtil del
      local, i desplegar necessita shell. → [desplegament.md](domotica/desplegament.md)
- [ ] Crear un **repositori separat i privat només per a les dades**, amb un *fine-grained
      token* limitat.
- [ ] ⚠️ **Decidir si les dades del panell web seran privades o públiques.** Les dades de
      sensors revelen patrons d'ocupació del local. Un panell estàtic no pot llegir un
      repositori privat sense credencials, i un token dins d'una pàgina web és un token
      públic. Recomanació: privades, a R2 amb domini propi darrere Cloudflare Access.
      → [publicacio-dades.md](domotica/publicacio-dades.md)
- [ ] **Decidir la via de l'arxiu de dades:** GitHub Releases (no toca l'historial de git) o
      emmagatzematge d'objectes R2/B2 (immutabilitat forta).
- [ ] Fixar l'**estructura de fitxers del panell** (`latest.json` + `index.json` +
      `daily/*.json`) i que les marques de temps siguin **ISO 8601 amb zona horària**.
- [ ] Escriure el **script de desplegament** amb validació de configuració abans del reinici.
- [ ] **Fixar les versions** al `docker-compose.yml` — res de `:latest`.
- [ ] Definir els **helpers i automatismes en YAML**, no per interfície: el que es crea des
      de la UI viu a `.storage/` i no es pot versionar.
- [ ] Muntar un **avís de caiguda** (Healthchecks.io / UptimeRobot) i una **còpia de
      l'històric fora del local**. Sense això l'accés remot no serveix de res.
- [ ] Valorar un **endoll intel·ligent de rearmada** per al portàtil i el router,
      independent de Home Assistant.
- [ ] **Consultar amb un professional el valor probatori** d'un històric autogenerat: pot
      caldre exportació segellada temporalment o un enregistrador independent. Això
      condiciona tota l'estratègia de les humitats.
- [x] ~~Verificar si hi ha IP pública o CGNAT.~~ Internet per **SIM** → CGNAT quasi segur:
      port forwarding i WireGuard directe queden descartats.
- [ ] **Decidir el protocol dels sensors.** Proposta: Zigbee amb **coordinador en xarxa
      col·locat al soterrani** (SLZB-06). → [control-punt-rosada.md](domotica/control-punt-rosada.md)
- [ ] **Prova de cobertura de ràdio** al soterrani, 48 h, abans de comprar res.
- [ ] **Definir exactament quines dades es registren** (l'usuari ho ha ajornat conscientment).
- [ ] Inventariar el **deshumidificador**: marca, model, consum nominal, com s'engega.

## Verificacions físiques al local (abans de gastar diners)

- [ ] ⚠️ **El deshumidificador arrenca sol després d'un tall de corrent?** Si no, tot el
      control per endoll intel·ligent és inútil.
- [ ] ⚠️ **Per on entra l'aire de reposició** quan els extractors funcionen? (Prova de fum.)
      Si entra per fissures en contacte amb el terreny, **el ventilador pot estar empitjorant
      les humitats** i el projecte canvia de naturalesa.
- [ ] Els ventiladors estan **endollats o cablejats**? Hi ha interruptor de paret?
- [ ] Placa del deshumidificador: potència, L/dia, temperatura mínima, desguàs per tub.
- [ ] Quina és la **paret més freda i humida** (termòmetre IR de mà) → allà va el sensor de
      temperatura superficial.
- [ ] Rang de temperatura del soterrani a l'hivern (per sota de 15 °C un deshumidificador per
      compressor rendeix malament).
- [ ] Horaris de soroll admissibles per als veïns.
