# Domòtica del local — objectius

## L'objectiu d'alt nivell

> **Fer treballar la ventilació natural en lloc del deshumidificador sempre que l'aire
> exterior assequi, i tenir-ho tot mesurat.**

Es concreta en dues coses, i totes dues compten igual:

### 1. Control automàtic dels aparells

- **Ventiladors cap a l'exterior governats pel punt de rosada.** Comparar el punt de rosada
  **interior** amb l'**exterior**: si l'aire de fora és més sec en termes absoluts, ventilar
  i prou; si no, tancar i deixar fer el deshumidificador. L'objectiu explícit és **estalviar
  energia del deshumidificador**.
- **Paràmetres ajustables sense tocar codi:** llindars, histèresi, horaris.
- **Possibilitat de forçar coses a mà:** engegar o aturar un aparell saltant-se
  l'automatisme, sense que l'automatisme hi lluiti en contra.

### 2. Monitorització de dades

- **Consum del deshumidificador** — és la xifra que diu si l'automatisme funciona.
- Dades de **cada sensor**: temperatura i humitat relativa dels diversos punts.
- **Punts de rosada** calculats, interior i exterior.
- **Quan s'endeguen i s'aturen els ventiladors**, i quantes hores acumulen.
- El detall exacte del que es registra **es definirà més endavant**. El que ja sabem ara és
  que **cal una manera de visualitzar-ho**.

### Accés des de fora

Home Assistant viurà **al local**, però l'usuari no hi és sempre. Cal poder consultar les
dades i actuar **des de PC i des del mòbil**, des de fora de la xarxa del local. ✅ **Resolt:
Tailscale**, connectat el 20/09/2026 i **única via** d'accés — el CGNAT de la SIM descarta la
resta. → [acces-remot.md](acces-remot.md)

## El motiu de fons: les humitats

Aquest projecte no és només confort. La clàusula QUINTA de l'escriptura fa recaure sobre el
comprador la condensació derivada de **manca de ventilació imputable a ell** després del
lliurament, i hi ha una **retenció de 3.000 € que venç cap al març de 2027** per determinar
l'origen de les humitats. → [humitats.md](../local/humitats.md)

La defensa és tenir **dades**: un històric que demostri que la ventilació ha estat operativa
i que tot i així hi ha humitat és l'element més fort contra la tesi de la condensació. I la
mateixa instrumentació que serveix per a l'automatisme serveix per a això:

- Registre continu de temperatura i humitat relativa al soterrani, a la planta baixa i a
  **l'exterior**.
- Registre de l'estat i les hores de funcionament dels dos sistemes de ventilació forçada.
- Correlació amb la pluja i la humitat exterior: si la humitat puja quan plou, apunta a
  **filtració**; si és constant i independent de la ventilació, apunta a **capil·laritat**.
- Idealment, **temperatura superficial de les parets** afectades: si la superfície està per
  sobre del punt de rosada i tot i així hi ha humitat, no és condensació.

## Altres usos, més endavant

Ús previst del local: **magatzem i zona d'oci**.

- Control dels **splits** (el venedor recomana fer-los ventilar 10 min cada matí).
- **Il·luminació** i escenes.
- **Seguretat i presència**: càmera, detecció de moviment, avisos al mòbil.
- **Alertes**: tall de llum, inundació, humitat per sobre de llindar.

## Principis

- **Local first.** Res que depengui d'un núvol per funcionar. El sistema ha de seguir
  operatiu si cau Internet; l'accés remot pot caure, l'automatisme i el registre no.
- **Les dades són el producte.** Històric llarg i exportable. El valor probatori depèn de
  tenir sèries contínues i datades, no de tenir un dashboard bonic.
- **Barat i incremental.** Primer sensors i registre, després actuadors, després confort.
- **Res que no es pugui forçar a mà.** Si l'automatisme falla, l'aparell s'ha de poder
  engegar igualment.

## Estat

**Ja no és fase zero.** A **20 de setembre de 2026**:

- **Hi ha maquinari comprat i actiu:** hub Tapo H110, 5 sensors T/HR, sensor d'inundació,
  endoll amb mesura de consum i 2 relés encara sense instal·lar. → [inventari.md](inventari.md)
- **Hi ha codi escrit:** ~1.450 línies, i la lògica del punt de rosada sencera viu a
  `config/packages/rosada.yaml`. El servidor **corre**: Home Assistant 2026.9.3 sobre Linux
  Mint, amb la versió fixada. → [home-assistant.md](home-assistant.md)
- **Les decisions d'eines, llenguatges i interfícies estan preses**, no obertes. Manen a
  [decisio-stack.md](decisio-stack.md); [arquitectura.md](arquitectura.md) n'és l'índex
  d'estat i [fases.md](fases.md) el calendari amb les portes de test.

El que queda obert és **físic i de calendari**: portar-ho tot al local, el pas a la SIM, i
les 4 setmanes de mesura de la Fase B.
