# Monitorització i visualització — proposta

> **Estat: proposta, no decidida.**

## La premissa que canvia les prioritats

Això no és una instal·lació domòtica que, a més, guarda dades. És **un registre amb data
límit (9/03/2027)** que, a més, encén coses. Tres conseqüències:

1. **Hi ha coses que no es poden recuperar a posteriori.** Les estadístiques a llarg termini
   només s'acumulen des del moment que l'entitat existeix i està ben declarada. Les dades
   crues purgades no tornen. **Cada setmana de retard és història irrecuperable.**
2. **La redundància val més que la sofisticació.** Dues còpies en formats lletjos superen
   una base de dades elegant i única.
3. **El destinatari final no és Home Assistant.** És un pèrit o un advocat. El format que
   compta és un **CSV i un gràfic en PDF**, no un fitxer `.db`.

## ⚠️ Les dues coses que s'han de fer ABANS del primer sensor

Són les úniques que **no es poden arreglar més endavant**:

### 1. `purge_keep_days: 730`

El `recorder` purga als **10 dies** per defecte. Per a aquest projecte això és directament
destructiu. Cal configurar-ho **abans** que entri cap dada.

### 2. Convertir l'estat dels ventiladors en números

**Aquest és el forat que es descuida tothom.** Les estadístiques a llarg termini
(que no es purguen mai) només existeixen per a entitats amb `state_class` i unitat. Un
`switch` o un `binary_sensor` —ventilador encès/apagat— **no en genera cap**. Passats els
dies de retenció, **la prova que la ventilació estava operativa s'esborra**.

I això és exactament el nucli de la defensa contra la clàusula QUINTA.

La solució: sensors **`history_stats`** (hores/dia de funcionament) i **`utility_meter`**
(kWh acumulats), tots dos amb `state_class`. Així la ventilació queda registrada com a
magnitud numèrica que sobreviu per sempre.

> **A més:** mesura **watts, no relés**. «El relé estava tancat» és feble. «El ventilador va
> consumir 45 W durant 18 h/dia els 140 dies» és una prova. Per això l'endoll de la
> ventilació ha de mesurar consum.

## Base de dades

| | A favor | En contra |
|---|---|---|
| **SQLite** (per defecte) | Zero manteniment; un sol fitxer, còpia trivial; cap dependència: si tota la resta falla, HA segueix gravant | Vulnerable a corrupció en apagada bruta; la purga no allibera espai sense `VACUUM`; **Grafana no hi pot consultar** |
| **MariaDB** | El camí més trepitjat de la comunitat HA | Un contenidor més, credencials, còpia pròpia |
| **PostgreSQL** | Igual de suportat; `pg_dump` net; **Grafana hi consulta directament**; porta oberta a TimescaleDB | Menys receptes copiables que MariaDB |

**Recomanació: PostgreSQL des del dia 1.** No perquè SQLite no aguanti el volum —l'aguanta
de sobres— sinó perquè **migrar el febrer de 2027, amb el termini a sobre, és exactament el
que no vols fer**.

> ⚠️ **Risc nou que introdueix un motor extern:** si el contenidor de la base de dades no
> arrenca, **HA no grava res** i no te n'assabentes fins que obres el gràfic. SQLite no té
> aquest mode de fallada. Mitigació obligatòria: `depends_on` + `restart: unless-stopped`,
> i una **automatització sentinella** que avisi si un sensor clau porta hores sense
> actualitzar-se.

## Estadístiques a llarg termini: què conserven i què no

Per a entitats amb `state_class: measurement` es guarden **min, max i mitjana per hora, per
sempre**. Però tenen **tres forats, i els tres importen aquí**:

1. **Els binaris no en tenen.** → vegeu l'apartat anterior. És el crític.
2. **La mitjana horària amaga l'episodi de condensació.** El discriminant tècnic és si la
   **temperatura superficial de la paret baixa per sota del punt de rosada interior**, i això
   passa en episodis de 20–60 minuts, sovint de matinada. Una mitjana horària el pot amagar
   o inventar. Per a la condensació **cal resolució crua**.
3. **Un canvi d'`entity_id` trenca la sèrie.** Si es reempara un dispositiu Zigbee i surt
   `..._2`, l'històric queda partit — i un salt inexplicat en un informe pericial és una
   esquerda. **Noms definitius el dia 1:** `sensor.soterrani_nord_temperatura`, no
   `sensor.aqara_a4c138_temperature`.

## InfluxDB i companyia: **no**

- **InfluxDB:** no aporta res que Postgres + Grafana no doni a aquesta escala, i afegeix una
  canonada, una còpia de seguretat més i risc de migració de versió (1.x→2.x→3.x han estat
  trencadors). **Grafana sí, InfluxDB no**: Grafana consulta Postgres directament.
- **VictoriaMetrics:** millor que Influx si algun dia cal un segon magatzem, però el problema
  no és el volum.
- **TimescaleDB / `ltss`:** bones peces, problema equivocat.
- **Prometheus:** eina equivocada (és *pull*, retencions curtes, i els esdeveniments
  discrets hi encaixen malament).
- **Exportació CSV periòdica:** modesta i **guanyadora** per a la part legal. És l'únic
  format que un pèrit obrirà sense demanar res.

## Volum: no és el problema

Supòsits: ~12 entitats de clima, 4 punts de rosada, 2 ventiladors amb estat i potència, 1
comptador del deshumidificador, cadència de 5 minuts (un soterrani té molta inèrcia;
mostrejar més sovint és soroll car).

| Magnitud | Estimació |
|---|---|
| Files crues/any | ~2,5–3,5 milions |
| **Base de dades crua, 1 any** | **~0,5–1 GB** |
| Base de dades crua, els 2 anys del cas | ~1–2 GB |
| Estadístiques horàries, per any | ~15–25 MB (no es purguen mai) |
| **CSV d'un any sencer, comprimit** | **~10–15 MB** |

**Tot el corpus probatori d'un any cap en un adjunt de correu.** Això elimina d'entrada el
*downsampling*, les polítiques de retenció i bona part de l'argument a favor d'InfluxDB.

> ⚠️ **L'única excepció:** un mesurador de potència que reporti cada 5–10 s genera ell sol
> més files que tots els sensors de clima junts (+600 MB/any). Cal limitar-ne la cadència o
> filtrar per delta.

**El que és car aquí no és l'espai: és la disciplina.** Les dades es perden per una purga mal
configurada, per un `state_class` que faltava, per un `entity_id` renomenat o per una còpia
que feia mesos que fallava en silenci. No per manca de disc.

## Dashboards natius vs Grafana

Els natius basten per al dia a dia, i tenen una cosa que Grafana no té: **l'app Companion al
mòbil**, amb notificacions, per VPN i sense exposar res. Ja donen `history-graph`,
`statistics-graph` (amb bandes min/mitjana/màx per a la vista de dos anys), el panell
d'**Energia** per al deshumidificador, i alertes.

**Grafana només guanya en quatre coses, i totes arriben a la fase de dossier:**

1. **Superposar unitats diferents amb doble eix** — el gràfic que decideix el cas és
   *temperatura superficial de la paret* + *punt de rosada interior* + *HR* + *estat del
   ventilador* en un sol eix temporal.
2. **Anotacions:** marcar sobre la sèrie «pluja forta 14/11», «derrama de façana executada»,
   «ventilador avariat 3 dies». Una cronologia anotada converteix dades en relat.
3. Rangs llargs sense ofegar el navegador.
4. **Compartir una vista de només lectura amb un pèrit** sense donar-li accés a HA, i
   exportar-la en PDF amb aspecte d'informe.

> **Regla: Home Assistant per viure-hi, Grafana per litigar-hi.**

## Còpies de seguretat i integritat

Són **dos problemes diferents**.

### Que no es perdi

Amb HA Container **no hi ha Supervisor i per tant no hi ha botó de *Backup***. La còpia te
la fas tu. Regla 3-2-1.

- **Cada nit:** còpia consistent en calent (`pg_dump`, o `VACUUM INTO` amb SQLite) + `tar`
  del volum de configuració. **Mai copiar el `.db` amb `cp` amb HA en marxa**: amb WAL actiu
  la còpia pot sortir inconsistent.
- **Una còpia fora del local:** disc extern al local **i** sincronització xifrada a casa o
  al núvol. Un incendi o un robatori al local no poden costar el cas.
- **Prova una restauració una vegada, al principi.** Una còpia que no s'ha restaurat mai no
  és una còpia, és una esperança.
- **Vigila-la:** notificació diària al mòbil. Una còpia que fa sis mesos que falla en silenci
  és el mode de fallada més comú i el més car.

### Que un tercer s'ho cregui

- **Rellotge:** NTP actiu, zona `Europe/Madrid`, i no tocar-ho mai més. HA desa en UTC
  internament, cosa que juga a favor.
- **Ritual mensual, el dia 1:** exportar CSV per sensor del mes tancat → comprimir →
  calcular **SHA-256** → guardar el manifest de hashos.
- **Datació per un tercer:** enviar el hash per correu a l'advocat. Un correu amb data de
  servidor en poder d'un tercer és molt més sòlid que qualsevol marca de temps del teu
  portàtil. Un **segell de temps RFC 3161** és barat i és l'estàndard que els pèrits entenen.
- **Documenta els forats.** Un buit inexplicat a la sèrie sembla manipulació; un buit **amb
  un registre que diu «tall de corrent de 03:12 a 05:40, el portàtil va seguir gravant amb
  bateria»** és el contrari: és prova de robustesa.
- **El repositori Git és bon context, no bona datació.** Documenta decisions i metodologia
  —cosa que té valor, perquè mostra procés i no reconstrucció *a posteriori*— però les dates
  dels commits les posa el teu ordinador.

## Recomanació

### Dia 1 — imprescindible

1. **HA Container + PostgreSQL** al mateix `docker compose`.
2. **`recorder` amb `purge_keep_days: 730`**, `commit_interval` elevat i `exclude` del soroll
   (`automation`, `script`, `update`, `sun`, `media_player`…) — **abans del primer sensor**.
3. **`state_class: measurement`** a tota T, HR i punt de rosada.
4. **`history_stats` + `utility_meter`** per a la ventilació. *No és opcional.*
5. **Noms d'entitat definitius** des del primer minut.
6. **Còpia nocturna fora del portàtil**, verificada amb una restauració real i vigilada amb
   una notificació diària.
7. **Ritual mensual CSV + SHA-256** fora del local. Mitja hora de muntatge.
8. **Sentinella:** avís al mòbil si un sensor del cas porta més de 3 h sense reportar.
9. **Dashboards natius** i l'app al mòbil.

### Més endavant

- **Grafana** (tardor/hivern de 2026, en construir el dossier), apuntat a Postgres.
- **Automatització de la ventilació un cop hi hagi línia base.** Canviar el règim de
  ventilació sense saber com era abans **destrueix el grup de control**.
- Splits per IR, il·luminació, càmera. El confort no té data límit.

### La cosa que més val per euro, i no és programari

Un **sensor de temperatura superficial de paret** (un DS18B20 enganxat a la paret i aïllat
per darrere, via ESPHome, val pocs euros) a cada punt humit. És l'únic sensor que
**discrimina directament** condensació de capil·laritat: si la superfície **mai** no baixa
del punt de rosada i tot i així la paret és humida, la tesi de la condensació cau.

Sense aquest sensor, tot l'aparell de monitorització demostra que ventilaves, **però no
demostra què era la humitat**. Amb la correlació amb la pluja (integració meteorològica)
per a la hipòtesi de filtració, queden coberts els tres discriminants.

## Per verificar contra documentació oficial actual

`purge_keep_days` i `auto_purge` per defecte · `commit_interval` per defecte · retenció de
les estadístiques de 5 minuts · esquema vigent de `states`/`states_meta` per a les consultes
de Grafana · botó de descàrrega CSV al panell d'historial · via per llegir l'estat de la
bateria de l'amfitrió (probablement un sensor de línia de comandes sobre
`/sys/class/power_supply/`) · `thermal_comfort` via HACS sobre HA Container · estat de
manteniment d'`ltss`.
