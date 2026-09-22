#!/usr/bin/env python3
"""Experiments amb el deshumidificador: una ordre per tuya-local, uns watts al P110M.

QUÈ RESOL
─────────
El deshumidificador té dos camins cap a HA que no es coneixen entre ells:
`tuya-local` (el que li diu què ha de fer) i l'endoll P110M per Matter (el que
mesura què gasta). Aquestes proves els lliguen: li donen una ordre i miren què
fa DE DEBÒ, pels watts. Serveixen per entendre l'aparell ara i per tornar-ho a
comprovar d'aquí a un any, o al soterrani a l'hivern.

    python3 tools/prova_deshumidificador.py resposta     # l'ordre arriba i el compressor obeeix
    python3 tools/prova_deshumidificador.py memoria      # 0.2b: recorda la configuració sense corrent?
    python3 tools/prova_deshumidificador.py operacio     # ECO / purificar / deshumidificar: què gasta
    python3 tools/prova_deshumidificador.py ventilador   # les tres velocitats: què gasta
    python3 tools/prova_deshumidificador.py ventilador_sol  # només moure aire, sense assecar: què gasta
    python3 tools/prova_deshumidificador.py modes        # manual / nit / roba / auto, amb el llindar al mínim
    python3 tools/prova_deshumidificador.py assecat      # quant dura el ventilador després d'aturar-se
    python3 tools/prova_deshumidificador.py diposit      # en continu fins que s'omple: els litres per kWh
    python3 tools/prova_deshumidificador.py tots         # tot això seguit, menys «resposta» i «diposit»

Fa servir HA_URL i HA_TOKEN (o HA_TOKEN_FILE), com calibratge.py i tarifa.py.
Deixa cada mostra a un CSV (--csv FITXER, per defecte a /tmp). Només
biblioteca estàndard. Surt amb codi 1 si «resposta» no passa.

COM ES LLEGEIXEN ELS WATTS (mesurat el 21/09/2026)
──────────────────────────────────────────────────
  · compressor en marxa  300–400 W   (placa: 470 W)
  · només el ventilador  ~16 W       (també els ~5 min que segueix després d'aturar)
  · en espera            ~1 W
  Per això els llindars són 150 W i 5 W: queden lluny de totes tres zones.

⚠️ EL COMPRESSOR MANA SOBRE LES PROVES. Cap pas no el fa arrencar i aturar en
   menys de 5 minuts: repicar-lo el mata. L'aparell té la seva protecció de
   5 min, i en tornar el corrent també espera ~5 min (provat el 21/09/2026),
   però les proves no s'hi recolzen. La de memòria només talla el corrent amb
   el compressor aturat de fa més de 6 minuts.

⚠️ ES DEIXA COM ESTAVA, passi el que passi: si falla, si s'interromp amb
   Ctrl-C o si arriba SIGTERM/SIGHUP. Es restauren el mode, el llindar, la
   velocitat, l'operació i l'assecat intern. I l'endoll, si una prova l'ha
   apagat, es torna a ENCENDRE abans de res més.

⚠️ QUI MANA. Fora de la prova de memòria, cap prova no toca l'endoll: el que
   noms-entitats.md permet de moment és llegir i ajustar. La de memòria és
   l'única que l'apaga, perquè és justament el que vol provar, i un minut.
"""

from __future__ import annotations

import csv
import json
import os
import signal
import statistics as est
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

APARELL = "humidifier.deshumidificador"          # tuya-local
VENTILADOR = "fan.deshumidificador"
OPERACIO = "select.deshumidificador_mode_aire"
ASSECAT = "switch.deshumidificador_assecat_intern"
AVARIA = "binary_sensor.deshumidificador_avaria"
POTENCIA = "sensor.deshumidificador_potencia"    # P110M, per Matter
ENDOLL = "switch.deshumidificador"
ENERGIA = "sensor.deshumidificador_energia"      # el comptador de l'endoll (kWh)
TOTES = (APARELL, VENTILADOR, OPERACIO, ASSECAT, AVARIA, POTENCIA, ENDOLL, ENERGIA)

W_COMPRESSOR = 150
W_VENTILADOR = 5
PAS_S = 10
MIN_MINUTS_RESPOSTA = 8
CONTINU = 35     # el mínim que admet HA; a la pantalla, «CO»: assecar sense parar
MAI = 80         # el màxim: per sobre de qualsevol HR d'una habitació normal


# ─── HA ──────────────────────────────────────────────────────────────────────

def _testimoni() -> tuple[str, str]:
    base = os.environ.get("HA_URL", "").rstrip("/")
    testimoni = os.environ.get("HA_TOKEN", "")
    if not testimoni and os.environ.get("HA_TOKEN_FILE"):
        testimoni = Path(os.environ["HA_TOKEN_FILE"]).expanduser().read_text(encoding="utf-8").strip()
    if not base or not testimoni:
        raise SystemExit("Falten HA_URL i HA_TOKEN (o HA_TOKEN_FILE).")
    return base, testimoni


def _crida(metode: str, camí: str, cos: dict | None = None):
    base, testimoni = _testimoni()
    peticio = urllib.request.Request(
        f"{base}{camí}", method=metode,
        data=json.dumps(cos).encode() if cos is not None else None,
        headers={"Authorization": f"Bearer {testimoni}", "Content-Type": "application/json"})
    with urllib.request.urlopen(peticio, timeout=20) as resposta:
        return json.loads(resposta.read().decode() or "null")


def estats() -> dict[str, dict]:
    return {s["entity_id"]: s for s in _crida("GET", "/api/states") if s["entity_id"] in TOTES}


def servei(domini: str, nom: str, entitat: str, **dades) -> None:
    _crida("POST", f"/api/services/{domini}/{nom}", {"entity_id": entitat, **dades})
    time.sleep(2)


# Les ordres que fan servir les proves, amb nom perquè el registre s'entengui.
def llindar(v): return lambda: servei("humidifier", "set_humidity", APARELL, humidity=v)
def mode(v): return lambda: servei("humidifier", "set_mode", APARELL, mode=v)
def velocitat(v): return lambda: servei("fan", "set_percentage", VENTILADOR, percentage=v)
def operacio(v): return lambda: servei("select", "select_option", OPERACIO, option=v)
def assecat(on): return lambda: servei("switch", "turn_on" if on else "turn_off", ASSECAT)


def _num(e: dict, ent: str) -> float | None:
    try:
        return float(e[ent]["state"])
    except (KeyError, ValueError, TypeError):
        return None


def classe(w: float | None) -> str:
    if w is None:
        return "—"
    return "compressor" if w > W_COMPRESSOR else "ventilador" if w >= W_VENTILADOR else "repòs"


def fotografia(e: dict) -> dict:
    a = e.get(APARELL, {}).get("attributes", {})
    f = e.get(VENTILADOR, {}).get("attributes", {})
    return {"engegat": e.get(APARELL, {}).get("state"), "mode": a.get("mode"),
            "llindar": a.get("humidity"), "velocitat": f.get("percentage"),
            "operacio": e.get(OPERACIO, {}).get("state"), "assecat": e.get(ASSECAT, {}).get("state")}


def fins_que(ordre, clau: str, valor, segons: float = 20, intents: int = 3) -> bool:
    """Dona l'ordre i espera que l'aparell la reflecteixi; si no, la repeteix.
    Cal perquè l'aparell canvia coses TOT SOL uns segons després d'una ordre: en
    passar de «purificar» a deshumidificar torna el mode de Roba a Manual, i si
    el llindar arriba abans, el rebutja (21/09/2026)."""
    for _ in range(intents):
        ordre()
        t0 = time.time()
        while time.time() - t0 < segons:
            if fotografia(estats()).get(clau) == valor:
                return True
            time.sleep(2)
    print(f"  ⚠️ {clau} no ha agafat el valor {valor} després de {intents} intents")
    return False


def restaura(f: dict) -> None:
    """L'ORDRE IMPORTA, i ho vam aprendre a les males (21/09/2026):
    · l'operació primer, perquè decideix què vol dir la velocitat i, si ve de
      «purificar», l'aparell hi canvia el mode tot sol;
    · el llindar i la velocitat, en mode MANUAL: en AUTO (i en ROBA) l'aparell
      REBUTJA el llindar sense dir res. Restaurant «auto» abans que «55 %», el
      llindar es va quedar al 80 %;
    · el mode original, l'últim.
    Cada pas es comprova i es repeteix si no ha agafat."""
    if f.get("operacio") not in (None, "unavailable", "unknown"):
        fins_que(operacio(f["operacio"]), "operacio", f["operacio"])
    fins_que(mode("normal"), "mode", "normal")
    if f.get("llindar") is not None:
        fins_que(llindar(f["llindar"]), "llindar", f["llindar"])
    if f.get("velocitat") is not None:
        fins_que(velocitat(f["velocitat"]), "velocitat", f["velocitat"])
    if f.get("mode") and f["mode"] != "normal":
        fins_que(mode(f["mode"]), "mode", f["mode"])
    if f.get("assecat") in ("on", "off"):
        fins_que(assecat(f["assecat"] == "on"), "assecat", f["assecat"])


# ─── Registre ────────────────────────────────────────────────────────────────

class Registre:
    CAMPS = ("experiment", "pas", "hora", "t", "w", "classe", "engegat", "mode", "llindar",
             "hr", "velocitat", "operacio", "assecat", "avaria", "codi_falla")

    def __init__(self, cami: Path):
        self.cami = cami
        self.fitxer = cami.open("w", newline="", encoding="utf-8")
        self.csv = csv.DictWriter(self.fitxer, fieldnames=self.CAMPS)
        self.csv.writeheader()
        self.files: list[dict] = []

    def mostra(self, experiment: str, pas: str, t: float) -> dict:
        e = estats()
        a = e.get(APARELL, {}).get("attributes", {})
        w = _num(e, POTENCIA)
        fila = {"experiment": experiment, "pas": pas, "hora": datetime.now().isoformat(timespec="seconds"),
                "t": round(t), "w": w, "classe": classe(w), "engegat": e.get(APARELL, {}).get("state"),
                "mode": a.get("mode"), "llindar": a.get("humidity"), "hr": a.get("current_humidity"),
                "velocitat": e.get(VENTILADOR, {}).get("attributes", {}).get("percentage"),
                "operacio": e.get(OPERACIO, {}).get("state"), "assecat": e.get(ASSECAT, {}).get("state"),
                "avaria": e.get(AVARIA, {}).get("state"),
                "codi_falla": e.get(AVARIA, {}).get("attributes", {}).get("fault_code")}
        self.csv.writerow(fila)
        self.fitxer.flush()
        self.files.append(fila)
        print(f"  {fila['hora'][11:]}  +{fila['t']:4d} s  {'—' if w is None else f'{w:6.1f}'} W "
              f"{fila['classe']:10s} mode {fila['mode']} · llindar {fila['llindar']} · HR {fila['hr']} % · "
              f"vel. {fila['velocitat']} · {fila['operacio']}")
        return fila


def pas(reg: Registre, experiment: str, nom: str, segons: float, *ordres, fins=None) -> list[dict]:
    """Dona les ordres i mostreja. Amb «fins», s'atura abans si la condició es compleix."""
    print(f"\n▶ {datetime.now():%H:%M:%S}  {experiment} · {nom}")
    for o in ordres:
        o()
    t0 = time.time()
    files = []
    while time.time() - t0 < segons:
        files.append(reg.mostra(experiment, nom, time.time() - t0))
        if fins and fins(files):
            break
        time.sleep(PAS_S)
    return files


def estable(files: list[dict], des_de: float = 0.4) -> list[dict]:
    """La part del pas un cop assentat: les transicions no compten a la mitjana."""
    if not files:
        return []
    return [f for f in files if f["t"] >= files[-1]["t"] * des_de and f["w"] is not None]


def resum_pas(nom: str, files: list[dict]) -> str:
    fs = estable(files)
    if not fs:
        return f"  {nom:34s} sense dades"
    ws = [f["w"] for f in fs]
    parts = {c: sum(f["classe"] == c for f in fs) / len(fs) for c in ("compressor", "ventilador", "repòs")}
    return (f"  {nom:34s} mediana {est.median(ws):6.1f} W · "
            f"compressor {parts['compressor']:4.0%} · ventilador {parts['ventilador']:4.0%} · "
            f"repòs {parts['repòs']:4.0%}")


def temps_fins(files: list[dict], cond) -> float | None:
    return next((f["t"] for f in files if cond(f)), None)


def quiet(minuts: float):
    """Condició: fa «minuts» que no passa res (menys de 5 W). Per tallar el corrent sense risc."""
    def cond(files):
        n = int(minuts * 60 / PAS_S)
        return len(files) >= n and all(f["w"] is not None and f["w"] < W_VENTILADOR for f in files[-n:])
    return cond


# ─── Els experiments ─────────────────────────────────────────────────────────

def exp_resposta(reg: Registre, cicles: int = 2, minuts: float = 10) -> bool:
    """El llindar per sota i per sobre de l'HR: el consum hi ha de respondre."""
    if minuts < MIN_MINUTS_RESPOSTA:
        raise SystemExit(f"Menys de {MIN_MINUTS_RESPOSTA} min per fase faria repicar el compressor. No.")
    mode("normal")()     # en AUTO i en ROBA l'aparell IGNORA el llindar (manual, pàg. 30)
    resultats = []
    for c in range(1, cicles + 1):
        for nom, v, engega in ((f"ENGEGA {c}", CONTINU, True), (f"ATURA {c}", MAI, False)):
            files = pas(reg, "resposta", nom, minuts * 60, llindar(v))
            resultats.append((nom, engega, files))
    print("\n═══ resposta ═══")
    tot_bé = True
    for nom, engega, files in resultats:
        limit = 360 if engega else 120     # 5 min de protecció + 1 de marge · el ventilador sol
        creua = temps_fins(files, (lambda f: f["classe"] == "compressor") if engega
                           else (lambda f: f["classe"] != "compressor"))
        despres = [f for f in files if creua is not None and f["t"] >= creua and f["w"] is not None]
        obeeix = sum((f["classe"] == "compressor") == engega for f in despres) / len(despres) if despres else 0
        bé = creua is not None and creua <= limit and obeeix >= 0.8
        tot_bé &= bé
        print(f"  {'✅' if bé else '❌'} {nom:9s} resposta en {'MAI' if creua is None else f'{int(creua)} s'} "
              f"(límit {limit} s) · obeeix el {obeeix:.0%} del temps")
        print(resum_pas("", files))
    print("✅ L'ordre arriba a l'aparell i el consum hi respon" if tot_bé else "❌ No passa")
    return tot_bé


def exp_memoria(reg: Registre) -> None:
    """0.2b: se li deixa una configuració inconfusible, es talla el corrent un minut i es mira què recorda."""
    marca = {"mode": "normal", "llindar": 70, "velocitat": 33}
    files = pas(reg, "memoria", "prepara: normal · 70 % · vel. 33 · quiet 6 min", 25 * 60,
                mode(marca["mode"]), llindar(marca["llindar"]), velocitat(marca["velocitat"]), fins=quiet(6))
    if not quiet(6)(files):
        print("❌ memoria: el compressor no s'ha quedat quiet 6 min. No tallo el corrent.")
        return
    abans = fotografia(estats())
    print(f"  abans del tall: {abans}")
    print(f"\n▶ {datetime.now():%H:%M:%S}  memoria · TALL de corrent (60 s)")
    servei("switch", "turn_off", ENDOLL)
    time.sleep(60)
    durant = estats().get(APARELL, {}).get("state")
    servei("switch", "turn_on", ENDOLL)
    print(f"  durant el tall, tuya-local veia l'aparell: {durant}")
    files = pas(reg, "memoria", "torna el corrent: esperant tuya-local", 5 * 60,
                fins=lambda fs: fs[-1]["mode"] is not None and fs[-1]["engegat"] not in ("unavailable", None))
    time.sleep(30)
    despres = fotografia(estats())
    print(f"  després del tall: {despres}")
    print("\n═══ memoria ═══")
    for k in ("engegat", "mode", "llindar", "velocitat", "operacio", "assecat"):
        igual = abans.get(k) == despres.get(k)
        print(f"  {'✅' if igual else '❌'} {k:10s} {abans.get(k)!s:>22} → {despres.get(k)!s}")
    if all(abans.get(k) == despres.get(k) for k in ("mode", "llindar")):
        print("✅ RECORDA el mode i el llindar després de quedar-se sense corrent (0.2b superada)")
    else:
        print("❌ NO els recorda: torna a una configuració per defecte (0.2b: l'arquitectura (a) trontolla)")


def exp_operacio(reg: Registre) -> None:
    """Les tres operacions del botó OPERATION (ECO, purificar, deshumidificar) amb el llindar en continu."""
    opcions = estats().get(OPERACIO, {}).get("attributes", {}).get("options") or []
    passos = []
    passos.append(("base: normal · continu", pas(reg, "operacio", "base: normal · continu", 5 * 60,
                                                  mode("normal"), llindar(CONTINU))))
    ordre = [o for o in opcions if o != "purify"] + [o for o in opcions if o == "purify"]
    for o in ordre:
        passos.append((f"operació {o}", pas(reg, "operacio", f"operació {o}", 8 * 60, operacio(o))))
    torna = next((o for o in opcions if o != "purify"), None)
    if torna:   # després de purificar, quant triga a tornar el compressor
        passos.append((f"torna a {torna}", pas(reg, "operacio", f"torna a {torna}", 8 * 60, operacio(torna))))
    print("\n═══ operacio ═══")
    for nom, files in passos:
        print(resum_pas(nom, files))


def exp_ventilador(reg: Registre) -> None:
    passos = [("base: normal · continu", pas(reg, "ventilador", "base: normal · continu", 5 * 60,
                                             mode("normal"), llindar(CONTINU)))]
    for v in (33, 67, 100):
        passos.append((f"velocitat {v} %", pas(reg, "ventilador", f"velocitat {v} %", 5 * 60, velocitat(v))))
    print("\n═══ ventilador ═══")
    for nom, files in passos:
        print(resum_pas(nom, files))


def exp_ventilador_sol(reg: Registre) -> None:
    """Operació «purificar» = el ventilador sol, sense compressor: què costa només moure aire.
    La pregunta: si val la pena fer-lo anar d'estona en estona per remenar l'aire del local."""
    opcions = estats().get(OPERACIO, {}).get("attributes", {}).get("options") or []
    if "purify" not in opcions:
        print(f"❌ ventilador_sol: no hi ha l'operació «purify» ({opcions})")
        return
    passos = [("purificar: el compressor s'atura", pas(reg, "ventilador_sol", "purificar: el compressor s'atura",
                                                       4 * 60, mode("normal"), operacio("purify")))]
    for v in (33, 67, 100):
        passos.append((f"ventilador sol {v} %", pas(reg, "ventilador_sol", f"ventilador sol {v} %", 4 * 60,
                                                    velocitat(v))))
    print("\n═══ ventilador_sol ═══")
    for nom, files in passos:
        print(resum_pas(nom, files))


def exp_modes(reg: Registre) -> None:
    """Amb el llindar en continu: si un mode l'ignora, es veu perquè el compressor no hi va sempre."""
    passos = [("normal · continu", pas(reg, "modes", "normal · continu", 8 * 60, mode("normal"), llindar(CONTINU)))]
    for m, minuts in (("sleep", 8), ("laundry", 8), ("auto", 12)):
        passos.append((f"{m} · continu", pas(reg, "modes", f"{m} · continu", minuts * 60, mode(m))))
    print("\n═══ modes ═══")
    for nom, files in passos:
        print(resum_pas(nom, files))


def exp_assecat(reg: Registre) -> None:
    """Quant va el ventilador després d'aturar el compressor, sense i amb l'assecat intern."""
    resultats = []
    for on in (False, True):
        etiqueta = "amb assecat intern" if on else "sense assecat intern"
        pas(reg, "assecat", f"escalfa: compressor 6 min, {etiqueta}", 6 * 60,
            assecat(on), mode("normal"), llindar(CONTINU))
        files = pas(reg, "assecat", f"atura i compta, {etiqueta}", 40 * 60, llindar(MAI), fins=quiet(2))
        fi_compressor = temps_fins(files, lambda f: f["classe"] != "compressor")
        fi_ventilador = temps_fins(files, lambda f: f["classe"] == "repòs")
        resultats.append((etiqueta, fi_compressor, fi_ventilador))
    print("\n═══ assecat ═══")
    for etiqueta, fc, fv in resultats:
        corre = None if fc is None or fv is None else fv - fc
        print(f"  {etiqueta:22s} el ventilador segueix "
              f"{'—' if corre is None else f'{corre / 60:.1f} min'} després d'aturar el compressor")


def exp_diposit(reg: Registre, max_hores: float = 16) -> None:
    """Els litres per kWh: en continu fins que el dipòsit s'omple i l'aparell s'atura sol (codi 32).
    El flotador salta a ~3 L, no als 3,8 nominals (mesurat amb una gerra el 22/09/2026).
    ⚠️ La safata interior s'omple abans que el dipòsit: si l'aparell no ha treballat abans, el
       primer dipòsit surt car. Es fa amb la safata ja mullada (21/09/2026)."""
    global PAS_S
    PAS_S = 60     # una nit sencera: una mostra per minut n'hi ha prou
    e0 = estats()
    kwh0 = _num(e0, ENERGIA)
    t0 = time.time()
    files = pas(reg, "diposit", "continu fins al codi 32", max_hores * 3600,
                operacio("dehumidify"), mode("normal"), llindar(CONTINU), velocitat(100),
                fins=lambda fs: fs[-1]["codi_falla"] == 32)
    e1 = estats()
    kwh1 = _num(e1, ENERGIA)
    ple = bool(files) and files[-1]["codi_falla"] == 32
    hores = (time.time() - t0) / 3600
    comp = sum(f["classe"] == "compressor" for f in files) / len(files) if files else 0
    hr = [f["hr"] for f in files if isinstance(f["hr"], (int, float))]
    print("\n═══ diposit ═══")
    print(f"  {'✅ dipòsit ple (codi 32)' if ple else '⚠️ NO s´ha omplert'} en {hores:.1f} h · compressor {comp:.0%}"
          f" del temps · HR de l'aparell {hr[0] if hr else '—'} → {hr[-1] if hr else '—'} %")
    if kwh0 is not None and kwh1 is not None:
        kwh = kwh1 - kwh0
        print(f"  energia: {kwh:.3f} kWh" + (f" · amb els ~3 L d'un ple: {3.0 / kwh:.2f} L/kWh" if kwh > 0 else ""))


EXPERIMENTS = {"resposta": exp_resposta, "memoria": exp_memoria, "operacio": exp_operacio,
               "ventilador": exp_ventilador, "ventilador_sol": exp_ventilador_sol,
               "modes": exp_modes, "assecat": exp_assecat, "diposit": exp_diposit}


# ─── Marc: comprovar abans, restaurar després ────────────────────────────────

class Interrompuda(Exception):
    pass


def _talla(signe, _marc):
    raise Interrompuda(f"senyal {signal.Signals(signe).name}")


def comprovacions_prèvies(e: dict) -> list[str]:
    errors = [f"{ent} no està disponible" for ent in TOTES
              if ent not in e or e[ent]["state"] in ("unavailable", "unknown")]
    if errors:
        return errors
    if e[ENDOLL]["state"] != "on":
        errors.append("l'endoll està apagat: sense corrent no hi ha res a mesurar")
    if e[APARELL]["state"] != "on":
        errors.append("el deshumidificador està apagat (aquestes proves no l'engeguen: no en són l'amo)")
    if e[AVARIA]["state"] == "on":
        errors.append("el deshumidificador marca avaria")
    hr = e[APARELL]["attributes"].get("current_humidity")
    if not isinstance(hr, (int, float)) or not (40 < hr < 75):
        errors.append(f"l'HR de l'habitació ({hr} %) ha de ser entre 40 i 75 perquè el continu engegui i el "
                      f"{MAI} % aturi sense dubtes")
    return errors


def main(argv: list[str]) -> int:
    noms = [a for a in argv if a in EXPERIMENTS or a == "tots"]
    if not noms:
        print(__doc__)
        return 1
    # «tots» no inclou «resposta» (és la prova de punta a punta) ni «diposit» (dura una nit)
    triats = [n for n in EXPERIMENTS if n not in ("resposta", "diposit")] if "tots" in noms else noms
    cami = Path(argv[argv.index("--csv") + 1]) if "--csv" in argv \
        else Path(f"/tmp/deshumidificador-{'-'.join(triats)}-{datetime.now():%Y%m%d-%H%M}.csv")

    e = estats()
    errors = comprovacions_prèvies(e)
    if errors:
        print("No es pot fer la prova:", *errors, sep="\n  · ")
        return 1
    original = fotografia(e)
    print(f"Configuració d'abans (es restaurarà): {original}\nMostres a {cami}")

    for s in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(s, _talla)
    reg = Registre(cami)
    resultat = True
    try:
        for n in triats:
            r = EXPERIMENTS[n](reg)
            resultat &= r is not False
    except (KeyboardInterrupt, Interrompuda) as err:
        print(f"\n⚠ Interrompuda ({err or 'Ctrl-C'}): restauro.")
        resultat = False
    finally:
        # Primer de tot, el corrent: una prova no pot deixar mai l'endoll apagat.
        if estats().get(ENDOLL, {}).get("state") != "on":
            servei("switch", "turn_on", ENDOLL)
            for _ in range(30):
                time.sleep(10)
                if estats().get(APARELL, {}).get("state") not in ("unavailable", None):
                    break
        restaura(original)
        time.sleep(5)
        ara = fotografia(estats())
        diferent = {k: (original[k], ara[k]) for k in original if original[k] != ara[k]}
        print(f"\nRestaurat: {ara}" + (f"\n  ⚠️ NO QUADRA: {diferent} — revisa-ho a mà" if diferent else ""))
        reg.fitxer.close()
    return 0 if resultat else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
