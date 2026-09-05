# vb/scream

> Gemessen 2026-09-02 im vollen Server-Stapel, gepaart gegen dieselben 10 Trägersätze
> mit gleichem Seed. Protokoll §51, Studie `~/reports/burst_levers.md`.

## Rezept

| | |
|---|---|
| Skriptart | **allein stehend** |
| Burst-Adapter | `vb/scream` bei Gewicht **1.3** |
| Burst+Stop-DPO | keiner |
| Prompt-Form | **P3** — längere angegebene Dauer (+1,0 s) |

## Was dabei herauskommt

| Maß | Wert | gegen Grundform |
|---|--:|--:|
| Trefferquote, Familie | **0.167** | +0.167 (t +4.7, 8/10) |
| Trefferquote, streng | 0.150 | — |
| konservativ (−1 sd Seed-Rauschen) | **0.098** | |
| Genuineness | 2.66 | |
| Blend | 4.10 | |
| WER (Parakeet) | 0.243 | |
| DNSMOS | 2.92 | |

## Wie oft erzeugen

Bei einer Trefferquote von 0.17 braucht es **13 Kandidaten**, damit mit 90 %
Wahrscheinlichkeit mindestens einer den Laut realisiert. Konservativ gerechnet (0.10): **23 Kandidaten**.

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
| bester Adapter | **neu** `d2_matched` (nur DramaBox Rang ≤ 1) ⚠ |
| Skalierungsfaktor | **1,50** |
| Skriptart | **eingebettet** |
| Stapel | **nur der Adapter**, ohne Produktions-Stapel |
| Trefferquote, Familie (grobe Tabelle) | **0,500** |
| dieselbe Zelle im **veröffentlichten 23-Gruppen-Schema** | 0,500 — bestes Rezept dort: `d2_matched_alone` / inline / w = 1,50 |
| Trefferquote, streng | 0,500 |
| Genuineness | 1,10 |
| WER (Parakeet) | 0,160, gepaart +0,005 gegen die eigene w = 0-Zelle |
| Detektor-Boden (echte Sprache) | streng 0,595, Familie 0,595 — **nicht belastbar** (n < 30) |

**Entscheidung: das neue Rezept ersetzt das alte.** 0,500 gegen 0,170 familienweit, also mehr als eine Seed-Rausch-Standardabweichung (0,068) besser.

⚠ **Lizenz.** Dieser Adapter ist auf DramaBox-TTS-Audio mittrainiert; die LTX-2 Community Licence ist dafür **nicht geprüft** (§61). Solange das offen ist, bleibt das alte Rezept die freigegebene Rückfallvariante.

### Wie oft erzeugen (neu gerechnet)

Bei einer Trefferquote von 0,50 braucht es **4 Kandidaten**, damit mit 90 % Wahrscheinlichkeit mindestens einer den Laut realisiert. Konservativ gerechnet (0,43, eine Seed-Rausch-Standardabweichung abgezogen): **5 Kandidaten**.

Auswahl unter den Treffern nach Klang. Best-of-N bleibt der wirksamere Hebel als jede Stärkeänderung.

### Woher die Zahlen kommen

* **Messgerät:** `reward.RewardModel -> laion/vocal-burst-detector-v2` — dasselbe, das die Laufzeit selbst benutzt, und dasselbe, mit dem die Tabelle oben gemessen wurde.
* **Zweites Messgerät zur Kontrolle:** `laion/vocal-burst-detector-x2 (production, VoiceCLAP ensemble)`. Es kennt 16 der 45 Klassen; wo es diese Klasse kennt, steht sein Urteil in `VOCAL_BURSTS.md`. Keine Zeile mischt die beiden.
* **„Familie“** ist `burst_family.py` (md5 `19a0607b`), eine **gröbere** Einteilung als das veröffentlichte 23-Gruppen-Schema (`vm_groups.py` md5 `f83e3850`) — sie überschreitet dessen Grenzen, ist also systematisch großzügiger. Deshalb steht beides da.
* **„Streng“ ist streng bis auf 0,37 %:** `reward._same_class` ist ein Teilstring-Test, ein `Coughing` zählt also als Treffer für `cough`. Über 97.349 Ziel-Cues betrifft das 12 von 3.269 gezählten Erkennungen, **0** davon überschreiten eine 23-Gruppen-Grenze.

<!-- /vb_cls2:sec64 -->
