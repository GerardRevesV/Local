# Requisits oberts — llista viva

> **Què és això.** Coses que el projecte ha de saber fer i que **encara no són decisions
> preses**. Entren aquí quan es defineixen, es treballen aquí mentre es pensen, i en surten
> quan es converteixen en codi o en una línia de [decisio-stack.md](decisio-stack.md).
>
> **Aquest document no mana.** Si un requisit acaba contradient
> [decisio-stack.md](decisio-stack.md), el canvi s'escriu **allà** i aquí només en queda el
> rastre. Vegeu la jerarquia a [`CLAUDE.md`](../../CLAUDE.md).

## Índex

| # | Requisit | Definit | Estat | Fase on toca |
|---|---|---|---|---|
| **R1** | Netejar les lectures espúries sense perdre la prova | 21/09/2026 | 🔸 Dissenyat, **no escrit**: falta saber la cadència real | B |
| **R2** | Tocar els paràmetres de l'algoritme des de la web | 21/09/2026 | 🔴 **Hi ha un bloquejant que es pot resoldre avui** | A |
| **R3** | Veure-ho tot junt i poder-ho correlar | 21/09/2026 | 🔴 Una part **no té arreglada a posteriori** | A i B |

> Les tres tenen una vora en comú, i val la pena dir-la d'entrada: **totes tres toquen el
> corpus probatori.** Un filtre que esborra, un paràmetre que canvia sense deixar rastre i una
> previsió que no es registra fan exactament el mateix mal — que al març de 2027 hi hagi una
> sèrie que no es pugui explicar.

---

## R1 — Netejar les lectures espúries sense perdre la prova

> *«Quan s'agafa un sensor fa pic d'humitat i temperatura; hauríem de ser capaços de netejar
> aquests espuris (filtrar-los) d'alguna manera.»*

### Primer, una distinció que canvia el disseny

Agafar un sensor amb la mà **no és un error de mesura**: el sensor fa la seva feina i mesura
la mà. Això vol dir que sota la paraula «espuri» hi ha com a mínim quatre coses diferents, i
cadascuna vol un tractament diferent:

| Família | Exemple | Com es reconeix | Què se n'ha de fer |
|---|---|---|---|
| **Pertorbació real, irrellevant** | agafar-lo, respirar-hi a prop, obrir la porta, arrencar el ventilador | dura **minuts**, puja i baixa suau | **no es filtra: s'anota** (vegeu R3) |
| **Artefacte de transmissió** | una mostra sola disparada, la següent torna al lloc | **una sola mostra**, salt físicament impossible | es descarta i **es compta** |
| **Sensor degradat** | bateria baixa, condensació a dins, brutícia | soroll que **creix**, deriva, valors enganxats a 0 o 100 | **alarma**, no filtre |
| **Buit** | no arriba res | `unavailable`, o el mateix valor congelat | ja resolt: fallada segura |

**La conseqüència de disseny:** el discriminador barat entre la primera i la segona família
no és la mida del salt, és la **persistència**. Una pertorbació real dura més d'una mostra;
un artefacte, no. Un filtre construït sobre aquesta idea és molt més fi que una mitjana
mòbil, i no perd els esdeveniments de debò.

### La regla que no es negocia

**La sèrie crua no es toca mai.** El filtratge crea entitats **noves**; les originals
segueixen gravant-se i s'arxiven senceres cada nit.

Això ja és el criteri del projecte en un cas germà: els desplaçaments de calibratge de
[`custom_templates/calibratge.jinja`](../../config/custom_templates/calibratge.jinja) s'apliquen
**només al càlcul derivat**, i la lectura crua queda intacta. El filtratge segueix la mateixa regla, pel mateix
motiu:

> Un pic pot ser **la prova**. El desgebratge del deshumidificador, una entrada d'aigua, una
> porta oberta tota la nit, un dia que algú va estar al soterrani. Si l'arxiu està suavitzat,
> la frase *«el 14 de gener a les 03:12 l'HR del fons va saltar 12 punts»* ja no es pot dir.
> **Suavitzar l'arxiu és destruir informació de manera irreversible per guanyar un gràfic més
> bonic.**

Per tant, **dues sèries**: la **crua** (arxiu, no decideix res) i la **filtrada** (decideix, i
també s'arxiva, perquè si no la decisió no és reproduïble).

### Les tres capes

| Capa | Què atrapa | Com | Què fa amb la mostra dolenta |
|---|---|---|---|
| **1. Plausibilitat** | valors impossibles i codis d'error | límits físics durs: T ∈ [−10, 50] °C, HR ∈ [1, 100] % | **no la fa servir**: l'entitat derivada passa a *unavailable*. **Mai s'arrodoneix al límit** |
| **2. Persistència** | el pic d'una sola mostra | una mostra que se surt més de X de l'anterior **no es creu fins que la següent la confirma** | l'ajorna i **la compta** |
| **3. Suavitzat** | el tremolor de ±0,2 °C i ±1 % | **mediana** mòbil curta | la substitueix **només al camí de decisió** |

Dos detalls que no són estètics:

- **Mediana, mai mitjana.** La mitjana s'empassa el pic i el reparteix entre les mostres
  veïnes; la mediana l'ignora del tot i, a més, torna sempre un valor **realment mesurat**.
- **La capa 1 va a `availability:`, no a un filtre de rang.** Vegeu tot seguit.

### El que el `filter` de Home Assistant fa de debò

Comprovat a la documentació oficial el 21/09/2026, perquè el comportament no és el que el nom
suggereix:

| Filtre | Què fa amb el valor dolent | Ens serveix? |
|---|---|---|
| `range` | **el substitueix pel límit** (retalla) | 🚫 **Prohibit.** Converteix una lectura absurda en una de plausible, que és pitjor que no tenir-la. Per això la capa 1 va a `availability:` |
| `outlier` | **el substitueix per la mediana** de la finestra | ✅ Serveix per a la capa 3, amb la condició d'escriure al costat del gràfic que la sèrie filtrada és **estimació**, no mesura |
| `lowpass` | el pondera amb els anteriors: **introdueix retard** | 🔸 Amb temps mínims de 12 min ja tenim inèrcia de sobres. Afegir-ne més fa arrencar tard |
| `throttle` / `time_throttle` | es queda la primera mostra de la finestra i **llença la resta** | 🚫 No per al camí de dades: és aprimar l'arxiu |

### El filtre no pot ser un silenciador

És el mode de fallada d'aquesta funcionalitat, i és silenciós: **un sensor que comença a fer
pics és un sensor que s'està morint** (bateria, condensació a dins, brutícia). Si el filtre
els amaga bé, perdem setmanes d'avís.

Per tant, indissociable del filtre:

- Un **comptador de mostres descartades per sensor i per dia**, que s'arxiva com la resta.
- Una **alerta quan la taxa puja** (llindar a fixar amb dades de la Fase B, no ara).
- La taxa de descart és, de fet, **un indicador de salut del sensor tan bo com el residu
  contra l'AEMET** que ja tenim a `sensor.residu_del_punt_de_rosada_exterior`.

### Per què encara no està escrit

Perquè **dimensionar-lo sense dades seria inventar-se'l**. Falten tres números que només
surten de mirar:

1. **La cadència real de report** de cada Tapo cap al hub, i del hub cap a HA. Amb Matter és
   una subscripció amb interval mínim i màxim; quin surt de debò, **està per veure**.
2. **El soroll base** de cada sensor en repòs (desviació típica en una hora quieta).
3. **La pendent màxima creïble** de T i d'HR al soterrani, que és el que fixa el llindar de la
   capa 2 sense tallar esdeveniments reals.

Les finestres del `filter` es compten en **mostres**, no en minuts: sense (1), una finestra de
4 tant pot ser 2 minuts com 20. Escriure'l ara vol dir reescriure'l al desembre.

**El pla:** a la Fase B, el filtre corre **en paral·lel i sense decidir res** —exactament la
mateixa disciplina que `sensor.decisio_del_soterrani`, que registra sense actuar— durant una
setmana llarga. Quan la taxa de descart tingui sentit, passa a alimentar la decisió, i **la
data del canvi queda escrita**.

### Una honestedat sobre quant val això per al control

El control ja està protegit contra pics per construcció: banda morta d'1,2 °C, temps mínim
d'engegada de 12 min i d'aturada de 10 min. Un pic d'una mostra **no farà repicar cap relé**.

Per tant, el valor real d'R1 és, per ordre:

1. **Llegibilitat** — gràfics i dossier sense dents de serra inexplicables (R3).
2. **Salut dels sensors** — la taxa de descart és el detector precoç.
3. **Control** — evitar una arrencada espúria que després bloqueja 12 min en ON. Real, però
   el tercer.

Dir-ho evita el pitjor desenllaç possible d'aquest requisit: un filtre agressiu, posat aviat
i per comoditat visual, que es menja la vora dels esdeveniments que justament havíem de
mesurar.

### Decisions que queden obertes

| Decisió | Dada que la desbloqueja |
|---|---|
| Llindar de la capa 2 (pendent màxima creïble) | 72 h de sèrie real de cada sensor |
| Mida de la finestra de la mediana | cadència real de report |
| Llindar d'alerta de la taxa de descart | taxa base amb els sensors sans |
| Si el node ESPHome filtra a bord | quan existeixi: ESPHome porta filtres propis i és on són els DS18B20 |

---

## R2 — Tocar els paràmetres de l'algoritme des de la web

> *«Hauríem de ser capaços des de la web de definir paràmetres, com temps entre enviaments,
> llindars, etc., que farà servir l'algoritme.»*

### «La web», aquí, és la interfície de Home Assistant

No cal panell propi **per a això**. Els
`input_number` que ja hi ha a [`packages/rosada.yaml`](../../config/packages/rosada.yaml)
surten sols a la interfície d'HA i a l'app Companion, s'hi toquen amb el dit, i s'hi arriba
des de fora per Tailscale. El requisit, en la seva part central, **ja està cobert** — i té un
forat.

> ⚠️ *Aquí hi deia «`decisio-stack.md` el descarta i té raó». El **21/09/2026** aquell
> document **va reobrir** el panell propi: primer taulers natius i, si no hi arriben, un
> panell servit per HA des de `config/www/`. Per a **aquest** requisit segueix sense caldre'n
> cap —els `input_number` ja surten sols a la interfície—, però ja no és cert que estigui
> descartat.*

### 🔴 El forat, i es pot tapar avui

Els nou `input_number` del paquet porten `initial:`. La documentació oficial d'HA diu:

> *«If you set a valid value for `initial` this integration will start with the state set to
> that value. Otherwise, it will restore the state it had before Home Assistant stopping.»*

És a dir: **tal com està ara, cada reinici d'HA retorna tots els llindars al valor de
fàbrica.** Ajustes Δ_ON a 1,6 °C al desembre amb les dades de la Fase B, hi ha un reinici
—i n'hi haurà: desplegaments, talls de llum, actualitzacions del host— i el sistema torna a
2,0 °C **sense dir res**. A l'arxiu es veurà el salt del paràmetre, i serà exactament el
tipus de cosa que costa d'explicar davant d'un pèrit.

**Prova de tres minuts, i es pot fer ara mateix a l'assaig general de casa:**

1. Posa `input_number.delta_td_on` a un valor inconfusible, 3,0.
2. `docker compose restart homeassistant`.
3. Mira si val 3,0 o si ha tornat a 2,0.

> ✅ ***22/09/2026 — llegit al codi de la 2026.9.3*** (`input_number/__init__.py`, dins del
> contenidor): **amb `initial:` arrenca sempre amb aquell valor**; sense, **restaura** l'últim;
> i sense estat previ, pren **el mínim del rang** —la segona de les dues respostes de sota, la
> més agressiva—. La Fase 1 de la [v2](logica-v2-pla.md) treu els `initial:` i un automatisme
> posa els valors de partida **una sola vegada** per paràmetre (`input_number.parametres_versio`).

**Si torna a 2,0** (que és el que diu la documentació), la correcció és treure `initial:` dels
nou helpers. Però abans cal saber **què val un helper sense `initial:` la primera vegada**,
quan encara no té estat previ: si és `unknown`, el `| float` sense valor per defecte del
sensor de decisió fallarà i la decisió passarà a `sense_dades` — que és **fallada segura** i
per tant acceptable; si és el mínim, Δ_ON arrencaria a 1,0 °C, que és **més agressiu** del que
volem. Les dues respostes porten a una acció diferent, i totes dues es comproven al mateix
banc de proves de casa.

### La línia que separa el que va a la web del que va a git

Aquesta és la part del requisit que val la pena escriure bé, perquè és una regla que després
no s'ha de tornar a discutir:

> **A la web hi va el que canvia el COMPORTAMENT del control.
> A git hi va el que canvia el SIGNIFICAT de les dades.**

| Paràmetre | On | Per què |
|---|---|---|
| Δ_ON, Δ_OFF, HR objectiu, marge mínim, T interior mínima, HR exterior de bloqueig | 🌐 **Web** | Són la intenció de l'usuari. Es toquen amb dades a la mà i el sensor de decisió registra amb quin valor va decidir |
| Temps mínims d'engegada i d'aturada | 🌐 **Web** | Igual — **però el de 5 min del compressor va també a l'aparell**, que és on és rígid |
| Mode del soterrani i caducitat del manual | 🌐 **Web** | És operació del dia a dia |
| **Desplaçaments de calibratge** | 📦 **Git** | Canvien el valor de totes les mesures derivades. Ja hi són, i el fitxer ho diu: «canviar un calibratge ha de ser un acte deliberat, datat i revisable» |
| **Paràmetres del filtratge (R1)** | 📦 **Git** | Canvien quines mostres existeixen. És el cas més clar de tots |
| `purge_keep_days`, exclusions del `recorder` | 📦 **Git** | Poden destruir la sèrie, i en silenci |
| **Quines entitats entren a l'arxiu** | 📦 **Git** — en un fitxer de configuració de `nit.py`, mai encastat al codi | Ja decidit a `decisio-stack.md` |
| Noms d'entitat, fórmula de Magnus | 📦 **Git** | Un canvi parteix la sèrie |

### I el «temps entre enviaments»? Són dues coses, i van a llocs diferents

- **Cada quant el sensor reporta** (Tapo → hub → HA, i el node ESPHome quan hi sigui): això
  **canvia la densitat de la prova**. Va a git, i possiblement ni tan sols és configurable —
  amb Matter ho fixa la subscripció, i **està per veure** què negocia HA amb el hub H110.
- **Cada quant el sistema pot actuar** (`min_on_ventilador`, `min_off_ventilador`,
  `min_off_deshumidificador`): això és comportament. Va a la web, i **ja hi és**.

### El que falta perquè el requisit estigui complet

1. **Que el valor vigent en un moment donat es pugui saber després.** Els `input_number` són
   entitats amb històric: n'hi ha prou amb **no excloure'ls mai del `recorder`** i
   **incloure'ls a la llista d'entitats que exporta `nit.py`**. Sense això, la pregunta *«quin
   llindar hi havia el 3 de gener?»* no té resposta, i és una pregunta que es farà.
2. **Validació creuada que un helper sol no pot fer.** `min:`/`max:` impedeixen valors
   suïcides, però no impedeixen **Δ_OFF ≥ Δ_ON**, que trenca la histèresi i fa repicar el
   relé. El sensor de decisió ho ha de detectar i passar a `bloquejat` amb motiu
   «paràmetres incoherents», més un avís. Són deu línies i eviten que una edició al mòbil a
   les tres de la matinada quedi vigent tot l'hivern.
3. **Una targeta al panell amb els paràmetres i la data de l'últim canvi**, i el registre
   filtrat als helpers. És el que converteix «algú va tocar alguna cosa» en una línia amb
   data.

### Decisions que queden obertes

| Decisió | Dada que la desbloqueja |
|---|---|
| Treure `initial:` o no | La prova de reinici de tres minuts, al banc de casa |
| Si cal un valor de seguretat quan un helper és `unknown` | Què val un helper sense `initial:` la primera vegada |
| Si la subscripció Matter deixa triar la cadència de report | Quan el hub estigui emparellat i reportant |

---

## R3 — Veure-ho tot junt i poder-ho correlar

> *«Hauríem de ser capaços de tenir una molt bona visibilitat per correlar temperatura, HR,
> punt de rosada, quan els aparells s'han endollat, previsió del que passarà i realitat del
> que passa.»*

### Això no és cosmètica: és la mesura que pot respondre la pregunta del projecte

La incògnita més cara del projecte és **per on entra l'aire de reposició** (tasca 0.1 de
[fases.md](fases.md)): si entra per fissures en contacte amb el terreny, els ventiladors
poden estar **empitjorant** les humitats i el projecte canvia de naturalesa.

La prova de fum la respon un dia. **La correlació la respon cada dia, i sola:**

> Si l'aire ve del carrer, el punt de rosada del soterrani ha de **seguir** el de l'exterior
> amb un retard i una amortiguació mesurables. Si el `Td` del soterrani ignora olímpicament
> el `Td` exterior durant setmanes amb els ventiladors en marxa, **l'aire no ve del carrer**.

I això es pot mesurar **a la Fase B, sense tocar res**: amb els ventiladors en el règim actual
—que és el que la clàusula QUINTA obliga a mantenir— n'hi ha prou amb la correlació creuada
amb retard entre les dues sèries. Cap relé, cap risc, i la resposta a la pregunta més cara del
projecte com a subproducte de mirar bé les dades.

**Aquesta és la raó de fons d'R3**, i és molt més forta que «que es vegi bonic».

### Què ha de compartir eix de temps

Punts de rosada (tres del soterrani, planta baixa, exterior) · ΔTd · marge de condensació ·
temperatures i HR crues · **watts** del deshumidificador i, a la Fase C, dels ventiladors ·
estat i motiu de `sensor.decisio_del_soterrani` · mode i paràmetres vigents · precipitació de
l'estació oficial · **previsió** · i els **esdeveniments anotats a mà**.

### En viu: els panells natius, i el que honestament no poden fer

**El que sí:** targetes `history-graph` apilades amb la **mateixa finestra de temps**. Quatre
targetes —rosades, temperatures i marge, HR, potència— més el registre del sensor de decisió,
donen correlació visual per eix compartit. Zero peces noves, i és el 80 % del que es mira el
dia a dia.

> ✅ *(21/09/2026)* **La de potència ja hi és**, a la vista *Històric* amb les mateixes 48 h que
> la resta. Els kWh i els euros per hora i per tram són a la vista nova *Consum* →
> [subministraments.md](../local/subministraments.md#el-cost-a-home-assistant).

**El que no:** una sola targeta nativa amb **dos eixos** (°C i W), bandes ombrejades sobre els
episodis de ventilació, la previsió superposada a la realitat i anotacions datades. Barrejar
°C i % en una targeta és directament enganyós: comparteixen eix Y.

### En profunditat: a casa, contra els CSV arxivats

És el que ja diu [decisio-stack.md](decisio-stack.md) («si cal per al dossier, viu al portàtil
de casa contra els CSV») i **no afegeix cap peça al local**, que és el que el fa acceptable.

**La proposta concreta, i és un canvi de calendari:** el guió de gràfics del dossier —tasca
D.1, prevista per al gener— **s'avança a la Fase B**. El motiu és dur:

> Un gràfic que no es pot fer al gener és un requisit que s'ha descobert tard. Si al novembre
> descobrim que per pintar les bandes de ventilació ens falta una entitat que ningú gravava,
> encara hi som a temps. Al gener, no.

Joc de gràfics estàndard: (1) Td interior i exterior superposats amb les bandes de ventilació
i una tira de color amb la decisió; (2) marge de condensació contra la línia dels 3 °C;
(3) watts i litres/dia; (4) **previsió contra realitat**; (5) els tres punts del soterrani
superposats — el gràfic que diu si la humitat és **general o localitzada**, que és la pregunta
pericial.

### 🔴 La previsió: l'única part que no té arreglada a posteriori

Una previsió només val si es guarda **en el moment en què es va fer**. Al gener no es pot
reconstruir què deia el model el 12 de novembre.

I hi ha un detall tècnic que ho fa menys automàtic del que sembla: des de 2024 les previsions
**ja no són atributs** de l'entitat `weather`; s'obtenen cridant el servei
`weather.get_forecasts`. Per tant no n'hi ha prou amb gravar l'entitat del temps: cal un
sensor de plantilla **per disparador** que cada hora demani la previsió, en calculi el punt de
rosada i el deixi **com a estat**, que és el que el `recorder` sap gravar. *(A verificar
contra la 2026.9.3 abans d'escriure-ho.)*

Horitzons proposats: **+3 h, +12 h i +24 h**, de T i HR → Td. Tres entitats, poc volum.

Serveix per a tres coses, i cap és decorativa:

1. **Mesurar si la previsió encerta** aquí, en aquest carrer. Si encerta, la Fase C pot
   **avançar-se**: ventilar abans que la finestra es tanqui val hores.
2. **Al dossier**, poder ensenyar que el sistema preveia i encertava.
3. **Una comprovació de plausibilitat més** del sensor exterior, que ja en té una contra
   l'AEMET.

### L'altra lectura de «previsió»: què esperava el sistema que passés

A més del temps, hi ha la predicció **pròpia**: el sistema decideix ventilar esperant un
efecte. Val la pena registrar l'**eficàcia** de cada episodi —quant s'ha mogut el `Td`
interior per hora de ventilació— i comparar-la amb el que el model de mescla diria. Si
ventilar no mou l'agulla, o l'aire no ve d'on ens pensem, o el cabal és una altra cosa que la
placa diu. És el mateix raonament de dalt, i a la Fase C es fa episodi a episodi.

### Quan s'han «endollat» els aparells: watts, no relés

Regla ja establerta a [monitoritzacio.md](monitoritzacio.md), i per a la correlació importa
més que enlloc: les bandes d'un gràfic surten de la **potència**, no de l'estat de l'endoll.
«L'endoll estava tancat» no diu si el compressor anava; 470 W sí. I els dos codis del Qlima
—**P1** desgebratge i **P2** dipòsit ple— es veuen com a **anomalies a la sèrie de potència**:
endollat i consumint poc. Correlar-los amb la temperatura del soterrani és la manera de saber
quantes hores de gener es passa descongelant-se en comptes d'assecar.

### El quadern de la sèrie — i aquí es tanca el cercle amb R1

Falta la capa que cap sensor dona: **els esdeveniments externs**. Pluja forta, obres a la
façana, la porta oberta dues hores, el deshumidificador mogut de lloc, una visita al local…
i **«el dia 3 vaig agafar el sensor del fons»**.

És la resposta correcta a la meitat de la família 1 d'R1: el pic d'agafar un sensor **no s'ha
d'esborrar, s'ha d'explicar**. Un pic anotat val més que un pic desaparegut, i costa una línia
de text.

**Proposta:** un fitxer pla al repositori, `docs/domotica/diari-de-la-serie.md`, una línia per
esdeveniment amb data, hora i descripció. Zero peces, es versiona, i el guió de gràfics el pot
llegir per posar-hi les anotacions. Amb la regla de sempre: **sense noms ni dades personals**.

### Decisions que queden obertes

| Decisió | Dada que la desbloqueja |
|---|---|
| Si les previsions surten de Met.no, de l'AEMET o de totes dues | Quina dona HR per hores de manera utilitzable a la 2026.9.3 |
| Quants horitzons es graven | Volum real per dia un cop es vegi (surt barat, però es mesura) |
| Si el guió de gràfics acaba sent matplotlib a casa o alguna cosa més simple | Com es vegi el primer joc de gràfics amb dades reals |
| Si mai caldrà un panell per a tercers | Si un pèrit o un advocat ho demana. Mentre la resposta sigui «encara no», no s'hi munta res |

---

## Com s'afegeix un requisit aquí

1. S'escriu amb les paraules de qui el demana, citades.
2. Es diu **per què importa en aquest projecte concret** — si la resposta és «perquè queda
   bé», probablement no entra.
3. Es diu **què no té arreglada a posteriori**, que és l'única urgència real que hi ha.
4. Es diu **quina dada el desbloqueja** i a quina fase toca.
5. S'apunta a [pendents.md](../pendents.md) i, si canvia el pla, a [fases.md](fases.md).
