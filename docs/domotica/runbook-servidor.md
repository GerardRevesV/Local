# Runbook — muntar el servidor de zero

> **Per a què serveix:** refer aquesta màquina sencera si es mor el disc, si cal canviar de
> portàtil, o si d'aquí a dos anys ningú recorda com estava muntada. Conté **les ordres
> exactes**, què hi ha instal·lat i **els paranys que ens van costar temps**.
>
> Escrit el **20/09/2026**, el dia que es va muntar. Les decisions de fons són a
> [`decisio-stack.md`](decisio-stack.md); això és el *com*, no el *per què*.

## Temps real que va costar

Unes 4 hores, i gairebé tot va ser esperar descàrregues i trobar tres paranys. Refet amb
aquest document al davant, hauria de ser **poc més d'una hora**.

---

## 1. Què cal tenir abans de començar

| | |
|---|---|
| Portàtil | Acer TravelMate B3 TMB311-32-C4JR — vegeu [home-assistant.md](home-assistant.md#el-maquinari-del-servidor) |
| Pen drive | ≥ 4 GB, **que s'esborrarà** |
| ISO | Linux Mint 22.x, 64 bits |
| Gravadora | **Rufus** (GPT / UEFI) o balenaEtcher — **mai copiant l'ISO com un fitxer** |
| Xarxa | **Fibra o banda ampla de casa.** Vegeu l'avís de les dades, més avall |
| Comptes | GitHub, Tailscale (el mateix compte que duri fins al final del projecte) |

> ⚠️ **No muntis això sobre la SIM del local.** Entre la imatge d'HA (3,43 GB) i les
> actualitzacions del sistema (434 paquets en una instal·lació nova) se'n van uns **5 GB**.
> Tot el muntatge es fa a casa i després es porta la màquina.

---

## 2. BIOS

`F2` picada repetidament des del moment d'encendre. És un **InsydeH2O**.

| Pestanya | Opció | Valor |
|---|---|---|
| Main | `F12 Boot Menu` | **Enabled** ← *sense això el pen drive no arrenca mai* |
| Boot | Ordre | `USB HDD` a dalt mentre s'instal·la; **el disc intern a dalt després** |
| Boot | `Secure Boot` | Es deixa **activat**: Mint hi arrenca bé |
| Information | — | Apuntar CPU, RAM i model de disc |

Sortir desant: `F10`. **`Alt`+`F10` no**: és la recuperació d'Acer i esborra el disc.

---

## 3. Instal·lar Mint

Doble clic a *Install Linux Mint*. Les quatre pantalles que importen:

1. **Teclat** — provar-lo al quadre de text. Si t'equivoques, la contrasenya que posis després
   quedarà amb símbols diferents dels que creus.
2. **Tipus d'instal·lació** → *Esborra el disc i instal·la Linux Mint*.
3. 🔴 **Cap xifratge.** Ni del disc sencer, ni de la carpeta personal:
   - Disc xifrat → la màquina arrenca i **espera una contrasenya** que al local no escriurà ningú.
   - Carpeta xifrada → `~/Local/config` **no existeix** fins que algú inicia sessió, i HA arrenca sense configuració.
4. **Zona horària `Madrid`**, usuari i contrasenya que recordis, nom de màquina reconeixible.

En acabar: treure el pen drive i tornar l'ordre d'arrencada al disc intern.

---

## 4. L'única línia que s'escriu al teclat del portàtil

```bash
sudo apt install -y openssh-server && sudo systemctl enable --now ssh && hostname -I
```

A partir d'aquí **tot es fa des de l'altre ordinador**. Apunta la IP que t'ha dit.

### Clau SSH, des del PC de casa

```bash
ssh-keygen -t ed25519 -C "casa->local-ha" -f ~/.ssh/id_local -N ""
```

```bash
cat ~/.ssh/id_local.pub | ssh usuari@LA-IP "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

Demana la contrasenya **un cop**. Després, un àlies a `~/.ssh/config` perquè no calgui recordar res:

```
Host local-ha
    HostName 100.x.y.z        # la IP de Tailscale un cop la tingui; abans, la de LAN
    User <usuari>
    IdentityFile ~/.ssh/id_local
    IdentitiesOnly yes
    ServerAliveInterval 30
```

> **Per què la IP de Tailscale i no la de LAN:** la de LAN només val mentre les dues màquines
> comparteixin xarxa. La de Tailscale val sempre, també quan el portàtil sigui al local.

---

## 5. Sistema al dia i guió de preparació

Amb `-t`, que `sudo` ha de poder demanar la contrasenya:

```bash
ssh -t local-ha "sudo apt update && sudo apt full-upgrade -y && cd ~/Local && git pull && bash scripts/prepara-host.sh"
```

[`scripts/prepara-host.sh`](../../scripts/prepara-host.sh) és **idempotent**: es pot tornar a
executar sempre. Fa, per ordre:

| | Què | Per què |
|---|---|---|
| 1 | `openssh-server`, `git`, `curl` | La via d'entrada |
| 2 | Zona horària + NTP + `systemd-time-wait-sync` | Un CMOS mort injectaria files datades el 2015 al mig de la sèrie |
| 3 | Emmascarar `sleep/suspend/hibernate` + `HandleLidSwitch=ignore` | Un servidor que dorm és un forat a l'històric |
| 4 | **Docker CE del repositori oficial** | El de Mint va endarrerit i el de snap trenca els volums |
| 5 | `SystemMaxUse=200M` al journal | Que els logs no s'empassin el disc |
| 6 | Apagar el Bluetooth | No s'usa, i HA omple el log d'errors intentant-hi accedir |
| 7 | `unattended-upgrades` només seguretat, a les 04:30, **sense Docker** | Una actualització no planificada és un forat a l'històric |
| 8 | Tailscale | L'única via d'entrar-hi quan la màquina sigui al local |

Tailscale demanarà obrir un enllaç. **Es pot obrir des de qualsevol ordinador**: l'enllaç
identifica el portàtil, el navegador només demostra qui ets.

### 🔴 Després, i a mà, dues coses al web de Tailscale

1. **Machines → `local-ha` → Disable key expiry.** Si no, la clau caduca sola d'aquí a uns
   mesos i et quedes sense accés — i pel calendari d'aquest projecte, tocaria enmig de
   l'hivern que s'ha de documentar.
2. Instal·lar Tailscale **també al PC de casa i al mòbil**. Amb un sol node no serveix de res.

---

## 6. Home Assistant

```bash
ssh local-ha "cd ~/Local && git pull && docker compose up -d"
```

I comprovar que la configuració és bona **abans** de donar-ho per fet:

```bash
ssh local-ha "cd ~/Local && docker compose exec -T homeassistant python -m homeassistant --script check_config -c /config"
```

Ha de sortir només `Testing configuration at /config`. Qualsevol altra línia és un problema.

Després, al navegador: **http://LA-IP:8123** → crear el compte.

> ⚠️ **No afegeixis la integració `tplink` fins que el hub H100 no estigui al Wi-Fi
> definitiu.** La integració guarda la IP del hub; si canvia de xarxa, s'ha de refer.

---

## 7. Què hi ha instal·lat — estat del 20/09/2026

| Component | Versió | D'on surt |
|---|---|---|
| Linux Mint | **22.3** (base Ubuntu *noble*) | ISO |
| Nucli | 6.14.0-37-generic | Mint |
| Docker CE | **29.8.1** | Repositori oficial de Docker |
| Docker Compose | 5.5.1 | Connector `docker-compose-plugin` |
| Home Assistant | **2026.9.3** (contenidor, 3,43 GB) | `ghcr.io/home-assistant/home-assistant` |
| Tailscale | 1.102.4 | `tailscale.com/install.sh` |
| git | 2.43.0 | Mint |
| Python | 3.12.3 | Mint — `nit.py` només farà servir la biblioteca estàndard |

**Serveis actius a l'arrencada:** `ssh`, `docker`, `tailscaled`.
**Emmascarats a posta:** `sleep.target`, `suspend.target`, `hibernate.target`.
**Apagat a posta:** `bluetooth`.

**Tot el que es versiona viu a `~/Local`**, que és aquest repositori. El servidor **només
llegeix**: s'edita a casa, es puja a GitHub i el local fa `git pull`. Mai s'edita allà.

---

## 8. Els paranys, que és el que de debò val aquest document

### 🪤 El pen drive «no fa res»

`F12` ve **desactivada de fàbrica** als BIOS d'Acer. No és que el llapis estigui mal gravat:
és que la tecla no existeix fins que l'actives a *Main → F12 Boot Menu → Enabled*.

### 🪤 Docker no s'instal·la a Mint amb la recepta d'Ubuntu

El repositori de Docker vol el nom de la versió **d'Ubuntu**, i Mint en diu un altre (`xia`).
Cal treure'l del propi sistema:

```bash
. /etc/os-release && echo $UBUNTU_CODENAME     # → noble
```

Copiar la recepta d'Ubuntu tal qual deixa un repositori que no existeix.

### 🪤 `history_stats` tomba el paquet sencer, en silenci

HA fusiona els paquets **per domini**, i `history_stats` **no és una integració**: és una
plataforma de sensor. Escrita com a clau de primer nivell:

```
Setup of package 'rosada' failed: integration 'history_stats' cannot be merged, expected a dict
```

I el que cau no és aquell bloc: és **tot `rosada.yaml`**. Va sempre així:

```yaml
sensor:
  - platform: history_stats
    ...
```

> Això és exactament el tipus d'error que no es nota: HA arrenca perfectament, la interfície
> funciona, i simplement no hi ha cap de les entitats de la lògica. Per això `desplega.sh`
> comprova que `sensor.decisio_del_soterrani` **existeix i és fresc** després de cada desplegament.

### 🪤 `purge_interval` està obsolet

A la 2026.9.3 ja no existeix i deixa un avís a cada arrencada. `purge_keep_days: 730` sí que
s'ha de mantenir, i és la línia més important de tot el projecte.

### 🪤 El Bluetooth omple el log

`default_config` engega la integració de Bluetooth, i el contenidor no té `NET_ADMIN`/
`NET_RAW`. Es podrien donar aquestes capacitats, però seria regalar privilegis per una funció
que no volem: els sensors van per 868 MHz amb el hub. Es desactiva el servei al sistema.

### 🪤 Les descàrregues

Imatge d'HA: **3,43 GB**. Actualitzacions d'una Mint acabada d'instal·lar: **434 paquets**.
Si això passa per la SIM del local, és un disgust. **Tot es baixa a casa.**

---

## 9. Si s'ha de refer perquè s'ha mort el disc

L'ordre importa, perquè el que no es pot recuperar és l'històric:

1. Munta el sistema seguint els punts 2–6 d'aquest document.
2. **Restaura `.storage` i `secrets.yaml`** de la còpia setmanal xifrada abans d'arrencar HA.
   ⚠️ Sense `.storage` cal **reemparellar** els sensors, i reemparellar **parteix totes les
   sèries**: les entitats canvien d'identificador i l'històric anterior queda orfe.
3. Restaura la base de dades de la instantània nocturna més recent.
4. `docker compose up -d` i `check_config`.
5. Comprova que `purge_keep_days` segueix sent **730** *a la instància en calent*, no al fitxer.

> La pèrdua màxima acceptada per disseny és de **24 hores**, perquè el corpus probatori real
> són els CSV diaris segellats de `Local-data`, no la base de dades.
