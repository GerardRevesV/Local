# Pendents

Llista única de coses obertes. **Actualitzar-la cada cop que entri informació nova.**

## Crític — amb data límit

- [ ] **Determinar l'origen de les humitats abans del ~9 de març de 2027** (venciment de la
      retenció de 3.000 €). → [humitats.md](local/humitats.md)
- [ ] **Verificar l'estat del subministrament elèctric** del local i donar-lo d'alta si cal.
      Sense llum no hi ha ventilació, i la clàusula QUINTA ho fa recaure sobre el comprador.
      → [installacions.md](local/installacions.md)

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
- [ ] Comprovar l'estat de l'**aigua** i si hi ha o es pot tenir **Internet** al local.

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
- [ ] **Decidir el mètode d'accés remot.** Hi ha proposta: Tailscale + Nabu Casa.
      → [acces-remot.md](domotica/acces-remot.md)
- [ ] Muntar un **avís de caiguda** (Healthchecks.io / UptimeRobot) i una **còpia de
      l'històric fora del local**. Sense això l'accés remot no serveix de res.
- [ ] Valorar un **endoll intel·ligent de rearmada** per al portàtil i el router,
      independent de Home Assistant.
- [ ] **Consultar amb un professional el valor probatori** d'un històric autogenerat: pot
      caldre exportació segellada temporalment o un enregistrador independent. Això
      condiciona tota l'estratègia de les humitats.
- [ ] **Verificar si l'operadora del local dona IP pública** o hi ha CGNAT — condiciona l'accés remot.
- [ ] **Decidir el protocol dels sensors** (Zigbee, Wi-Fi, ESPHome) i comprovar la cobertura
      de ràdio al soterrani.
- [ ] **Definir exactament quines dades es registren** (l'usuari ho ha ajornat conscientment).
- [ ] Inventariar el **deshumidificador**: marca, model, consum nominal, com s'engega.
