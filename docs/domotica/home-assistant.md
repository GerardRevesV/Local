# Home Assistant — muntatge del servidor

## Estat actual (20 de setembre de 2026)

**En curs:** preparant un **pen drive amb Linux Mint** per instal·lar-lo en un **portàtil
secundari**, que farà de servidor de Home Assistant.

- [x] Decidit: el servidor serà un portàtil que ja es té, no un Raspberry Pi ni un NUC nou.
- [x] Decidit: sistema operatiu base **Linux Mint**.
- [ ] Gravar el pen drive amb l'ISO de Linux Mint.
- [ ] Arrencar el portàtil des del pen drive i instal·lar Mint.
- [ ] Instal·lar Home Assistant (mètode per decidir, veure sota).
- [ ] Accés a la interfície i primer arrencada.
- [ ] Decidir on viu el servidor físicament (casa o local) i com s'hi accedeix.

> Aquesta llista s'ha d'anar marcant a mesura que avanci.

## Decisió pendent: com instal·lar Home Assistant

Hi ha quatre maneres i **no són equivalents**. Com que la base és Linux Mint, això
condiciona:

| Mètode | Add-ons | Notes |
|---|---|---|
| **HA OS** (bare metal) | Sí | El sistema operatiu *és* Home Assistant. Es menja tot el disc: incompatible amb tenir Mint a sota. |
| **HA Supervised** | Sí | Oficialment només sobre **Debian** net. Linux Mint **no** és una base suportada. |
| **HA Container** (Docker) | **No** | Suportat i senzill sobre qualsevol Linux, Mint inclòs. Sense add-ons: cada servei extra (Mosquitto, Zigbee2MQTT, base de dades) es munta com a contenidor a part. |
| **HA Core** (venv de Python) | No | El més manual. Poc recomanable. |

**Camí recomanat amb Mint: HA Container sobre Docker.** Es perd la botiga d'add-ons, però
tot el que els add-ons donen es pot muntar com a contenidors amb `docker compose`, que a més
és més fàcil de versionar en aquest repositori.

> Si el que es vol és l'experiència completa amb add-ons, l'alternativa és instal·lar
> **Debian** al portàtil en comptes de Mint i fer-hi **HA Supervised**, o dedicar el portàtil
> sencer a **HA OS**. Val la pena decidir-ho *abans* d'instal·lar Mint.

⚠️ Aquesta taula s'ha de **verificar contra la documentació oficial actual** abans de
decidir res: els mètodes d'instal·lació de Home Assistant canvien.

## Coses a tenir resoltes abans de començar a codificar

- **On viu el servidor.** Si el que es vol monitoritzar és el local, el servidor (o com a
  mínim els sensors i un gateway) ha de ser **al local**, amb Internet i alimentació estable.
- **Alimentació.** El portàtil té bateria pròpia: fa de SAI improvisat davant talls de llum,
  i pot **registrar el tall**, cosa rellevant per demostrar que la ventilació estava operativa.
- **Arrencada automàtica.** El portàtil ha d'arrencar sol després d'un tall (BIOS: *restore
  on AC power loss*) i no suspendre's en tancar la tapa.
- **Accés remot.** Sense obrir ports a Internet. Opcions: VPN (WireGuard/Tailscale) o Nabu
  Casa. **Pendent de decidir.**
- **Còpies de seguretat.** Les dades històriques són el motiu del projecte; perdre-les és
  perdre'l. Còpia automàtica fora del portàtil.
- **Retenció de l'històric.** El `recorder` de Home Assistant purga per defecte al cap de
  **10 dies**. Per a l'ús d'aquest projecte cal **allargar-ho molt** (mesos o anys) i
  probablement moure la base de dades a PostgreSQL o afegir **InfluxDB**. És un dels primers
  ajustos que caldrà fer, no un detall posterior.

## Registre d'instal·lació

Aquí s'anirà anotant què s'ha fet realment, amb data.

| Data | Què |
|---|---|
| 20/09/2026 | Preparant el pen drive amb Linux Mint |
