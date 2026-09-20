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
| `magnitud` | `temperatura` · `humitat` · `rosada` · `bateria` · `potencia` · `energia` |

## Taula d'entitats

### Sensors d'ambient — font: integració `tplink`

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

### Actuadors i mesura — font: integració `tplink`

| Aparell | Funció | `entity_id` |
|---|---|---|
| Tapo P110 | Deshumidificador | `switch.deshumidificador` · `sensor.deshumidificador_potencia` · `sensor.deshumidificador_energia` |
| Tapo S110E | Ventilador 1 | `switch.ventilador_1` · `sensor.ventilador_1_potencia` |
| Tapo S110E | Ventilador 2 | `switch.ventilador_2` · `sensor.ventilador_2_potencia` |
| Tapo T300 | Inundació | `binary_sensor.soterrani_inundacio` |

### Derivades — les calcula `packages/rosada.yaml`

| `entity_id` | Què és |
|---|---|
| `sensor.soterrani_fons_punt_de_rosada` *(i `centre`, `gran`)* | Punt de rosada de cada punt |
| `sensor.planta_baixa_punt_de_rosada` · `sensor.exterior_punt_de_rosada` | Punt de rosada |
| `sensor.soterrani_punt_de_rosada_de_referencia` | **Referència interior** = la més alta dels tres punts |
| `sensor.dtd_interior_exterior` | `soterrani_rosada − exterior_rosada` — el criteri |
| `sensor.marge_de_condensacio` | `paret més freda − soterrani_rosada` — el KPI del fong |
| `sensor.residu_del_punt_de_rosada_exterior` | Sensor propi − estació oficial — **salut del sensor** |
| `sensor.decisio_del_soterrani` | **L'únic punt d'avaluació.** Què s'ha de fer i per què |

### Paràmetres ajustables

`input_number.` : `delta_td_on` · `delta_td_off` · `hr_objectiu` · `marge_superficie_min` ·
`t_int_minima` · `hr_ext_bloqueig` · `min_on_ventilador` · `min_off_ventilador` ·
`min_off_deshumidificador`

`input_select.mode_soterrani` · `timer.override_manual`

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
