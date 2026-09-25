# Conveni de noms d'entitat

> **Fase A.8.** S'ha de fixar **abans d'emparellar o renombrar res**, i després no es toca.

## Per què això és seriós

Un canvi d'`entity_id` **parteix la sèrie històrica**. Home Assistant no reanomena l'històric:
crea una entitat nova i l'antiga es queda morta amb les dades velles dins. En un informe
pericial, **un salt inexplicat a la sèrie és una esquerda**, i arreglar-ho a posteriori vol
dir editar la base de dades a mà.

Els noms que posa sol l'integrador són del tipus `sensor.t315_a4c138_temperature`. Això no és
un nom: és un número de sèrie. Si un dia es reempara el dispositiu, canvia.

## La regla

```
sensor.<zona>_<punt>_<magnitud>
```

| Part | Valors permesos |
|---|---|
| `zona` | `soterrani` · `baixa` · `exterior` |
| `punt` | `fons` · `centre` · `gran` · *(buit si la zona té un sol punt)* |
| `magnitud` | `temperatura` · `humitat` · `rosada` · `bateria` · `potencia` · `energia` · `cost` |

Les **derivades de calibratge** afegeixen un sufix al nom de la seva germana, i res més:
`_calibrada` a la humitat crua (`sensor.soterrani_fons_humitat` →
`sensor.soterrani_fons_humitat_calibrada`) i `_cru` al punt de rosada, que ja és calibrat
(`sensor.planta_baixa_punt_de_rosada` → `sensor.planta_baixa_punt_de_rosada_cru`). Per això
la planta baixa surt com a `baixa_` en l'una i `planta_baixa_` en l'altra: cadascuna segueix la
seva germana *(23/09/2026)*.

## Taula d'entitats

> ⚠️ **Dues d'aquestes taules les llegeix un guió** *(23/09/2026)*. La porta 2 de
> [`scripts/inicia-serie.sh`](../../scripts/inicia-serie.sh) treu d'aquí quines entitats han
> d'existir abans de començar la sèrie: les `sensor.*_temperatura` i `*_humitat` de **Sensors
> d'ambient**, i les `*_humitat_calibrada` i `*_punt_de_rosada` de **Derivades — les calcula
> `packages/rosada.yaml`**. Cada `entity_id` sencer i entre backticks, dins de la taula (una
> abreviatura com «*i `centre`*» no hi compta), i els dos títols de secció com són. Si la
> lectura no quadra —dues crues per cada calibrada i per cada punt de rosada—, el guió s'hi
> nega en lloc de mirar-ne menys.

### Sensors d'ambient — font: **Matter** (hub H110 via `matter-server`)

| Aparell | Ubicació | `entity_id` de temperatura | `entity_id` d'humitat |
|---|---|---|---|
| Tapo T315 | Soterrani, fons | `sensor.soterrani_fons_temperatura` | `sensor.soterrani_fons_humitat` |
| Tapo T315 | Soterrani, centre | `sensor.soterrani_centre_temperatura` | `sensor.soterrani_centre_humitat` |
| Tapo T310 | Soterrani, gran | `sensor.soterrani_gran_temperatura` | `sensor.soterrani_gran_humitat` |
| Tapo T315 | Planta baixa | `sensor.baixa_temperatura` | `sensor.baixa_humitat` |
| Tapo T310 | Exterior | `sensor.exterior_temperatura` | `sensor.exterior_humitat` |

### Temperatura de superfície — font: ESPHome

| Aparell | Ubicació | `entity_id` |
|---|---|---|
| DS18B20 | Paret freda 1 | `sensor.soterrani_paret_1_superficie` |
| DS18B20 | Paret freda 2 | `sensor.soterrani_paret_2_superficie` |

### Actuadors i mesura — font: **Matter** (vegeu la nota de sota)

| Aparell | Funció | `entity_id` |
|---|---|---|
| Tapo P110M | Deshumidificador | `switch.deshumidificador` · `sensor.deshumidificador_potencia` · `sensor.deshumidificador_energia` |
| Tapo S110E | Ventilador 1 — soterrani, **fons** | `switch.ventilador_1` · `sensor.ventilador_1_potencia` · `sensor.ventilador_1_energia` |
| Tapo S110E | Ventilador 2 — soterrani, **sala gran** | `switch.ventilador_2` · `sensor.ventilador_2_potencia` · `sensor.ventilador_2_energia` |
| Tapo T300 | Inundació | `binary_sensor.soterrani_inundacio` |

**L'endoll en publica nou més**, que Matter bateja sol i que en renombrar el dispositiu han
quedat amb el mateix prefix: `sensor.deshumidificador_effective_voltage` i
`…_effective_current` (tensió i corrent), `…_energy_exported`,
`select.deshumidificador_power_on_behavior` —el **comportament després d'un tall**, que ha
d'estar en `on`—, `update.deshumidificador_microprogramari`, `button.deshumidificador_identifica`
i tres sensors de diagnòstic desactivats. **No són al conveni perquè no els fa servir ningú**;
hi consten perquè existeixen i perquè la decisió sobre tensió i corrent és oberta.

**Els dos S110E en publiquen els mateixos**, amb el prefix `ventilador_1_` i `ventilador_2_`
*(26/09/2026, nodes 10 i 11)*. Amb una diferència que és a posta: el seu
`select.ventilador_N_power_on_behavior` és a **`off`** —després d'un tall, **apagats** (C.6)—, al
revés que el de l'endoll.

> **La nota, que fins avui faltava (21/09/2026).** Que la font sigui Matter vol dir que
> l'aparell ha de **parlar Matter**: el hub **H110** i els **S110E** sí, i l'endoll també,
> perquè és un **P110M** i no un P110 pelat — confirmat pel que anuncia a la xarxa
> ([inventari.md](inventari.md)).
>
> ✅ **Tots renombrats** (verificat el 21/09/2026): els **sis del hub** i, amb l'emparellament
> de l'endoll, els **dotze del P110M**. La casella A.8 queda tancada per al maquinari que hi
> ha avui; queden els **S110E** de la Fase C.
>
> ⚠️ Matter bateja les entitats amb el model i un tros d'identificador
> (`sensor.tapo_p110m_power`). **Es renombren immediatament**, abans que gravin res, i es
> canvia l'**ID d'entitat**, no només el nom visible. Procediment:
> [emparellar-matter.md](emparellar-matter.md).
>
> ❓ **Tensió i corrent no són al conveni a posta.** Un endoll amb mesura també les publica, i
> no fan falta per a res del projecte. Queda per decidir si entren a `exclude.entities` del
> `recorder` (mai per glob) o si s'accepten i s'obliden → [pendents.md](../pendents.md).

### El deshumidificador per `tuya-local` — fixat el 21/09/2026, ABANS d'afegir-lo

> ✅ **Aplicat el mateix 21/09/2026:** afegit a les 18:57 i **les dotze entitats renombrades a
> les 18:59**, abans que gravessin res que valgués la pena. El dispositiu es diu
> *Deshumidificador Qlima*. La taula de sota és la definitiva.

El Qlima D825 parla en local per `tuya-local` (tasca B.1c,
[inventari.md](inventari.md#decisió-no-integrem-el-deshumidificador-per-tuya--es-reobre-provar-tuya-local)).
És **el mateix aparell** que alimenta el P110M, i per això comparteix el prefix
`deshumidificador`: el domini ja diu qui és qui.

| `entity_id` | Què és |
|---|---|
| `humidifier.deshumidificador` | **L'aparell**: engegat, **llindar d'HR** (35–80 %, de 5 en 5), mode (`auto` · `normal` · `sleep` · `laundry`), i l'HR que mesura ell (atribut `current_humidity`) |
| `sensor.deshumidificador_temperatura` | La temperatura que mesura ell (°C, en enters) |
| `binary_sensor.deshumidificador_avaria` | Avaria (codi de falla a l'atribut `fault_code`). ✅ **El P2 hi surt: codi 32**, dipòsit ple o tret (21/09/2026). El P1, per veure |
| `fan.deshumidificador` | La velocitat del ventilador |
| `select.deshumidificador_mode_aire` | Deshumidificar · purificar · totes dues |
| `switch.deshumidificador_silenci` · `_nit` · `_assecat_intern` | Configuració de l'aparell |
| `select.deshumidificador_indicadors` · `_temporitzador` | Configuració de l'aparell |
| `lock.deshumidificador_bloqueig_infantil` | El bloqueig dels botons |
| `sensor.deshumidificador_temps_restant` | El que queda del temporitzador (min) |

> **Les de configuració es graven, a posta.** Pensàvem desactivar el que no es fes servir, però
> un canvi de mode, de silenci o de nit **explica** un canvi de rendiment, i aquestes entitats
> només escriuen quan algú les toca: cap volum.
>
> ❓ **El P1, i la 106 i la 107.** El P2 ja se sap que és el codi 32 del `fault_code`. L'aparell
> publica dues dades que la configuració del D820A no coneix (les **106** i **107**, totes dues
> a 0) i que **no es van moure amb el dipòsit**. Podrien ser el desgebratge o la bomba →
> [pendents.md](../pendents.md).

> ⚠️ **Dos amos no.** Al principi, d'aquest aparell **només es llegeix i s'ajusta el llindar**.
> Qui l'engega i l'atura per a la lògica segueix sent `switch.deshumidificador`, el P110M. Que
> el `humidifier` mani també és una decisió que es prendrà a posta, no per accident.
>
> ✅ ***22/09/2026 — presa, a posta:*** amb la lògica v2 **mana el `humidifier`**, pel llindar,
> i l'endoll **només mesura** i queda sempre encès. Segueix havent-hi un sol amo: ha canviat
> quin → [decisio-stack.md](decisio-stack.md).
>
> ⚠️ `tuya-local` bateja les entitats amb el nom del dispositiu i el de la funció en anglès.
> **Es renombren el mateix moment d'afegir-lo**, abans que gravin res, com es va fer amb el
> P110M ([runbook](runbook-servidor.md#-renombrar-entitats-sense-tocar-storage)).

### Derivades — les calcula `packages/rosada.yaml`

| `entity_id` | Què és |
|---|---|
| `sensor.soterrani_fons_punt_de_rosada` · `sensor.soterrani_centre_punt_de_rosada` · `sensor.soterrani_gran_punt_de_rosada` | Punt de rosada de cada punt, **calibrat** |
| `sensor.planta_baixa_punt_de_rosada` · `sensor.exterior_punt_de_rosada` | Punt de rosada, **calibrat** |
| `sensor.soterrani_fons_humitat_calibrada` · `sensor.soterrani_centre_humitat_calibrada` · `sensor.soterrani_gran_humitat_calibrada` · `sensor.baixa_humitat_calibrada` · `sensor.exterior_humitat_calibrada` | L'HR amb la correcció de `custom_templates/calibratge.jinja`, i l'atribut `calibratge` amb la versió. **És la que miren els gràfics** i la HR màxima; la crua (`*_humitat`) no es toca mai i segueix a l'històric *(23/09/2026)* |
| `sensor.soterrani_fons_punt_de_rosada_cru` · `sensor.soterrani_centre_punt_de_rosada_cru` · `sensor.soterrani_gran_punt_de_rosada_cru` · `sensor.planta_baixa_punt_de_rosada_cru` · `sensor.exterior_punt_de_rosada_cru` | El punt de rosada **sense** calibrar. **Només per depurar**: cap decisió no el mira *(23/09/2026)* |
| `sensor.soterrani_punt_de_rosada_de_referencia` | **Referència interior** = la més alta dels tres punts |
| `sensor.dtd_interior_exterior` | `soterrani_rosada − exterior_rosada` — el criteri |
| `sensor.marge_de_condensacio` | `paret més freda − soterrani_rosada` — el KPI del fong |
| `sensor.residu_del_punt_de_rosada_exterior` | Sensor propi − estació oficial — **salut del sensor** |
| `sensor.decisio_del_soterrani` | **L'únic punt d'avaluació.** Què s'ha de fer i per què. *(Des de la Fase 1 de la v2, a `packages/control.yaml`: vegeu més avall)* |

### Derivades — consum i tarifa, les calcula `packages/consum.yaml`

*(21/09/2026.)* Totes surten del comptador de l'endoll i del calendari de
[`tarifa.jinja`](../../config/custom_templates/tarifa.jinja). El perquè de cada decisió és a
[subministraments.md](../local/subministraments.md#el-cost-a-home-assistant).

| `entity_id` | Què és |
|---|---|
| `sensor.tarifa_periode` | Tram d'ara: `punta` · `pla` · `vall` |
| `sensor.tarifa_preu` | Preu del kWh d'ara, **amb impostos** (`EUR/kWh`); l'atribut `sense_impostos` diu el del contracte |
| `sensor.deshumidificador_cost` | **Euros acumulats**, una mostra cada 5 minuts (només si el comptador s'ha mogut). No es reinicia mai: el dia i el mes els fan les estadístiques. Als atributs hi ha la referència de l'última mostra |
| `sensor.deshumidificador_energia_punta` *(i `_pla`, `_vall`)* | kWh acumulats **en cada tram**. La pregunta de l'optimització: quina part del consum cau en punta |

> ⚠️ **`sensor.deshumidificador_cost` no es pot renombrar sense tocar el codi:** les variables
> del bloc el llegeixen pel seu `entity_id` —encara no hi ha `this`—. `comprova.sh` avisa si
> desapareix.
>
> Durant el calibratge (i fins que no s'endolli al local), el «deshumidificador» d'aquests
> noms és **el que hi hagi endollat**. El nom és el de la funció de l'endoll, com sempre.

### Paràmetres ajustables

`input_number.` : `delta_td_on` · `delta_td_off` · `hr_objectiu` · `marge_superficie_min` ·
`t_int_minima` · `hr_ext_bloqueig` · `min_on_ventilador` · `min_off_ventilador` ·
`min_off_deshumidificador`

`input_select.mode_soterrani` · `timer.override_manual`

> 🔄 **22/09/2026 — la lògica v2 en canvia la llista.** `hr_objectiu` i
> `min_off_deshumidificador` **surten** amb la Fase 1 (el seu històric es queda); la resta
> segueix amb el mateix nom i passa a `packages/control.yaml`. Els nous són a la secció de sota.

### La lògica v2 — fixats el 22/09/2026, ABANS de crear-los

Surten de [logica-v2-pla.md](logica-v2-pla.md), fase per fase. Les plantilles noves porten
`default_entity_id`, o sigui que **el nom no depèn del nom visible**: és aquest. ⚠️ Només la
primera vegada: si el nom ja era pres, HA hi posa `_2` i se'l queda per sempre.
`comprova.sh` canta cada `default_entity_id` que no hi sigui tal qual.

**Fase 1 — la decisió en ombra** (`packages/control.yaml`, i les dues de física a `rosada.yaml`)

| `entity_id` | Què és |
|---|---|
| `sensor.decisio_del_soterrani` | **El mateix de sempre**, amb la v2 a dins (mateix `unique_id`). Atributs nous: `llindar`, `mode_aparell`, `velocitat`, `ventiladors`, `urgencia`, `dtd`, `referencia`, `tram`, `llindar_tram`, `higiene_pendent`, `actuacio`, `versio` i `entrades` |
| `sensor.decisio_llindar_deshumidificador` | El llindar que la decisió vol a l'aparell (%). *No es toca* = no disponible |
| `binary_sensor.decisio_ventiladors` | Si la decisió vol els ventiladors engegats. *No es toquen* = no disponible |
| `sensor.ventilacio_minuts_avui` | Minuts de ventilació d'avui: els que la decisió **hauria** fet mentre és en ombra; els dels relés quan actua (Fase 3) |
| `sensor.dtd_interior_planta_baixa` | `soterrani_rosada − planta_baixa_rosada`: el ΔTd contra l'altra referència |
| `sensor.soterrani_humitat_maxima` | La HR **calibrada** més alta dels tres punts —el màxim de les tres `*_humitat_calibrada`—; el punt, a l'atribut `punt` |
| `input_select.referencia_ventilacio` | *Planta baixa* · *Exterior* |
| `input_boolean.actuacio_deshumidificador` · `…_ventiladors` | Els dos interruptors del mode ombra: **apagats**, no s'actua |
| `input_number.parametres_versio` | Fins a quina versió s'han posat els valors de partida (cada fase que afegeix paràmetres, un bloc) |
| `input_number.hr_vall` · `hr_pla` · `hr_punta` · `hr_fix` · `hr_urgencia` · `hr_urgencia_objectiu` · `hr_mentre_ventila` · `delta_td_higiene` · `renovacions_dia` · `renovacions_absencia` · `cabal_ventiladors` · `volum_soterrani` | Els paràmetres nous |

**Fase 2 — dades i gràfics** (`packages/deshumidificador.yaml`; la dispersió a `rosada.yaml` i els euros per tram a `consum.yaml`)

| `entity_id` | Què és |
|---|---|
| `sensor.soterrani_dispersio_rosada` | Td més alt − Td més baix dels tres punts |
| `sensor.deshumidificador_humitat` | L'HR que mesura l'aparell, **només amb el ventilador en marxa** |
| `sensor.deshumidificador_estat` | `compressor` · `ventilador` · `espera` · `apagat` · `diposit` · `avaria` · `sense_corrent`, pels watts i el codi d'avaria |
| `binary_sensor.deshumidificador_compressor` | Compressor en marxa (> 150 W) |
| `sensor.deshumidificador_hores_compressor` | Hores de compressor acumulades (els minuts, en enters, a l'atribut `minuts`) |
| `sensor.deshumidificador_hores_funcionament` | Hores amb compressor o ventilador (≥ 5 W): les que compten per al filtre |
| `sensor.deshumidificador_hores_filtre` · `input_number.deshumidificador_filtre_netejat` · `script.deshumidificador_filtre_netejat` | Hores des de l'última neteja del filtre (avís a les 360 h) |
| `sensor.deshumidificador_cost_punta` · `…_pla` · `…_vall` | Euros acumulats en cada tram |

**Fase 3 — actuació** (`packages/control.yaml`; els relés, a `custom_templates/ventiladors.jinja`)

| `entity_id` | Què és |
|---|---|
| `input_boolean.ventilador_1_virtual` · `…_2_virtual` | Els relés de mentida, fins als S110E |
| `binary_sensor.ventiladors_en_marxa` | Si algun relé de la interfície és encès (i, amb els S110E, si consumeix) |
| `sensor.ventiladors_potencia` | Suma dels watts dels relés; no disponible mentre siguin virtuals |
| `script.ventiladors_engega` · `script.ventiladors_atura` | L'**única** porta cap als relés |
| `script.deshumidificador_aplica` | Porta l'aparell a la configuració de la decisió, verificant cada pas |
| `input_number.ventiladors_max_minuts` | Cap engegada més llarga que això |

## Com s'apliquen

1. A Home Assistant: **Configuració → Dispositius i serveis → Entitats**, buscar l'entitat i
   canviar-li l'**ID d'entitat** (no només el nom visible).
2. Fer-ho **abans** que l'entitat tingui històric que valgui la pena.
3. Deixar el nom visible en llenguatge natural («Soterrani — fons, temperatura») i l'`entity_id`
   segons la taula.

> ⚠️ **Un cop fixat, no es toca.** Si cal canviar-ne un, es documenta la data del canvi a
> [pendents.md](../pendents.md) perquè el forat de la sèrie quedi explicat i no sembli
> manipulació.

## Per què la referència interior és el **màxim** i no la mitjana

`sensor.soterrani_punt_de_rosada_de_referencia` pren **el punt de rosada més alt dels tres punts del soterrani**, no
la mitjana. Dues raons:

1. **La condensació és local.** Condensa allà on l'aire més humit troba la superfície més
   freda. Una mitjana amaga precisament el racó que té el problema.
2. **És el criteri conservador.** Si ventilem quan el pitjor punt millora, millorem tots. Amb
   la mitjana podríem ventilar mentre el racó dolent empitjora.

Els tres punts es registren igualment per separat: la **diferència entre ells** és el que dirà
si la humitat és general o localitzada.
