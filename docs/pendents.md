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
- [ ] **Decidir la via de l'arxiu de dades:** GitHub Releases (no toca l'historial de git) o
      emmagatzematge d'objectes R2/B2 (immutabilitat forta).
      → [publicacio-dades.md](domotica/publicacio-dades.md)
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
