# Inventari d'aparells

> Actualitzat el **20/09/2026** amb el maquinari que ja està comprat. Això **substitueix** la
> proposta de maquinari de [control-punt-rosada.md](control-punt-rosada.md) i corregeix la
> decisió de ràdio de [decisio-stack.md](decisio-stack.md).

## ✅ Ja comprat i funcionant

### Ecosistema TP-Link Tapo

| Aparell | Model | Ubicació | Estat |
|---|---|---|---|
| Hub | **Tapo H100** (?) | corridor | Actiu |
| Endoll intel·ligent | **Tapo P1xx** ⚠️ | corridor | Actiu — per al deshumidificador |
| Sensor T/HR | **Tapo T315** | *Centre* | Actiu |
| Sensor T/HR | **Tapo T315** | *Dalt* | Actiu |
| Sensor T/HR | **Tapo T315** | *Fons* | Actiu |
| Sensor T/HR | **Tapo T310** | *Fora* | Actiu |
| Sensor T/HR | **Tapo T310** | *Gran* | Actiu |
| Sensor d'inundació | **Tapo T300** (?) | Centre | Actiu |
| Càmeres | Tapo | — | N'hi ha |

**Lectura de referència (20/09/2026, 16:25):** Centre 22,4 °C / 66 % · Dalt 23,5 °C / 61 % ·
Fons 23,5 °C / 62 % · Fora 23,9 °C / 68 % · Gran 22,7 °C / 64 %.

> Amb aquestes lectures, el punt de rosada interior ronda els **15–16 °C** i l'exterior els
> **17,5 °C**: ara mateix **ventilar afegiria aigua**. És exactament el cas que l'automatisme
> ha d'evitar, i es veu ja al primer cop d'ull.

### Deshumidificador

**QLIMA D 825 PA SMART** (ref. Leroy Merlin 91164803, EAN 8713508793047)

| Característica | Valor |
|---|---|
| Capacitat | **25 L/24 h** |
| **Consum elèctric** | **470 W** (2,2 A) |
| Cabal d'aire | 200 m³/h |
| Per a estances de | 140–165 m³ *(el soterrani ≈ 115 m³ — hi cap de sobres)* |
| Dipòsit | 3,8 L |
| **Bomba de condensats incorporada** | ✅ Sí — la «PA» del nom |
| **Desguàs continu** | ✅ Sí, amb el tub inclòs |
| **Reinici automàtic després d'un tall** | ✅ **SÍ** |
| Higròstat ajustable | ✅ 40–80 % HR |
| Temporitzador | Màx. 9 h |
| Velocitats de ventilador | 3 |
| Control | Electrònic + **WiFi (app Smart Life / Tuya)** |
| Refrigerant | **R290** (propà), 70 g, GWP 3 |
| Filtres | Malla + HEPA |
| Soroll | < 47 dB(A) a 1 m |
| Dimensions / pes | 355 × 255 × 572 mm · 17 kg |
| Protecció | IPX4 |
| Garantia | 3 anys |

---

## 🎉 Tres coses que això desbloqueja

### 1. El reinici automàtic està confirmat

Era **la verificació bloquejant** de tot el disseny: si el deshumidificador no es reprengués
sol després d'un tall, el control per endoll intel·ligent no serviria de res. La fitxa de
producte ho diu explícitament: **«Reinicio automático: Sí»**.

→ L'arquitectura **(a)** de [control-punt-rosada.md](control-punt-rosada.md) queda confirmada:
l'higròstat propi de la màquina regula, i Home Assistant només fa l'**enclavament** amb els
ventiladors i les **franges horàries**.

### 2. La preocupació del Zigbee al soterrani desapareix

Els sensors Tapo **no fan servir Zigbee ni Wi-Fi**: parlen amb el hub per **ràdio sub-GHz de
868 MHz**. A 868 MHz la penetració a través de formigó armat és **notablement millor** que a
2,4 GHz — és el mateix argument que feia recomanable Z-Wave, però sense pagar-lo.

→ **Fora: SLZB-06, ZHA, coordinador Zigbee, prova de cobertura de 48 h.** ~45 € i una decisió
irreversible menys.

### 3. La bomba resol el dipòsit

A 25 L/dia, un dipòsit de 3,8 L **s'omple en menys de 4 hores**. Sense desguàs continu
l'aparell s'aturaria sol tres vegades al dia i l'automatisme no se n'assabentaria.

→ Amb la **bomba incorporada** el condensat es pot enviar cap amunt fins a un desguàs, sense
dependre de la gravetat. **El desguàs continu no és opcional: és obligatori.**

---

## ⚠️ El que cal verificar, per ordre d'importància

### 1. 🔴 L'endoll és un P110/P115 o un P100/P105?

**Només el P110 i el P115 mesuren consum. El P100 i el P105 no.** A la captura el nom surt
tallat com a «Tapo P1…».

> Si és un **P100**, l'objectiu «veure el consum del deshumidificador» **no es pot complir**
> amb aquest endoll i cal canviar-lo. Són uns 15–20 €.

Es veu al lateral de l'aparell o a la fitxa del dispositiu dins l'app.

### 2. 🟠 Temperatura mínima de funcionament

La fitxa de producte només diu «Interval de funcionament: 35 °C», que sembla el **màxim**. El
mínim no hi consta. Els deshumidificadors per compressor típics treballen de **5 a 35 °C** i
perden molt rendiment per sota de ~15 °C.

**Cal mirar-ho al manual** (132 pàgines, l'has de tenir amb l'aparell). Si el soterrani baixa
de 15 °C al gener, el rendiment real caurà molt per sota dels 25 L/dia de catàleg.

### 3. 🟠 On és cada sensor exactament

Els noms actuals són *Centre, Dalt, Fons, Fora, Gran*. Necessito saber, per a cadascun:

- **A quina planta és** (planta baixa o soterrani).
- **Si toca una paret humida** o està a l'aire.
- **«Fora» és realment a l'exterior?** Si ho és, hi ha un problema: el **T310 no és per a
  intempèrie**. Li cal un **abric de radiació** i estar protegit de la pluja, o les lectures
  d'HR seran brossa els dies que importen.

Sense aquesta correspondència no puc escriure la lògica: tot el sistema es basa a comparar el
punt de rosada **interior del soterrani** amb l'**exterior**.

### 4. 🟡 Calibratge creuat

Tens **models barrejats** (3× T315 i 2× T310). Això fa el pas de calibratge **més important**,
no menys: l'error sistemàtic entre models diferents no es cancel·la sol.

**Deixa'ls 24 h junts a la mateixa habitació**, apunta la desviació de cadascun respecte de la
mediana, i li aplico un *offset* fix a Home Assistant. Cost zero, i permet baixar el llindar
de decisió de 2,0 °C a ~1,2 °C — que són hores de ventilació gratuïta guanyades.

### 5. 🟡 Credencials de Tapo

La integració oficial `tplink` de Home Assistant **suporta el hub H100 i els seus sensors
filles**, i els consulta **localment** per IP. Però la configuració inicial demana el **correu
i la contrasenya del compte Tapo**, no només un testimoni local.

→ Reserva una **IP fixa per al hub** al router abans de configurar res.

---

## 🔧 El que encara falta

| Què | Per a què | Estat |
|---|---|---|
| **Commutació dels 2 ventiladors** | Governar-los pel punt de rosada | ❓ Depèn de si estan endollats o cablejats |
| **ESP32 + 2× DS18B20** | **Temperatura superficial de la paret freda** | Per comprar (~15 €) |
| **Abric de radiació** per al sensor exterior | Que les lectures de fora siguin fiables | Per comprar o fer (~10 €) |

> El **DS18B20 a la paret** segueix sent el component que més val per euro de tot el projecte:
> és l'únic sensor que **discrimina directament** condensació de capil·laritat. Els Tapo diuen
> com està l'aire; només aquest diu com està **la paret**.

---

## Decisió: NO integrem el deshumidificador per Tuya

El Qlima és un dispositiu **Tuya/Smart Life**. Es podria integrar a Home Assistant de dues
maneres, i **descartem totes dues de moment**:

| Via | Per què no |
|---|---|
| Integració **Tuya oficial** | Passa pel núvol. Hi ha informes d'entitats mal mapades en deshumidificadors Qlima |
| **tuya-local** (HACS) | Local i millor, però cal extreure la *local key* amb un compte de desenvolupador de Tuya IoT, la llicència del qual **caduca i s'ha de renovar**. Suporta D720, D812 i D820A, **però el D825 no hi és a la llista** |

**El que farem:** l'**higròstat propi** del Qlima regula la humitat, i el **Tapo P110** el
governa i en mesura el consum. Amb això tenim les dues coses que necessitem —engegar-lo o no,
i saber què gasta— **sense cap dependència de núvol nova ni cap llicència que caduqui**.

> És la decisió més alineada amb «com menys infraestructura millor» de tot el projecte:
> s'estalvia una integració, un compte de desenvolupador i un mode de fallada.
>
> Si més endavant vols ajustar el llindar d'HR **a distància**, es reobre. Mentre el llindar
> es posi un cop i no es toqui, no cal.

---

## ⚡ Dos avisos operatius

### Cicle curt del compressor

Com que l'aparell **es reprèn sol** en tornar el corrent, si Home Assistant encén i apaga
l'endoll de pressa, el compressor **arrenca contra pressió** i es fa malbé.

→ El **temps mínim d'aturada de 5 minuts** deixa de ser una recomanació i passa a ser
**obligatori** a la lògica. Vegeu [control-punt-rosada.md](control-punt-rosada.md).

### Refrigerant R290 (propà)

Són 70 g de gas **inflamable**. No és perillós en una estança normal —i un soterrani de 46 m²
ho és de sobres— però:

- No tancar-lo en un armari petit ni en un espai sense ventilació.
- Cap font d'ignició a prop.
- Si es manipula o es transporta, tombat mai; dret i deixant-lo reposar abans d'engegar-lo.

## 💶 Què costa fer-lo anar

A 470 W i amb la [tarifa Naturgy Noche](../local/subministraments.md):

| Franja | €/h | 8 h/dia | 30 dies |
|---|---|---|---|
| 🟢 Vall | 3,5 c€ | 0,28 € | **8,3 €** |
| 🟡 Pla | 5,1 c€ | 0,41 € | 12,3 € |
| 🔴 Punta | 8,6 c€ | 0,69 € | **20,6 €** |

**Desplaçar-lo de punta a vall estalvia uns 12 € al mes** amb 8 h diàries. I si l'automatisme
del punt de rosada aconsegueix substituir-ne una part per ventilació —30–150 W en comptes de
470 W— l'estalvi s'hi suma. Aquesta taula és la que la Porta B ha de validar amb dades reals.
