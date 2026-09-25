# Diari de la sèrie

> Els esdeveniments de fora que cap sensor no explica: finestres, neteja, talls de llum, obres,
> sensors tocats, aparells moguts. **Un pic anotat val més que un pic esborrat** → R1 i «El quadern
> de la sèrie» a [requisits.md](requisits.md#el-quadern-de-la-sèrie--i-aquí-es-tanca-el-cercle-amb-r1).
>
> Una línia per esdeveniment, amb l'hora local. **Sense noms ni dades personals.** A *Font*:
> **mesurat** vol dir que surt de les dades d'HA; **usuari**, que ho ha dit l'usuari i les dades
> soles no ho poden confirmar. El que no se sap s'escriu ⏳, no s'endevina.

| Inici | Fi | Què | Font | Què fa a les dades |
|---|---|---|---|---|
| 23/09 20:15 | 23/09 21:37 | **Trasllat** de casa al local | mesurat | Els cinc sensors, `unavailable`. `baixa` es va poder **mullar** pel camí: ~6 punts d'HR de més fins a l'endemà a les 09:00 → [calibratge.md](calibratge.md#registre) |
| 24/09 13:46 | 24/09 13:51 | **Sensors repartits** per les sales, en posicions de prova; es buida el dipòsit del deshumidificador | usuari · mesurat (el compressor para a les 13:46:26) | 5 min que **no serveixen**. Marcador del calibratge apagat a les 13:51:11 |
| 24/09 13:56:10 | ⏳ | **L'actuació del deshumidificador s'encén** des del tauler: HA el governa amb els llindars de tram (60–70 %) | mesurat | Amb l'HR per sota del llindar, **repòs** (només ventilador). Per això el soterrani no s'asseca des del 24/09 |
| 24/09 14:00:56 | 24/09 14:15:08 | Deshumidificador **al 35 %** a mà (el compressor, en marxa); HA el torna al llindar del tram en el repàs de cada 15 min | mesurat | L'únic quart d'hora d'assecat de la tarda |
| 24/09 ~15:55 | ⏳ | **Finestres obertes** | usuari (anunciat a les 15:53; ⏳ si han estat obertes tot el temps) | L'aire de fora entra: aquella tarda portava **més** vapor que el de dins (Td 17,0 contra 15,4 °C) |
| ⏳ | ⏳ | **Neteja amb aigua i lleixiu**, ventilant | usuari | L'aigua que s'evapora puja l'HR i el Td de dins |
| 24/09 16:11 | 24/09 16:42 | **Tall de llum** al local | mesurat: hub, endoll i aparell cauen alhora | 31 min de forat a tots els sensors i a l'endoll |
| 25/09 11:23 | 25/09 11:27 | **Tall de llum** | mesurat | 4 min |
| 25/09 11:38 | 25/09 12:01 | **Tall de llum** | mesurat | 23 min |
| 25/09 18:21 | 25/09 19:43 | **Tall de llum**; el router torna a les 19:25 | mesurat | 81 min |

**Els talls de llum**, segons l'usuari, són per **instal·lar els S110E**. ⏳ Quins dels quatre ho
són, pendent. En tots quatre el portàtil aguanta amb la bateria, sense reiniciar-se, i HA segueix
en marxa; el que cau és el router, el hub i l'endoll, i per tant **totes** les dades.

**Del 24/09 a la tarda al 26/09**, la sèrie barreja tres coses que la fan poc útil per llegir el
soterrani: les finestres obertes, la neteja i el deshumidificador en repòs. El 26/09 a la 01:00 el
racó més humit era a **17,8 °C de Td i 67,6 % d'HR**, ~2,4 °C de Td més que el 24/09 a la tarda.
