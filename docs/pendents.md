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
- [ ] **Preguntar a l'advocat:** si la condensació que porta la mateixa ventilació —la que la
      clàusula QUINTA obliga a mantenir, i que en continu fa entrar aire humit a l'estiu— queda
      fora de l'exoneració, que només cobreix la manca de ventilació imputable a la compradora.
      I si, un cop automatitzada (Fase C), aturar-la quan l'aire de fora és més humit compta com
      a mantenir-la operativa. → [objectius.md](domotica/objectius.md#el-motiu-de-fons-les-humitats)

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

### 📅 Abans de portar-ho al local — el pla (22–23/09/2026)

*El trasllat, previst per al 23/09 al vespre o el 24/09. El que hi ha aquí és el que **només es
pot fer còmodament a casa**, o el que val més fer abans de desendollar res.*

**Aquesta nit**

- [ ] **Deshumidificador: la prova del dipòsit.** Manual · continu · velocitat alta, dipòsit
      buit, fins que s'atura sol (codi 32). **En acabar, mesurar l'aigua amb una gerra**:
      litres ÷ kWh = el primer punt de la taula del cost per litre. Eina:
      `tools/prova_deshumidificador.py diposit`. ⚠️ L'habitació és petita i ja seca: treurà poc
      i a HR baixa, o sigui que serà un **mínim**, no la xifra del soterrani.
      ✅ ***Primer dipòsit, 22/09:*** Manual · continu (35), compressor **de les ~00:43 a les
      12:57:51**, quan salta el **codi 32** i l'aparell baixa a ~0,8 W (aturat 5 min a les 08:13,
      des de l'aparell). **~12,2 h de compressor i ~4,5 kWh** (2,67 en vall, 0,72 en pla, 1,12
      en punta: **~0,61 €**). HR de l'aparell **46–60 %** (53 % ponderada pel temps) i ~28 °C.
      **La finestra és oberta**, o sigui que asseca aire del carrer i l'HR no cau: no espatlla
      la prova —els litres per kWh depenen de l'aire que entra a l'aparell, no de si l'habitació
      és tancada— i el ⚠️ d'«HR baixa» ja no hi val. Si es tanca, **apuntar-ne l'hora**.
      En saltar el 32, `select.deshumidificador_mode_aire` passa sol de `dehumidify` a
      `dehumidify_and_purify` (12:58:05): mirar si hi torna en buidar-lo.
      **S'atura net i no vessa.** Amb ~3,0–3,2 L tretes: **~0,25 L/h i ~0,67–0,71 L/kWh**;
      €/L per tram, vall ~0,13–0,14 · pla ~0,20–0,21 · punta ~0,33–0,35 → [deshumidificador.md](domotica/deshumidificador.md#9-el-primer-dipòsit-ple--22092026).
      - [x] ~~**La gerra, una sola vegada.**~~ ✅ **Un «ple» són ~3 L**, no els 3,8 nominals: el
            flotador talla cap al 80 %. La safata ja venia gairebé plena de les proves del 21/09:
            l'aigua treta, ~3,0–3,2 L.
      - [ ] **El segon dipòsit**, sense tocar res: de l'hora que es torna a posar buit al proper
            32. Treu el marge de la safata, i ja no cal mesurar-lo:
            `tools/analisi.py diposits --litres 3 3 …` (un valor per dipòsit).
- [ ] **Calibratge: la nit sencera**, i demà la **rampa amb el tàper de sal i la nevera** (el
      tàper fixa el 75 % gairebé a qualsevol temperatura; la nevera hi afegeix el fred de
      l'hivern) → [calibratge.md](domotica/calibratge.md).
      ✅ La nit, i el **tàper al replà** des de les ~05:00 del 22/09 (73 %, 27,8 °C): els
      desplaçaments del 21/09 **no hi valen** i tots cinc semblen llegir **baix** contra la
      sal (provisional) → [el replà](domotica/calibratge.md#el-replà--22092026).
      🔄 **La nevera**: a dins des de les 12:45, ✅ ràdio bé, tapat a les 13:44. ⚠️ La pasta
      sembla més freda que els sensors → **drap a sota i al voltant**. Demà surt **tapat** →
      [tercera tanda](domotica/calibratge.md#tercera-tanda--la-nevera).
      Els graons ja no calen. En acabar: l'anàlisi per replans, `tools/calibratge.py`,
      aplicar els desplaçaments i **apagar el mode calibratge**.
- [ ] ⚠️ **Refer qualsevol calibratge tret amb `--descarrega` abans del 22/09/2026.** L'eina
      demanava l'històric sense `end_time`, i HA en torna només 24 h des de l'inici: amb més
      de 24 h demanades, l'ajust feia servir **només les primeres 24 h** i perdia les rampes
      més recents, sense avís. ✅ Eina corregida el 22/09/2026 →
      [calibratge.md](domotica/calibratge.md#després).

**Demà, a casa**

- [ ] **La bomba, amb el tub de 5 m i una galleda**: que bombi, fins a quina alçada, i si la
      106 o la 107 es mouen quan està activada. Al soterrani serà obligatòria.
- [ ] **L'higròmetre del deshumidificador contra un Tapo ja calibrat**, unes hores de costat.
- [ ] A la pantalla: si el llindar **35 és el «CO»**; el **so de l'alarma** (TIMER + SPEED).
- [ ] **L'assecat intern en apagar** l'aparell.
- [ ] **Smart Life**: si avisa del dipòsit ple i de les avaries.
- [ ] **L'endoll una hora sense internet**: si l'energia s'atura.
- [ ] Decidir la **configuració de repòs** (proposta: Manual · 55 % · velocitat alta · bloqueig
      infantil) i deixar-l'hi abans de portar-lo.
- [ ] **Bateries dels sensors** abans de repartir-los.

**Abans de desendollar res**

- [ ] **La tanda física del portàtil**, si també va al local: BIOS (*restore on AC power loss*,
      límit de càrrega, disc intern primer), cable RJ-45 → *Tanda física*, més avall. Al local,
      cada casella és un viatge.
- [ ] **Còpia de `matter-data/` i de `config/.storage` a casa.** Si el portàtil pateix en el
      trasllat, sense aquestes claus cal reemparellar-ho tot i la sèrie es parteix.
- [ ] **Moure-ho tot amb el mateix router de la SIM**: si la xarxa és la mateixa, no cal
      reemparellar res. Apagar el portàtil net; al local, primer el router, després el hub i
      l'endoll, i el portàtil l'últim.

**Al local**

- [ ] Repartir els sensors segons l'assignació, i `scripts/inicia-serie.sh` per marcar l'inici
      de la sèrie de debò.
- [ ] La **setmana de base**: deshumidificador fix al 55 % i ventiladors com ara
      ([logica-v2.md](domotica/logica-v2.md)).
- [ ] **Fotos de les plaques dels ventiladors**, la **porta de l'escala** i, quan es pugui, la
      **prova de fum**.

### ❓ El que falta per saber — les incògnites del sistema

*Recollides el 22/09/2026 després dels experiments i de la [lògica v2](domotica/logica-v2.md).
S'aniran omplint quan el muntatge sigui estable al local i hi hagi el maquinari que falta. Cada
una diu **com es respon** i **què decideix**: una incògnita que no decideix res no hi és.*

**Ara mateix, a casa (no cal res de nou)**

| Què | Com es respon | Què decideix |
|---|---|---|
| **Litres per kWh** del deshumidificador, i com cauen amb l'HR | Una nit en continu amb el dipòsit buit: l'hora del codi 32 i els kWh, **a partir del segon dipòsit** | Confirma o corregeix la taula del cost per litre, i amb ella els tres llindars |
| Si el llindar **35 és el «CO»** | Mirar la pantalla amb el llindar a 35 | Si el continu de la urgència i de les proves és el que creiem |
| Què fa l'**assecat intern** | Apagar l'aparell amb l'assecat activat i mirar quant va el ventilador | Si val la pena deixar-lo activat al soterrani |
| La **desviació de l'higròmetre** de l'aparell | Un Tapo al costat unes hores, quan acabi el calibratge | Traduir l'objectiu dels racons al llindar de l'aparell (el segon nivell) |
| Si l'**energia del P110M depèn d'internet** | Una hora sense sortida a internet | Si el cost s'atura quan cau la SIM |
| Si **Smart Life avisa** del dipòsit ple i de les avaries | Mirar-ho a l'app (la prova del dipòsit ho hauria disparat) | Si hi ha un avís que funciona encara que HA caigui |
| Si l'**alarma del dipòsit** xiula | El so: TIMER + SPEED alhora; i omplir-lo amb el so actiu | Res greu: el codi 32 ja arriba a HA |
| Quina operació és l'**ECO**, i **velocitat alta o baixa** | Litres per kWh de cadascuna (depèn de la primera fila) | L'operació i la velocitat de la configuració de repòs |
| **La memòria després d'un tall llarg** | Engegat, amb una configuració inconfusible, i 30 min sense corrent; i el mateix apagat | Si HA ha de restaurar-la sempre en tornar el corrent (ja proposat per prudència: el 22/09 va tornar amb la de fàbrica) |
| **Com comptar l'aigua que surt pel tub** | Un **pluviòmetre de balancí**. A priori, **escenari C**: Ecowitt WH40 sense fils → [tres escenaris](domotica/inventari.md#comptar-laigua-i-mesurar-la-paret--tres-escenaris-22092026) | Els litres/dia al soterrani, on amb la bomba no hi ha codi 32. Un cabalímetre normal no serveix: massa poc cabal, a glopades i amb aire |

**Quan el muntatge sigui al soterrani i estable**

| Què | Com es respon | Què decideix |
|---|---|---|
| **Per on entra l'aire** | La prova de fum (tasca 0.1), amb els extractors en marxa | Si ventilar pot mullar: si entra pel terra, la ventilació es reconsidera sencera |
| La **porta de l'escala**, oberta o tancada | Saber-ho, i si cal, mesurar amb totes dues | El cabal, i per on entra l'aire |
| Contra quina **referència** ventilar: planta baixa o exterior | Unes setmanes gravant tots dos ΔTd | `referencia_ventilacio` |
| **Quant aguanta la sequedat** | Les dues setmanes d'experiment amb `hr_vall` al 50 % | Si el pre-assecat surt a compte o es queda al 55 % |
| Si la humitat és **general o localitzada** | Els tres punts del soterrani, calibrats | Si el deshumidificador és al lloc bo, i la idea de remenar l'aire |
| Els **kWh/dia de base** | La setmana de base: 55 % fix i ventiladors com ara | Quant estalvia la v2 |
| Com es mesuren els **litres amb la bomba** | Sense dipòsit no hi ha codi 32: comptador d'aigua, o un recipient de tant en tant | Els litres/dia de la Porta B al soterrani |
| El **límit de dades** de la SIM | Les 72 h de `vnstat` | El pla de dades |

**Quan es compri o s'instal·li**

| Què | Com es respon | Què decideix |
|---|---|---|
| **Models, potència i cabal dels ventiladors** | Les fotos de la placa → [installacions.md](local/installacions.md) | Les renovacions en minuts i el ΔTd en litres per kWh: sense el cabal, els llindars de ventilació són provisionals. I el **balanç d'aigua**: quanta en pot portar la ventilació contra la que treu el deshumidificador → [objectius.md](domotica/objectius.md#el-motiu-de-fons-les-humitats) |
| Els **S110E**: càrrega de motor i temporitzador propi | La fitxa del relé; si els ventiladors van endollats o cablejats | La fallada segura de la ventilació, i si cal instal·lador |
| El **marge de la paret** i quina paret és la més freda | Una sonda a la paret més freda (termòmetre IR de mà per trobar-la). A priori, **escenari C**: dues Ecowitt WN34L sense fils → [tres escenaris](domotica/inventari.md#comptar-laigua-i-mesurar-la-paret--tres-escenaris-22092026) | La urgència de debò: avui mira l'aire, no la paret |
| El **CO₂** (i potser el radó) | Un SCD40; un detector de radó si cal | Renovar per demanda en comptes de per rellotge |

**A l'hivern**

| Què | Com es respon | Què decideix |
|---|---|---|
| El **rendiment a 12–15 °C** i el **desgebratge (P1)** | Les primeres setmanes de fred; mirar quina dada es mou (la 106, la 107?) | Si el deshumidificador aguanta l'hivern, i el cost per litre real |
| La **temperatura mínima** del soterrani | Les sèries d'hivern | `t_int_minima`, i si la resina necessita escalfor |

**Quan arribi la primera factura**: que els **preus i les hores de cada tram** quadrin amb
`tarifa.jinja` (el pendent ja hi és, més avall).

**El servidor** té les seves pròpies incògnites al bloc *Resiliència*, més avall: el BIOS, la
bateria i les còpies.

### 🆕 Lògica v2 — el que falta per decidir-la ([logica-v2.md](domotica/logica-v2.md))

*Proposta del 21/09/2026: llindar del deshumidificador per tram, triat pel cost per litre (vall 55 ·
pla 60 · punta 65, amb el 50 de vall com a experiment),
urgència per sobre del preu, ventilació contra una referència triable (**planta baixa** o
exterior, gravant-les totes dues), i estats d'higiene, impressió i ocupat.*

- [ ] **Models i cabal dels ventiladors** (l'usuari en té fotos) → `installacions.md`.
- [ ] **La porta de l'escala: oberta o tancada**, habitualment. Canvia el cabal i per on entra
      l'aire.
- [ ] **Si els S110E tenen temporitzador propi**, perquè els ventiladors s'apaguin sols si HA
      cau engegant-los.
- [x] ~~**Decidir la v2** i, llavors, codificar-la a `rosada.yaml` amb la rèplica offline.~~ ✅
      **Decidida el 22/09/2026**, i el pla per codificar-la és a
      [logica-v2-pla.md](domotica/logica-v2-pla.md): va a `packages/control.yaml` i a la macro
      `custom_templates/decisio.jinja`, no a `rosada.yaml`. Cada fase, un PR:
  - [x] ~~**Fase 1 — la decisió en ombra**~~ ✅ **Desplegada el 22/09/2026 a les 12:14**, recarregant
        i sense tocar cap aparell → [registre](domotica/home-assistant.md#registre-dinstallació).
  - [ ] **Porta 1**: 24 h de `replica.py --deriva` sense cap discrepància. *(La primera passada,
        just després de desplegar: 2 files, 0 diferències. Amb el calibratge encès la decisió diu
        sempre `calibratge`: la porta de debò es juga quan els sensors siguin al seu lloc.)*
  - [ ] **Fase 2 — dades i gràfics**: hores de compressor i filtre, € per tram, avisos del
        dipòsit i de l'AUTO, vista *Aprendre*, i `tools/analisi.py` a casa. ✅ Codificada
        (22/09/2026). ✅ **Desplegada** el mateix dia. ⏳ **Posar a zero el comptador del filtre**
        (script) el dia que es netegi: les hores van començar a comptar a les 12:14.
  - [x] ~~🐛 **`tools/calibratge.py --descarrega` només rep 24 h**: sense `end_time`, l'API
        d'històric de HA torna 24 h des de l'inici, o sigui **les més antigues** de les 72 que
        demana per defecte. Trobat el 22/09/2026 escrivint `analisi.py`.~~ ✅ **Corregit el
        22/09/2026.** La URL de l'històric ara es construeix en un sol lloc,
        `replica.cami_historic`, que fan servir `calibratge.py`, `replica.py` i `analisi.py`.
        El que queda obert és **refer els ajustos antics** → a dalt, a *Aquesta nit*.
  - [ ] **Fase 3 — actuació, apagada per defecte**: interfície dels ventiladors (relés
        virtuals), executors, i la configuració restaurada quan l'aparell torna del corrent.
        ✅ Codificada i ✅ **desplegada amb els dos interruptors apagats** (22/09/2026). ⏳ Després
        del trasllat: 24 h amb `actuacio_ventiladors` encès sobre els relés de mentida, i unes hores
        amb `actuacio_deshumidificador` encès i algú al davant comptant xiulets.
  - [ ] **La setmana de base**, en mode *Llindar fix* amb `actuacio_deshumidificador` encès.
  - [ ] **Fase 4 — el segon nivell**, quan se sàpiga la desviació de l'higròmetre de l'aparell.
  - [ ] **Fase 5 — els S110E**: un sol canvi, a `custom_templates/ventiladors.jinja`.
- [ ] ❓ **El volum del soterrani**: la v2 fa servir **115 m³** (~46 m² per l'alçada), però
      l'alçada no s'ha mesurat mai. Amb el cabal, és el que converteix renovacions en minuts.
- [ ] 📌 **Filament en caixes estanques amb dessecant**: a un 55 % ja agafa massa humitat.
- [ ] **Provar l'assecat intern apagant l'aparell**, no amb el llindar: amb el llindar no allarga
      els 5 min de ventilador (21/09/2026), i probablement només actua en apagar-lo.

### 🔴 Resiliència — el que falta perquè una caiguda no costi dades ni silenci

*Prioritzat el 21/09/2026.* El deshumidificador ja aguanta sol qualsevol caiguda (torna sol,
recorda la configuració i es controla des de Smart Life); **les dades i els avisos, no**. Anàlisi
sencera a [home-assistant.md](domotica/home-assistant.md#què-passa-si-cau-la-llum-el-portàtil-o-internet).
Per ordre de profit per esforç —cada un té el seu pendent més avall:

1. 🔴 **Avís de caiguda** (healthchecks.io). Avui, si el portàtil cau, **no te n'assabentes**. →
   «Muntar un avís de caiguda», a *Muntatge*.
2. 🔴 **BIOS — *restore on AC power loss***. Sense això, un tall més llarg que la bateria deixa HA
   apagat fins que algú hi vagi. → *Tanda física*.
3. 🔴 **Còpies de seguretat**: `matter-data/` (les claus: sense elles, reemparellar i sèrie
   partida), `config/.storage` i l'històric. Avui un portàtil mort ho perd tot. → «`matter-data/`
   ha d'entrar a la còpia de seguretat», a *Muntatge*, i `nit.py`.
4. ⚠️ **SAI petit per al router i el hub**, perquè un tall curt no sigui un forat. → *El portàtil
   que farà de servidor*.
5. 🆕 **Mirar si l'app Smart Life avisa del dipòsit ple i de les avaries.** Si ho fa, és un avís
   que funciona **encara que HA hagi caigut**.

### 🆕 Requisits definits el 21/09/2026 — [requisits.md](domotica/requisits.md)

Tres coses que el sistema ha de saber fer i que encara **no són decisions preses**. El
raonament sencer, amb el que desbloqueja cadascuna, és a
[requisits.md](domotica/requisits.md). Aquí només hi ha el que s'ha de fer.

- [ ] 🔴 **R2 — Provar si un llindar canviat sobreviu a un reinici d'HA.** Tres minuts al banc
      de casa: posar `input_number.delta_td_on` a 3,0, reiniciar el contenidor i mirar si hi
      segueix. La documentació d'HA diu que amb `initial:` **no** hi segueix, i els nou helpers
      de `rosada.yaml` en porten. Si es confirma, cada reinici esborra l'ajust de tot un
      hivern **sense dir res**.
      *22/09/2026: **confirmat llegint el codi de la 2026.9.3** —amb `initial:` arrenca sempre
      amb ell; sense, restaura; sense estat previ, el mínim del rang—. La Fase 1 de la
      [v2](domotica/logica-v2-pla.md) treu els `initial:` i posa els valors de partida un sol
      cop. La prova del reinici queda com a confirmació, el primer dia que calgui reiniciar.*
- [ ] 🔴 **R2 — Garantir que els `input_number` es graven i s'exporten.** Mai a l'`exclude` del
      `recorder`, i sempre a la llista d'entitats de `nit.py`. Sense això, *«quin llindar
      regia el 3 de gener»* no té resposta.
- [ ] **R2 — Detectar paràmetres incoherents** (Δ_OFF ≥ Δ_ON) al sensor de decisió, amb pas a
      `bloquejat` i avís. Un `min:`/`max:` no ho pot impedir. *(Entra amb la Fase 1 de la v2.)*
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
      **escrita**: `config/packages/rosada.yaml` (469 línies), amb un únic punt d'avaluació,
      `sensor.decisio_del_soterrani`. *(22/09/2026: la decisió passa a
      `config/packages/control.yaml` (1026 línies), amb la lògica v2.)* Node-RED, AppDaemon, pyscript i el servei propi en
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
      humida. 🟡 **Segona tanda, 21–22/09/2026**: tàper amb sal, amb el marcador encès, replà
      al 73 % → [el replà](domotica/calibratge.md#el-replà--22092026). Dispersió de Td 0,61 °C
      sense corregir i 0,40 amb els desplaçaments del 21/09, que **no hi valen**; tots cinc
      semblen llegir baix contra la sal (provisional). ⏳ Falta el punt en fred →
      [tercera tanda, la nevera](domotica/calibratge.md#tercera-tanda--la-nevera).
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
- [x] ~~🆕 **Provar `tuya-local` amb el deshumidificador.**~~ ✅ **Superada el 21/09/2026 a les
      18:57:** el reconeix com a **D820A (89 %)**, en local, i les dotze entitats es van
      renombrar a les 18:59. Reinici d'HA a les 18:49 (9 s), acordat amb l'usuari amb el
      calibratge en marxa. → [inventari.md](domotica/inventari.md#decisió-no-integrem-el-deshumidificador-per-tuya--es-reobre-provar-tuya-local)
      *El que deia mentre es feia:* ✅ **Endollat al P110M** a les 18:15 i ✅ **ja és a la Wi-Fi del router
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
- [x] ~~🆕 **Saber on surt el P2 del deshumidificador.**~~ ✅ **Codi d'avaria 32** (21/09/2026,
      treient, omplint i tornant a posar el dipòsit): `binary_sensor.deshumidificador_avaria`
      a `on` amb `fault_code: 32`, tant **ple** com **tret**. Només es comprova quan
      deshumidifica, no quan purifica. → [deshumidificador.md](domotica/deshumidificador.md#8-el-dipòsit--per-quina-dada-surt-el-p2)
- [ ] 🆕 **Saber on surt el P1 (desgebrant) i què són la 106 i la 107.** No es van moure amb el
      dipòsit. El P1 només es veurà amb fred, al soterrani: mirar-ho el primer dia que el
      compressor passi estona aturat amb el ventilador en marxa i l'HR per sobre del llindar.
- [ ] 🆕 **Una nit sencera per saber els litres per kWh** —la dada de la Porta B que falta per a
      aquest aparell—. Manual i continu, dipòsit buit, i: si s'omple, l'hora del codi 32 i els
      kWh fins llavors donen **~3 L / kWh** sense mesurar res (un «ple» són ~3 L, no 3,8); si
      no, l'aigua del matí amb una gerra. Una hora de compressor el 21/09 no va arribar ni a
      mullar el dipòsit. 🔄 *22/09: primer punt, ~0,67–0,71 L/kWh a 28 °C i 53 %; falta el
      segon dipòsit* → [deshumidificador.md](domotica/deshumidificador.md#9-el-primer-dipòsit-ple--22092026).
- [ ] 🆕 **Mirar a la pantalla si el llindar 35 és el «CO»** del manual (assecar sense parar).
      Es comporta com a tal, però l'aparell hauria de mostrar «CO».
- [ ] 🆕 **Deixar-lo en la configuració de repòs** proposada: **Manual · 55 % · velocitat alta ·
      bloqueig infantil** (i bomba, al soterrani). En AUTO, com venia, HA no el pot governar.
      I, a la Fase C, que HA **la restauri cada cop que arrenqui** → [deshumidificador.md](domotica/deshumidificador.md#si-ha-cau-el-pla-b-ja-hi-és-i-no-demana-programar-res-a-laparell)
- [ ] 🆕 **Decidir si l'HR que mesura el deshumidificador serveix.** És un atribut, no un
      sensor, o sigui que no fa estadístiques; si serveix, cal una plantilla que la tregui. El
      44 % del 21/09 contra el 66–72 % dels sensors **ja és explicat**: era en una altra
      habitació, amb aire condicionat. Per saber si és precís, un dia al costat d'un Tapo.
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
- [x] ~~🔴 **Però: recorda el llindar d'humitat** després d'un cicle d'alimentació?~~ ✅ **Sí.**
      Provat el 21/09/2026 a distància, tallant l'endoll un minut: recorda el mode, el llindar i
      la velocitat, i es reprèn sol. I, de propina, **espera ~5 min abans d'engegar el
      compressor** en tornar el corrent. *(Tasca 0.2b.)* →
      [deshumidificador.md](domotica/deshumidificador.md#2-memòria-la-prova-02b)
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
