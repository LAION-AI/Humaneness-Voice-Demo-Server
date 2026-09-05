# vb/chuckle

> Gemessen 2026-09-02 im vollen Server-Stapel, gepaart gegen dieselben 10 Trägersätze
> mit gleichem Seed. Protokoll §51, Studie `~/reports/burst_levers.md`.

## Rezept

| | |
|---|---|
| Skriptart | **allein stehend** |
| Burst-Adapter | `vb/chuckle` bei Gewicht **2** |
| Burst+Stop-DPO | keiner |
| Prompt-Form | **C_gl** — C_gl |

## Was dabei herauskommt

| Maß | Wert | gegen Grundform |
|---|--:|--:|
| Trefferquote, Familie | **0.725** | +0.392 (t +3.0, 7/10) |
| Trefferquote, streng | 0.377 | — |
| konservativ (−1 sd Seed-Rauschen) | **0.657** | |
| Genuineness | 3.76 | |
| Blend | 3.58 | |
| WER (Parakeet) | 0.581 | |
| DNSMOS | 2.94 | |

## Wie oft erzeugen

Bei einer Trefferquote von 0.73 braucht es **2 Kandidaten**, damit mit 90 %
Wahrscheinlichkeit mindestens einer den Laut realisiert. Konservativ gerechnet (0.66): **3 Kandidaten**.

Auswahl unter den Treffern nach Klang; wenn mehrere sitzen, den mit der höchsten
Genuineness nehmen. Best-of-N ist hier der wirksamere Hebel als jede Stärkeänderung.

<!-- vb_cls2:sec64 -->

## Nachtrag §64 (2026-09-04) — Adapter und Stärke, neu gemessen

> Studie `vb_cls2`, Bericht mit Hörproben: `~/reports/bericht_vokale_bursts.html`.
> Variiert wurden **Adapter und Skalierungsfaktor** auf dem Trägersatz der
> Grundform, gemessen mit demselben Detektor (`vocal-burst-detector-v2`) wie oben.
> Die alte Messung variiert die **Prompt-Form**. Beide Zahlen stehen auf demselben
> Instrument und demselben Trägerkorpus, aber sie variieren **verschiedene**
> Faktoren: ein Unterschied ist ein Unterschied zwischen zwei *Rezepten als
> Ganzem* und darf keinem einzelnen Faktor zugeschrieben werden.

| | |
|---|---|
| bester Adapter | der ausgelieferte Adapter |
| Skalierungsfaktor | **2,00** |
| Skriptart | **eingebettet** |
| Stapel | voller Produktions-Stapel |
| Trefferquote, Familie (grobe Tabelle) | **0,533** |
| dieselbe Zelle im **veröffentlichten 23-Gruppen-Schema** | 0,533 — bestes Rezept dort: `shipped` / inline / w = 2,00 |
| Trefferquote, streng | 0,333 |
| Genuineness | 3,16 |
| WER (Parakeet) | 0,236, gepaart +0,095 gegen die eigene w = 0-Zelle |
| Detektor-Boden (echte Sprache) | streng 0,641, Familie 0,849 |

**Entscheidung: die alte Prompt-Strategie bleibt stehen.** Sie misst 0,730 familienweit gegen 0,533 für das beste neue Adapter/Stärke-Paar. Ersetzt wird nur, was die alte Zahl um mehr als eine Seed-Rausch-Standardabweichung (0,068, §52) schlägt; das ist hier nicht der Fall. Das oben stehende Rezept gilt weiter.

### Wie oft erzeugen (neu gerechnet)

Es gilt weiter die Rechnung des alten Rezepts oben (2 Kandidaten, konservativ 3). Zum Vergleich: bei der neu gemessenen Quote von 0,53 wären es **4 Kandidaten**, konservativ (0,47) **4**.

Auswahl unter den Treffern nach Klang. Best-of-N bleibt der wirksamere Hebel als jede Stärkeänderung.

### Woher die Zahlen kommen

* **Messgerät:** `reward.RewardModel -> laion/vocal-burst-detector-v2` — dasselbe, das die Laufzeit selbst benutzt, und dasselbe, mit dem die Tabelle oben gemessen wurde.
* **Zweites Messgerät zur Kontrolle:** `laion/vocal-burst-detector-x2 (production, VoiceCLAP ensemble)`. Es kennt 16 der 45 Klassen; wo es diese Klasse kennt, steht sein Urteil in `VOCAL_BURSTS.md`. Keine Zeile mischt die beiden.
* **„Familie“** ist `burst_family.py` (md5 `19a0607b`), eine **gröbere** Einteilung als das veröffentlichte 23-Gruppen-Schema (`vm_groups.py` md5 `f83e3850`) — sie überschreitet dessen Grenzen, ist also systematisch großzügiger. Deshalb steht beides da.
* **„Streng“ ist streng bis auf 0,37 %:** `reward._same_class` ist ein Teilstring-Test, ein `Coughing` zählt also als Treffer für `cough`. Über 97.349 Ziel-Cues betrifft das 12 von 3.269 gezählten Erkennungen, **0** davon überschreiten eine 23-Gruppen-Grenze.

<!-- /vb_cls2:sec64 -->
