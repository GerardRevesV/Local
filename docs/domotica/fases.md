# Fases, portes de test i repartiment de feina

> Basat en [decisio-stack.md](decisio-stack.md). Cada fase té una **porta de sortida
> verificable**: no es passa a la següent fins que la porta està tancada.

## El rellotge

Avui és **20 de setembre de 2026**. La retenció venç cap al **9 de març de 2027**: són
**5,5 mesos i un sol hivern**. Això no dona marge per experimentar a mitja carrera, i per
això el pla és **muntar-ho aviat i congelar-ho**.

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
| 0.2b | 🔴 **PROVA: desendollar-lo i tornar-lo a endollar** amb l'higròstat a 45 %. Recorda el llindar o torna a la configuració de fàbrica? | 👤 Tu |
| 0.3 | **Paret més freda i humida** amb termòmetre IR de mà | 👤 Tu |
| 0.4 | ~~Prova de cobertura Zigbee.~~ ✅ **No cal:** els Tapo van per 868 MHz. Queda dir-me **on és cada sensor** i si «Fora» és realment a l'exterior | 👤 Tu |
| 0.5 | **Salut del portàtil:** SMART del disc, capacitat de bateria, pila CMOS, si té Ethernet | 🤝 Tu executes, jo interpreto |
| 0.5b | 🔧 **Tanda física al BIOS, abans de moure el portàtil:** *restore on AC power loss*, límit de càrrega, disc intern a dalt de l'arrencada, RJ-45 amb cable | 👤 Tu |
| 0.6 | Ubicació física del portàtil: **planta baixa**, aixecat de terra, ventilat | 👤 Tu |
| 0.7 | Contractar la SIM i saber-ne el **límit de dades** | 👤 Tu |

### 🚦 Porta 0

- [ ] Sé **per on entra l'aire de reposició**.
- [x] ~~Sé si el deshumidificador es reprèn sol.~~ ✅ Sí, i funciona de 5 a 35 °C.
- [ ] 🔴 Sé si **recorda el llindar d'humitat** després d'un cicle d'alimentació. Si no el recorda, l'arquitectura del deshumidificador canvia.
- [x] ~~Sé si el Zigbee arriba al soterrani.~~ ✅ No hi ha Zigbee. **L'stack és 1 contenidor.**
- [ ] Sé **quin model és l'endoll** (P110/P115 mesuren consum; P100/P105 no).
- [ ] Sé **on és cada sensor** i si el de fora està protegit de la pluja.
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
| A.4 | Crear `Local-data` privat + clau de desplegament SSH | 👤 Tu |
| A.5 | `.gitattributes` amb `* text=auto eol=lf` | 🤖 Jo |
| A.6 | `docker-compose.yml` amb versió d'HA fixada | 🤖 Jo |
| A.7 | `recorder` amb `purge_keep_days: 730`, `commit_interval`, `exclude` per llistes | 🤖 Jo |
| A.8 | **Conveni de noms d'entitat** escrit al repositori | 🤖 Jo |
| A.9 | `nit.py` + unitats systemd + guardes | 🤖 Jo (**i el provo aquí** amb una base de dades sintètica) |
| A.10 | `desplega.sh` amb totes les portes | 🤖 Jo |
| A.11 | Compte de healthchecks.io i els dos checks | 👤 Tu |
| A.12 | **Restauració de prova manual verificada** | 🤝 Jo escric el procediment, tu l'executes |
| A.13 | **24 h amb tots els sensors junts** a la mateixa habitació → *offsets* | 👤 Tu |

### 🚦 Porta A — la més important de totes

- [ ] `purge_keep_days: 730` està **al fitxer desplegat**, verificat mirant la configuració en
      calent, no el repositori.
- [ ] `nit.py` ha fet **tres nits seguides** de commit correcte a `Local-data`.
- [ ] Els **dos checks** de healthchecks.io han passat a verd i he provat que **es posen
      vermells** desconnectant el portàtil a posta.
- [ ] He **restaurat** una còpia i he obert la base de dades restaurada.
- [ ] `desplega.sh` ha **avortat correctament** amb un YAML trencat a posta.
- [ ] Els noms d'entitat estan fixats i escrits.

> Aquesta porta és la que no es pot tornar a jugar. Un `purge_keep_days` mal posat descobert
> al gener són tres mesos de dades crues que no tornen.

---

## Fase B — Mesurar sense actuar (4 setmanes)

| # | Tasca | Qui |
|---|---|---|
| B.1 | ~~Instal·lar sensors i endoll.~~ ✅ **Ja fet.** Queda confirmar-ne la ubicació i el model de l'endoll | 👤 Tu |
| B.1b | **Desguàs continu** del deshumidificador amb la bomba incorporada — obligatori, el dipòsit s'omple en 4 h | 👤 Tu |
| B.2 | Muntar el node ESP32 + 2× DS18B20 a la paret freda | 👤 Tu |
| B.3 | Compilar i pujar el firmware d'ESPHome per OTA | 🤝 Jo escric el YAML, tu compiles a casa |
| B.4 | `packages/rosada.yaml`: Td, ΔTd, marge, `history_stats`, `utility_meter`, `sensor.decisio_del_soterrani` | 🤖 Jo |
| B.5 | **Els ventiladors segueixen en el règim actual — no s'aturen** | — |
| B.6 | Dashboards natius + app Companion | 🤝 Jo proposo, tu ajustes al gust |
| B.7 | Rèplica offline de la lògica + test de deriva | 🤖 Jo |

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
| C.3 | Enclavament dur ventilador/deshumidificador | 🤖 Jo |
| C.4 | Selector de mode amb caducitat i override físic | 🤖 Jo |
| C.5 | Anti-cicle curt **també configurat al dispositiu**, no només a HA | 🤝 Jo indico, tu configures |
| C.6 | Comportament d'arrencada de cada endoll: deshumidificador ON, ventiladors OFF | 👤 Tu |
| C.7 | **Congelació total de versions fins al 10/03/2027** | 🤖 Jo |

### 🚦 Porta C

- [ ] L'enclavament s'ha provat: forçant els dos alhora, **només n'hi ha un d'encès**.
- [ ] Desconnectant el sensor exterior a posta, **els ventiladors s'aturen** (fallada segura).
- [ ] El temps mínim d'engegada i d'aturada es respecten **després de reiniciar HA**.
- [ ] El mode manual **caduca sol** i torna a `Auto`.
- [ ] Traient el corrent i tornant-lo a posar, tot torna a l'estat previst sense tocar res.
- [ ] Una setmana en automàtic sense cap alerta ni cap repicada del relé.

---

## Fase D — Dossier (gener–febrer 2027)

| # | Tasca | Qui |
|---|---|---|
| D.1 | Gràfics a partir dels CSV arxivats | 🤖 Jo |
| D.2 | Cronologia anotada (pluges, derrama de façana, incidències) | 🤝 Tu aportes els fets, jo els munto |
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
