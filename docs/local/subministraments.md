# Subministraments

## Electricitat — Naturgy Tarifa Noche ✅ contractada

Contractada. És la modalitat amb **discriminació horària en tres trams** de Naturgy, sobre
els períodes regulats estàndard de la tarifa 2.0TD.

### Franges horàries

| Període | Horari | Preu energia |
|---|---|---|
| 🟢 **Vall (P3)** | **00:00 – 08:00** de dilluns a divendres<br>**24 h els caps de setmana i festius nacionals** | **0,0739 €/kWh** |
| 🟡 **Pla (P2)** | 08:00 – 10:00 · 14:00 – 18:00 · 22:00 – 00:00 (tots els dies) | 0,1092 €/kWh |
| 🔴 **Punta (P1)** | 10:00 – 14:00 · 18:00 – 22:00 (tots els dies) | 0,1822 €/kWh |

### Terme de potència

| Període | Horari | Preu |
|---|---|---|
| Punta | 08:00 – 00:00 de dilluns a divendres | 0,123030 €/kW·dia |
| Vall | 00:00 – 08:00 de dilluns a divendres + caps de setmana | 0,061562 €/kW·dia |

> Preus **sense impostos**, vigents a data de consulta (setembre de 2026) segons la pàgina
> oficial de Naturgy i Selectra. **S'actualitzen periòdicament: cal rellegir-los abans de
> fer servir les xifres per a res que importi.** Sense permanència, preus fixos per franja
> durant 12 mesos.

### Què vol dir això per al codi

**La punta és 2,47 vegades la vall.** Això és molt, i canvia el disseny del control:

- **El deshumidificador hauria de treballar preferentment en vall**, és a dir de matinada
  entre setmana i **tot el cap de setmana sencer**. Un compressor de 300–700 W en punta
  costa gairebé dues vegades i mitja el mateix en vall.
- **Els ventiladors**, en canvi, consumeixen poc (30–150 W) i el criteri que els governa és
  físic, no econòmic: si l'aire de fora asseca, ventilar surt a compte sempre. El preu no
  hauria de vetar una finestra de ventilació bona.
- Això **es combina bé amb la física**: la finestra de ventilació gratuïta a Barcelona és
  sobretot de **nit**, que és justament la franja vall. Les dues lògiques empenyen en la
  mateixa direcció.
- **Cal registrar el període tarifari com a entitat a Home Assistant** (hi ha integracions i
  plantilles que ho fan) per poder calcular el cost real i no només els kWh. És la xifra
  que dirà si l'automatisme val la pena.

> ⚠️ **A verificar:** la potència contractada del local i si el contracte és el domèstic de
> Tarifa Noche o una variant per a negocis. Amb ≤ 15 kW la 2.0TD aplica igual.

## Internet — router amb targeta SIM

L'accés a Internet del local serà per **router amb targeta SIM** (dades mòbils).

### Conseqüències, i n'hi ha de grosses

**1. CGNAT pràcticament garantit.** Les connexions mòbils gairebé sempre van darrere CGNAT
i amb IP dinàmica. Això **resol per si sol** la comparativa d'[accés remot](../domotica/acces-remot.md):

- ❌ **Port forwarding + reverse proxy: impossible.** Descartat definitivament, no per
  preferència sinó per física de xarxa.
- ❌ **WireGuard pur amb el servidor al local: impossible** sense un VPS intermediari.
- ✅ **Tailscale: funciona.** És exactament el seu cas d'ús. Farà *hole punching* i, si no
  pot, caurà a relé xifrat.
- ✅ **Nabu Casa / Cloudflare Tunnel: funcionen**, perquè la connexió la inicia el local cap
  enfora.

**2. El consum de dades passa a comptar.** Fins ara no era una variable; ara sí:

- El registre de sensors i les automatitzacions són **locals**: gasten zero dades.
- El que gasta és l'**accés remot** (cada cop que obres l'app), les **actualitzacions** de
  Home Assistant i dels contenidors, i sobretot **qualsevol càmera** — el vídeo es menja una
  tarifa de dades en dies.
- Si Tailscale no aconsegueix connexió directa i cau a relé, **tot el trànsit passa dues
  vegades** per la xarxa mòbil.
- Les **còpies de seguretat fora del local** (que la proposta de
  [monitorització](../domotica/monitoritzacio.md) considera imprescindibles) han de tenir en
  compte el volum: una base de dades d'1 GB pujada cada nit no és viable per SIM. Solució:
  còpies **incrementals** i **exportacions CSV mensuals comprimides** (~10–15 MB l'any
  sencer), que és precisament el que ja es recomanava.

**3. Fiabilitat.** Un router 4G/5G pot penjar-se i necessitar un cicle d'alimentació. Això
reforça l'argument de l'**endoll intel·ligent de rearmada** alimentant el router,
independent de Home Assistant.

### Per decidir

- [ ] Operadora, pla de dades i **límit mensual**.
- [ ] Model de router: si té Ethernet (cal per a un coordinador Zigbee en xarxa i per a un
      ESP32 amb PoE), i si té *watchdog* de reconnexió.
- [ ] Cobertura mòbil al local — i especialment **al soterrani**, on probablement no n'hi
      haurà: el router ha d'anar a la planta baixa.
- [ ] Si l'operadora ofereix IP pública fixa com a extra (algunes ho fan per pocs euros).
      No és necessari amb Tailscale, però simplifica.

## Aigua

Sense dades. **Pendent de verificar** l'estat del comptador i del contracte.
