# Inventari d'aparells

> **Buit de moment.** Aquesta taula s'ha d'omplir amb una visita al local. És el primer
> lliurable real del projecte de domòtica: sense saber què hi ha i com es controla, no es
> pot planificar res.

## Ja instal·lat al local

| Aparell | Quantitat | Ubicació | Marca / model | Com es controla | Integrable? |
|---|---|---|---|---|---|
| Sistema de ventilació forçada | 2 | Soterrani | *pendent* | *pendent* | *pendent* |
| Split (aire condicionat) | *pendent* | *pendent* | *pendent* | Comandament IR | *pendent* |
| **Deshumidificador** | *pendent* | Soterrani | *pendent* | *pendent* | *pendent* |
| Il·luminació | *pendent* | *pendent* | — | Interruptor | *pendent* |
| Quadre elèctric | 1 | *pendent* | *pendent* | — | — |

**Què cal anotar de cadascun:** marca i model exactes, si es controla per interruptor de
paret, per comandament IR o per app, consum aproximat, i si té connexió Wi-Fi pròpia.

## Per comprar (candidats, res decidit)

| Què | Per a què | Notes |
|---|---|---|
| Sensors de temperatura i humitat | El nucli del cas de les humitats i de l'automatisme del punt de rosada | Diversos punts del soterrani i de la planta baixa |
| Sensor d'humitat de paret / superfície | Distingir condensació de capil·laritat | Cal investigar què hi ha d'assequible |
| Relé o endoll intel·ligent per a la ventilació | Registrar i automatitzar l'estat dels 2 ventiladors cap a l'exterior | Ha de mesurar consum, per saber si el ventilador realment gira |
| **Endoll amb mesura de consum** per al deshumidificador | **Objectiu explícit de l'usuari**: veure'n el consum i comprovar si l'automatisme l'estalvia | És la xifra que valida tot el projecte |
| **Sensor exterior de T i HR** | Calcular el punt de rosada exterior — sense això no hi ha automatisme | Ha de resistir la intempèrie |
| Sensor d'inundació | Alerta | Soterrani |
| Controlador IR | Controlar els splits | Els splits ja porten comandament IR |
| Càmera | Seguretat i observació | Vegeu sota |

## Maquinari ja investigat

### Càmera TP-Link Tapo C200

Es va investigar en una conversa anterior (per observar els patrons de moviment d'un animal petit).
**Cal confirmar si era per al local.** El que es va concloure:

- Grava a **targeta microSD**: contínuament 24/7 **o** només quan detecta moviment; totes
  dues opcions són possibles.
- Suporta **RTSP / ONVIF** → el flux es pot enviar a un PC, NAS o a **Home Assistant /
  Frigate** i guardar-lo fora de la càmera.
- **Visió nocturna IR fins a ~9 m.**
- Detecció de moviment amb **sensibilitat ajustable**, i avisos al mòbil.
- Alimentació **per corrent**, no per piles.
- Dubte que va quedar obert: si els nivells de sensibilitat baixos són suficients per
  detectar un animal petit.

**Encaix en aquest projecte:** el suport RTSP/ONVIF la fa integrable amb Home Assistant
sense dependre del núvol, cosa que encaixa amb el principi de *local first*.
