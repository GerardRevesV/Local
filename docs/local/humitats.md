# Humitats — el tema obert

> **Data límit: ~9 de març de 2027.** És quan venç la retenció de 3.000 €. Fins llavors cal
> **determinar i documentar l'origen de les humitats**.

## Què va passar

Durant una visita al local al juny de 2026, poc abans de la signatura, van aparèixer
**humitats a diverses parets del soterrani**. El contracte que hi havia damunt la taula
contenia una exoneració genèrica de responsabilitat del venedor basada en la ventilació, i
es va renegociar.

La preocupació concreta de la part compradora: que no fos **condensació** (responsabilitat
seva si no ventila) sinó **capil·laritat, filtració o defecte estructural** (responsabilitat
del venedor o de la comunitat).

## Versió del venedor

Transmesa per escrit durant la negociació, en resum:

- La clàusula de ventilació la va posar perquè tenia previst **tallar el subministrament
  elèctric**, i volia que el comprador el reconnectés ràpid.
- Amb ocupació de persones —i més encara si s'hi passa la nit— el cos genera humitat i, en
  un soterrani sense ventilar, apareix **condensació**.
- Recomanació: mantenir sempre engegats els sistemes de **ventilació forçada** i, si hi ha
  ocupació de diverses persones, **programar els ventiladors dels splits** perquè facin
  circular l'aire uns **10 minuts cada matí**, sobretot a l'estiu.

## Què diu l'escriptura (clàusula QUINTA)

Text efectivament signat, en resum fidel:

- Es fa constar que **el soterrani compta amb dos sistemes de ventilació** que, *segons
  manifesta la part venedora*, es troben en correcte estat de funcionament i **han de
  romandre operatius** per evitar condensacions derivades d'un tancament prolongat.
- La part compradora exonera la venedora dels danys que derivin **exclusivament** de la manca
  de ventilació **imputable a la compradora i posterior al lliurament de la possessió**.
- **Aquesta exoneració NO arriba a:**
  1. Els danys o defectes **existents abans de la transmissió**.
  2. Un eventual **defecte estructural o constructiu** que impedeixi la ventilació adequada
     del soterrani.
  3. Els **vicis que la part venedora conegués i no hagués manifestat**.

Aquestes tres excepcions són el nucli de la protecció aconseguida: l'exoneració només
cobreix la condensació per mal ús propi.

## La retenció

| Camp | Valor |
|---|---|
| Import | **3.000,00 €** |
| Termini | **6 mesos màxim** des del 09/09/2026 → **~09/03/2027** |
| Finalitat | Temps estimat per ambdues parts per **determinar l'origen de les humitats** |
| Ús | La part compradora pot deduir-ne les despeses en què hagi incorregut per resoldre els problemes d'humitat, **exhibint les factures** al venedor |

Acord final, després d'una negociació: 3.000 € i 6 mesos. El punt de partida, al fitxer privat
(`docs/privat/identificacio.md`, *Preu i pagaments*).

> **Límit conegut:** si el cost de reparació supera la retenció, recuperar la diferència ja
> no és automàtic — depèn de les excepcions de la clàusula QUINTA i, si cal, de reclamar.

## Context de l'edifici: ITE desfavorable

L'informe **ITE de l'edifici, de febrer de 2020**, va resultar **DESFAVORABLE**. Entre les
deficiències detectades hi ha, de manera repetida, **humitats**:

- **Estructura horitzontal:** corrosió d'elements metàl·lics, amb biguetes degradades per
  humitat procedent de la coberta en un dels habitatges.
- **Humitats per filtracions en murs de tancament**, documentades en **diversos habitatges
  de plantes diferents**: humitat interior en mitgeres, taques i humitats actives en sostres
  d'habitacions tocant a mitgera i a la façana principal, i humitats antigues ja seques en
  plantes baixes de l'escala.
- **Coberta:** identificada com a **origen d'humitats**, amb pintura provisional aplicada
  com a pedaç.
- Mesures cautelars executades a estructura vertical, horitzontal, de coberta i d'escales.

*(El detall per habitatge consta a l'informe original i al fitxer privat; no s'aboca aquí
perquè afecta terceres persones.)*

**Per què importa:** documenta que l'edifici té un historial d'humitats per filtració
anterior a la compra. Reforça l'argument que les humitats del local poden no ser
condensació, i connecta amb la responsabilitat de la **comunitat** (vegeu
[comunitat.md](comunitat.md)).

> **Matís important:** a l'escriptura la part compradora **va exonerar el venedor d'aportar
> la documentació ITE**. Això afecta la reclamació *documental*, no les excepcions de la
> clàusula QUINTA ni l'evicció i sanejament.

## Pla obert

1. **Determinar l'origen** abans del març de 2027: condensació vs. capil·laritat vs.
   filtració vs. defecte estructural. Idealment amb un **informe tècnic** (mesurament
   d'humitat en parets, termografia) que deixi constància datada.
2. **Monitoritzar-ho amb dades.** És exactament el que ha de fer el projecte de
   [domòtica](../domotica/objectius.md): sensors de temperatura i humitat relativa,
   registre continu, correlació amb l'estat de la ventilació forçada. Que la ventilació
   hagi estat operativa i tot i així hi hagi humitat **només compta en les hores que l'aire de
   fora era més sec que el de dins**: ventilar amb aire més humit mulla, i la ventilació en
   continu ho fa a l'estiu. La prova més directa és la **temperatura de la paret**: si no
   arriba al punt de rosada i és molla, no és condensació. Les tres formes de l'argument, a
   [objectius.md](../domotica/objectius.md#el-motiu-de-fons-les-humitats).
3. **Seguir la derrama de la façana** de la comunitat: si la impermeabilització resol les
   filtracions, apunta a causa comunitària; si no, apunta a capil·laritat del soterrani.
4. **Conservar factures** de qualsevol actuació: són el mecanisme pactat per deduir de la
   retenció.
