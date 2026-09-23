# Fases, portes de test i repartiment de feina

> Basat en [decisio-stack.md](decisio-stack.md). Cada fase té una **porta de sortida
> verificable**: no es passa a la següent fins que la porta està tancada.
>
> Els requisits que encara **no són decisions** —i les tasques que en surten— viuen a
> [requisits.md](requisits.md).

## El rellotge

Avui és **20 de setembre de 2026**. La retenció venç cap al **9 de març de 2027**: són
**5,5 mesos i un sol hivern**. Això no dona marge per experimentar a mitja carrera, i per
això el pla és **muntar-ho aviat i congelar-ho**.

> 🟢 **21/09/2026 — canvi d'objectiu** ([decisio-stack.md](decisio-stack.md)): el
> ~09/03/2027 **deixa de governar cada decisió**. Segueix sent rellevant —l'hivern és quan es
> juga la disjuntiva ventilar/deshumidificar—, però una setmana de retard ja no és una pèrdua
> irreparable, i **«congelar-ho» ja no forma part del pla**. La Fase D queda ajornada.

| Fase | Què és | Quan |
|---|---|---|
| **0** | Física i decisions irreversibles | Ara |
| **A** | El que no té arreglada a posteriori | Abans del primer sensor |
| **B** | Mesurar sense actuar | 4 setmanes |
| **C** | Actuar | Des de mitjans de novembre |
| **D** | Dossier | Gener–febrer 2027 |

---

## Fase 0 — Física i decisions irreversibles

**Abans de comprar res.** Tot això són dades que canvien el disseny, i algunes el poden
invalidar.

| # | Tasca | Qui |
|---|---|---|
| 0.1 | **Prova de fum del camí de l'aire de reposició** amb els extractors en marxa | 👤 Tu |
| 0.2 | ~~Deshumidificador: arrenca sol? temperatura mínima?~~ ✅ **Resolt pel manual:** sí, i 5–35 °C | — |
| 0.2b | ~~**PROVA: desendollar-lo i tornar-lo a endollar**~~ ✅ **Superada el 21/09/2026**, a distància: configuració inconfusible, compressor quiet, un minut sense corrent tallant l'endoll. **Recorda el mode, el llindar i la velocitat, i es reprèn sol** → [deshumidificador.md](deshumidificador.md#2-memòria-la-prova-02b) | 🤖 Fet |
| 0.3 | **Paret més freda i humida** amb termòmetre IR de mà | 👤 Tu |
| 0.4 | ~~Prova de cobertura Zigbee.~~ ✅ **No cal:** els Tapo van per 868 MHz. ✅ **I ja està decidit on va cada un** dels cinc, amb el de fora protegit de la pluja | — |
| 0.5 | **Salut del portàtil:** SMART del disc, capacitat de bateria, pila CMOS, si té Ethernet | 🤝 Tu executes, jo interpreto |
| 0.5b | 🔧 **Tanda física al BIOS, abans de moure el portàtil:** *restore on AC power loss*, límit de càrrega, disc intern a dalt de l'arrencada, RJ-45 amb cable | 👤 Tu |
| 0.6 | Ubicació física del portàtil: **planta baixa**, aixecat de terra, ventilat | 👤 Tu |
| 0.7 | ~~Contractar la SIM~~ ✅ **Feta i en servei** *(21/09/2026)*: tot l'stack ja penja del router de la SIM. ⏳ Queda saber-ne el **límit de dades** i córrer les 72 h de `vnstat` | 👤 Tu |

### 🚦 Porta 0

- [ ] Sé **per on entra l'aire de reposició**.
- [x] ~~Sé si el deshumidificador es reprèn sol.~~ ✅ Sí, i funciona de 5 a 35 °C.
- [x] ~~Sé si **recorda el llindar d'humitat** després d'un cicle d'alimentació.~~ ✅ **Sí** (21/09/2026): recorda mode, llindar i velocitat. L'arquitectura (a) es manté. ⚠️ **Però en mode AUTO no fa cas del llindar**: ha d'estar en Manual → [deshumidificador.md](deshumidificador.md)
- [x] ~~Sé si el Zigbee arriba al soterrani.~~ ✅ No hi ha Zigbee. ⚠️ **Però l'stack ha passat a 2 contenidors** el 21/09/2026: `tplink` rebutja el hub i la via és Matter, que demana el seu propi servidor.
- [x] ~~Sé **quin model és l'endoll**.~~ ✅ **Tapo P110: mesura consum.** És el que fa
      possible el `utility_meter` del deshumidificador i, amb ell, els kWh/dia de la Porta B.
- [x] ~~Sé **on va cada sensor** i si el de fora estarà protegit de la pluja.~~ ✅ **Assignació
      fixada:** *Centre* (T315), *Fons* (T315) i *Gran* (T310) al soterrani, *Dalt* (T315) a la
      planta baixa i *Fora* (T310) a l'exterior, **protegit** ✅. ⚠️ Això és **on aniran**: ara
      mateix els cinc són encara **a casa**, junts, fent el calibratge creuat.
      → [inventari.md](inventari.md)
- [ ] Sé si el portàtil necessita **SAI**.
- [ ] ⚠️ Sé si el BIOS té ***restore on AC power loss***. Si no el té, la mitigació està
      decidida i escrita (apagada ordenada al 20 %, o `Wake on LAN`).

> ⚠️ **0.1 pot canviar el projecte de naturalesa.** Si l'aire entra per fissures en contacte
> amb el terreny, els ventiladors estan xuclant aire saturat del subsol i **poden estar
> empitjorant les humitats**. Si passa això, parem i replantegem: deixa de ser un problema de
> control i passa a ser-ho de construcció.

---

## Fase A — El que no té arreglada a posteriori

**Cap dada d'aquesta fase es pot recuperar si es fa malament.** És la fase on jo puc fer més
feina i tu menys.

| # | Tasca | Qui |
|---|---|---|
| A.1 | Instal·lar Linux Mint, Docker, Tailscale al portàtil del local | 👤 Tu |
| A.2 | Host: sense suspensió, *restore on AC power loss*, `Europe/Madrid`+NTP, `systemd-time-wait-sync`, rotació de logs, reserves DHCP | 🤝 Jo escric el guió, tu l'executes |
| A.3 | **Tailscale amb l'expiració de clau desactivada** | 👤 Tu (és al seu web) |
| A.4 | ~~Crear `Local-data` privat + clau de desplegament SSH~~ — ✅ **sense objecte** des del 21/09/2026 | 👤 Tu |
| A.5 | `.gitattributes` amb `* text=auto eol=lf` | 🤖 Jo |
| A.6 | `docker-compose.yml` amb versió d'HA fixada | 🤖 Jo |
| A.7 | `recorder` amb `purge_keep_days: 730`, `commit_interval`, `exclude` per llistes | 🤖 Jo |
| A.8 | **Conveni de noms d'entitat** escrit al repositori | 🤖 Jo |
| A.9 | `nit.py` + unitats systemd + guardes | 🤖 Jo (**i el provo aquí** amb una base de dades sintètica) |
| A.10 | `desplega.sh` amb totes les portes | 🤖 Jo |
| A.11 | Compte de healthchecks.io i els dos checks | 👤 Tu |
| A.12 | **Restauració de prova manual verificada** | 🤝 Jo escric el procediment, tu l'executes |
| A.13 | ✅ **Fet el 23/09/2026** — 60 h amb els cinc junts en tres tandes (nit, tàper amb sal fins al 73 %, nevera). Dispersió de Td **0,89 → 0,28 °C** per blocs; correcció d'HR aplicada a les cinc plantilles de `rosada.yaml` i T sense corregir. ⏳ **El fred queda obert**: el rang mesurat és 26–30 °C i el soterrani serà de 8–20; es repeteix allà a l'hivern. Números, mètode i dades crues a [calibratge.md](calibratge.md) | 🤝 Tu el fas, jo l'ajusto |
| A.14 | ✅ **Fet** — `scripts/comprova.sh` (302 línies): verifica d'una passada el host, la suspensió, la tapa, Docker, **els dos contenidors un per un**, HA, els sostres de memòria i Tailscale. És el que es corre **després de cada canvi al host** i abans de donar una porta per tancada | 🤖 Jo |
| A.15 | ✅ **Fet** — `tools/valida_yaml.py` (100 línies): valida el YAML **des de casa**, abans de desplegar, sense esperar el `check_config` del contenidor | 🤖 Jo |
| A.16 | 🔴 **Que els paràmetres sobrevisquin un reinici** ([R2](requisits.md#r2--tocar-els-paràmetres-de-lalgoritme-des-de-la-web)): provar-ho al banc de casa, decidir què es fa amb `initial:` i garantir que els `input_number` **no s'exclouen mai del `recorder`** ni de l'exportació | 🤝 Tu fas la prova de 3 min, jo corregeixo el YAML |
| A.17 | 🔴 **Gravar la previsió des del primer dia** ([R3](requisits.md#-la-previsió-lúnica-part-que-no-té-arreglada-a-posteriori)): sensors per disparador que materialitzin el Td previst a +3 h, +12 h i +24 h. Una previsió que no es grava **no es pot reconstruir després** | 🤖 Jo |
| A.18 | ✅ **Fet** — `tools/valida_xifres.py` (249 línies): comprova que les **xifres de línies** citades als documents quadrin amb els fitxers reals. Es corre **abans d'obrir cada PR**: cada cop que es tocava un fitxer, la xifra quedava vella sense que ningú se n'adonés, i va passar quatre vegades en una sola sessió | 🤖 Jo |

### 🚦 Porta A — la més important de totes

- [ ] `purge_keep_days: 730` està **al fitxer desplegat**, verificat mirant la configuració en
      calent, no el repositori.
- [ ] `nit.py` ha fet **tres nits seguides** de còpia correcta al disc USB. *(Deia «de commit
      correcte a `Local-data`»: superat el 21/09/2026. El que es prova —que la còpia nocturna
      no falla— es manté.)*
- [ ] Els **dos checks** de healthchecks.io han passat a verd i he provat que **es posen
      vermells** desconnectant el portàtil a posta.
- [ ] He **restaurat** una còpia i he obert la base de dades restaurada.
- [ ] `desplega.sh` ha **avortat correctament** amb un YAML trencat a posta.
- [ ] Els noms d'entitat estan fixats i escrits.
- [ ] 🔴 Un llindar canviat des de la interfície **segueix canviat després de reiniciar HA**, i
      el seu històric es grava i s'exporta. Si no, al gener no hi haurà manera de dir quin
      llindar regia el 3 de gener. → [R2](requisits.md#r2--tocar-els-paràmetres-de-lalgoritme-des-de-la-web)
- [ ] 🔴 La **previsió ja es grava** quan arrenca la sèrie de debò, no després.
      → [R3](requisits.md#-la-previsió-lúnica-part-que-no-té-arreglada-a-posteriori)

> Aquesta porta és la que no es pot tornar a jugar. Un `purge_keep_days` mal posat descobert
> al gener són tres mesos de dades crues que no tornen.

---

## Fase B — Mesurar sense actuar (4 setmanes)

| # | Tasca | Qui |
|---|---|---|
| B.0 | 🔴 **La frontera: `scripts/inicia-serie.sh --de-debo`.** Arxiva la base d'experimentació i comença de zero amb una data d'inici escrita. **Es corre un sol cop**, quan els cinc sensors ja siguin a la seva posició definitiva i **abans** que compti cap dels 28 dies | 🤝 Jo l'he escrit, tu l'executes |
| B.1 | ~~Comprar sensors i endoll, i fixar-ne model i destí.~~ ✅ **Fet:** cinc T/HR comprats i gravant, endoll **P110** amb mesura de consum, i assignació decidida. ⏳ **Queda repartir-los pel local** — avui són a casa | 👤 Tu |
| B.1b | **Desguàs continu** del deshumidificador amb la bomba incorporada — obligatori, el dipòsit s'omple en 4 h | 👤 Tu |
| B.1c | ✅ **Prova superada el 21/09/2026:** `tuya-local` 2026.9.1 (fixada per suma, sense HACS) el reconeix com a **D820A amb un 89 % de coincidència**, en **local** i amb protocol 3.4. Llegeix el llindar, l'HR, la temperatura i la falla, i les dotze entitats es van renombrar al cap de dos minuts. Queda saber on surten el P1 i el P2 → [inventari.md](inventari.md#decisió-no-integrem-el-deshumidificador-per-tuya--es-reobre-provar-tuya-local) — *Com era:* 🆕 **Provar `tuya-local`** amb el deshumidificador: emparellar-lo a la Wi-Fi del router SIM, configuració assistida, i veure si el reconeix. Si sí, noms fixats abans, i al principi **només lectura i llindar**. Opcional, excepte si 0.2b surt malament → [inventari.md](inventari.md#decisió-no-integrem-el-deshumidificador-per-tuya--es-reobre-provar-tuya-local) | 🤝 Tu emparelles, jo configuro |
| B.1d | ✅ **Fet el 21/09/2026** — endoll **P110M** emparellat per Matter (node 9), amb el microprogramari ja posat abans i **les dotze entitats renombrades el mateix dia**. En surten potència i **energia**, o sigui que els kWh/dia de la Porta B tenen font → [emparellar-matter.md](emparellar-matter.md#-com-va-acabar-21092026-0345) | 🤝 Fet |
| B.2 | Muntar el node ESP32 + 2× DS18B20 a la paret freda. *(22/09/2026: a priori, **escenari C, Ecowitt sense fils** —dues sondes WN34L i el pluviòmetre WH40 per comptar l'aigua—, pendent de veure distàncies i endolls → [tres escenaris](inventari.md#comptar-laigua-i-mesurar-la-paret--tres-escenaris-22092026))* | 👤 Tu |
| B.3 | Compilar i pujar el firmware d'ESPHome per OTA *(no caldria amb l'escenari C: Ecowitt s'integra sense programar)* | 🤝 Jo escric el YAML, tu compiles a casa |
| B.4 | ✅ **Fet** — `packages/rosada.yaml` (633 línies): Td, ΔTd, marge, `history_stats`, `utility_meter` i `sensor.decisio_del_soterrani`. Els blocs dels ventiladors hi són **comentats** fins a la Fase C. *(22/09/2026: la decisió, els paràmetres i els modes passen a `packages/control.yaml` amb la [lògica v2](logica-v2-pla.md), en ombra)* | 🤖 Jo |
| B.5 | **Els ventiladors segueixen en el règim actual — no s'aturen** | — |
| B.6 | Dashboards natius + app Companion | 🤝 Jo proposo, tu ajustes al gust |
| B.7 | ✅ **Fet** — `tools/replica.py` (1099 línies): rèplica offline de la lògica i test de deriva contra el que va registrar el sensor. *(22/09/2026: rèplica de la v2, amb `--prova-ha`, que compara la macro avaluada per HA, i `--deriva`, que torna a decidir cada fila gravada)* | 🤖 Jo |
| B.8 | **Filtratge d'espuris en paral·lel, sense decidir res** ([R1](requisits.md#r1--netejar-les-lectures-espúries-sense-perdre-la-prova)): primer mesurar cadència, soroll base i pendent màxima creïble; després escriure'l. La sèrie crua **no es toca** | 🤖 Jo |
| B.9 | **Avançar el guió de gràfics del dossier** (era D.1) i fer-hi la **correlació creuada Td soterrani ↔ Td exterior**: és la resposta continuada a *per on entra l'aire* | 🤖 Jo |
| B.10 | Obrir `diari-de-la-serie.md` i anotar-hi els esdeveniments externs —pluges, visites, un sensor agafat amb la mà— perquè cada pic tingui explicació | 🤝 Tu aportes els fets, jo els munto |

> 🔴 **Per què B.0 va primer.** Els sensors s'han provat a casa gravant amb els noms de debò
> —`sensor.soterrani_fons_temperatura` damunt d'una taula del menjador—. Aquestes files són a
> la mateixa base de dades i amb la mateixa etiqueta que les de debò, i davant d'un pèrit això
> és **contaminació**: trobat per l'altra part, posa en dubte la sèrie sencera. ⚠️ La base
> d'experimentació **s'arxiva, no s'esborra**: conté el calibratge creuat, que és l'única
> mesura de la desviació entre sensors i **no es pot repetir** un cop repartits pel local.

> **Per què els ventiladors no s'aturen:** la clàusula QUINTA obliga a mantenir-los operatius.
> El deure legal i el grup de control coincideixen — es mesura amb el règim actual i el sensor
> de decisió registra què *hauria* fet.

### 🚦 Porta B

- [ ] **28 dies seguits** de dades sense cap forat superior a 2 h.
- [ ] `sensor.decisio_del_soterrani` porta 28 dies registrant, i la **rèplica offline coincideix**
      amb el que va registrar (si divergeixen, les dues implementacions han derivat).
- [ ] Sé **quantes hores hauria ventilat** amb Δ_ON = 2,0 °C, i amb 1,5 i 2,5.
- [ ] Sé els **litres/dia i els kWh/dia** reals del deshumidificador.
- [ ] El marge de superfície (paret − Td interior) té 28 dies d'història.
- [ ] Sé **quantes mostres s'han descartat** per sensor i per dia, i per quin motiu — i el
      llindar d'alerta de la taxa de descart està fixat amb aquestes dades.
- [ ] Hi ha **un joc de gràfics fet des dels CSV arxivats** (no captures de la interfície) que
      correla rosades, potència, decisió i previsió en un mateix eix de temps.
- [ ] Sé si el **Td del soterrani segueix el de l'exterior**, amb quin retard i quina
      amortiguació. És la resposta amb dades a la incògnita del camí de l'aire.

> 🎯 **Aquesta porta decideix si la Fase C val la pena.** Si l'automatisme hauria ventilat
> 40 hores en un mes, l'estalvi no compensa els relés i ens quedem amb la instrumentació,
> que és el que de debò importa per al cas. Si en són 200+, endavant.
>
> ⚠️ Si els litres/dia passen de **8–10 sostinguts**, la conversa deixa de ser de domòtica i
> passa a ser de construcció: apunta a capil·laritat o filtració, no a condensació.

---

## Fase C — Actuar (des de mitjans de novembre)

| # | Tasca | Qui |
|---|---|---|
| C.1 | Fixar Δ_ON/Δ_OFF **amb les dades pròpies** de la Fase B | 🤝 Jo calculo, tu valides |
| C.2 | Instal·lar relés als ventiladors | 👤 **Instal·lador autoritzat** si són cablejats |
| C.3 | ~~Enclavament dur ventilador/deshumidificador~~ — **superat el 22/09/2026** per la [lògica v2](logica-v2-pla.md): el deshumidificador no s'apaga mai; mentre ventila, al 70 %, i en urgència treballen tots dos | 🤖 Jo |
| C.4 | Selector de mode amb caducitat i override físic. *(22/09/2026: els modes de la v2 —Òptim, Ocupat, Prioritzar ventilació, Assecat intensiu, Silenci, Impressió, Absència, Llindar fix, Tot aturat— entren a la Fase 1 del [pla](logica-v2-pla.md); l'override físic, amb els S110E)* | 🤖 Jo |
| C.5 | Anti-cicle curt **també configurat al dispositiu**, no només a HA | 🤝 Jo indico, tu configures |
| C.6 | Comportament d'arrencada de cada endoll: deshumidificador ON, ventiladors OFF. ✅ **La meitat feta el 21/09/2026**: el P110M venia en `off` —no hauria tornat sol després d'un tall— i s'ha posat a **`on`** des d'HA (`select.deshumidificador_power_on_behavior`). Queden els S110E | 🤝 Jo ho poso, tu ho verifiques |
| C.7 | ~~Congelació total de versions fins al 10/03/2027~~ — ✅ **sense objecte** des del 21/09/2026. Les versions segueixen fixades i s'actualitzen només a posta | 🤖 Jo |

### 🚦 Porta C

- [ ] L'enclavament s'ha provat: forçant els dos alhora, **només n'hi ha un d'encès**.
- [ ] Desconnectant el sensor exterior a posta, **els ventiladors s'aturen** (fallada segura).
- [ ] El temps mínim d'engegada i d'aturada es respecten **després de reiniciar HA**.
- [ ] El mode manual **caduca sol** i torna a `Auto`.
- [ ] Traient el corrent i tornant-lo a posar, tot torna a l'estat previst sense tocar res.
- [ ] Una setmana en automàtic sense cap alerta ni cap repicada del relé.

---

## Fase D — Dossier (gener–febrer 2027)

> ⏸️ **Ajornada el 21/09/2026**, amb la via documental: «amb la porta oberta», i no s'hi
> inverteix temps ara → [decisio-stack.md](decisio-stack.md). Les dades crues es continuen
> gravant amb `purge_keep_days: 730` precisament perquè aquesta fase es pugui reprendre.

| # | Tasca | Qui |
|---|---|---|
| D.1 | Gràfics a partir dels CSV arxivats — **el guió ja hauria d'estar escrit i rodat des de la B.9**; aquí només es corre sobre la sèrie sencera | 🤖 Jo |
| D.2 | Cronologia anotada (pluges, derrama de façana, incidències) — surt del `diari-de-la-serie.md` de la B.10 | 🤝 Tu aportes els fets, jo els munto |
| D.3 | Informe amb la conclusió sobre l'origen de les humitats | 🤝 Jo redacto, tu decideixes què se'n fa |
| D.4 | Decidir si es dedueix de la retenció i amb quines factures | 👤 Tu |

### 🚦 Porta D

- [ ] Hi ha una resposta defensable a *«l'origen és condensació o no?»*.
- [ ] Els gràfics ho mostren sense necessitat d'explicació oral.
- [ ] L'arxiu és complet, amb els hashos i els segells, i **s'ha verificat que es pot obrir**.

---

## Repartiment de feina, en resum

### 🤖 El que puc fer jo sol

Tot el que és text dins del repositori, i **provar-ho aquí abans que toqui el local**:

- `docker-compose.yml`, `configuration.yaml` i el `recorder`.
- `packages/rosada.yaml` sencer: fórmula de Magnus, ΔTd, marge de superfície, sensor de
  decisió, helpers, automatismes, enclavament.
- `nit.py` complet, **provat contra una base de dades SQLite sintètica en aquest portàtil**:
  puc generar dades falses, córrer l'exportador i verificar que les guardes salten.
- `desplega.sh` amb totes les portes, i les unitats de systemd.
- `esphome/soterrani.yaml`.
- La rèplica offline de la lògica i els tests de deriva.
- Conveni de noms, documentació, guions pas a pas per a tot el que hagis d'executar tu.
- Revisar sortides i logs que m'enganxis.

### 👤 El que necessito que facis tu

Tot el que és **físic, presencial o de compte propi**:

- Gravar el pen drive, instal·lar Mint, entrar a la BIOS.
- Comprar el maquinari.
- Endollar, emparellar, enganxar sensors, muntar l'abric de radiació.
- **La prova de fum**, el termòmetre IR, mirar la placa del deshumidificador.
- Obrir comptes: Tailscale, healthchecks.io, el repositori privat, la SIM.
- Executar les comandes al portàtil del local *(fins que no hi tingui accés)*.
- **Qualsevol intervenció en instal·lació elèctrica fixa** → instal·lador autoritzat.
- Decidir el que és teu: diners, privacitat, i quant manteniment vols sobre l'esquena.

### 🤝 El que farem junts

- Interpretar els resultats de la Fase 0 i decidir si el projecte segueix igual.
- Fixar els llindars amb les dades reals de la Fase B.
- El dossier final.

## ✅ Acordat el 20/09/2026

- **Accés SSH:** un cop el sistema estigui muntat, tindré accés al portàtil del local per
  Tailscale. A partir d'aquell moment moltes files de «👤 Tu» passen a «🤖 Jo»: desplegar,
  mirar logs, diagnosticar i ajustar. Tu et quedes amb el que és físic.
- **Ordre de treball:** escric tot el codi **ara**, en paral·lel a les teves verificacions de
  la Fase 0. `nit.py` el provo en aquest portàtil contra una base de dades sintètica abans
  que toqui el local.
- **Maquinari:** ja en tens bona part comprat. La llista de maquinari de
  [control-punt-rosada.md](control-punt-rosada.md) és una proposta, **no una llista de
  compra**: s'ajustarà al que ja tinguis quan me'l passis.
- **Repositori:** públic, amb totes les dades identificatives fora, a `docs/privat/`
  (ignorat per git). L'historial s'ha reescrit perquè mai n'hagi contingut cap.
