# vb/clears_throat

> Gemessen 2026-09-02 im vollen Server-Stapel, gepaart gegen dieselben 10 Trägersätze
> mit gleichem Seed. Protokoll §51, Studie `~/reports/burst_levers.md`.

## Rezept

| | |
|---|---|
| Skriptart | **eingebettet** |
| Burst-Adapter | `vb/clears_throat` bei Gewicht **1.25** |
| Burst+Stop-DPO | keiner |
| Prompt-Form | **P4** — Platzierung an der Satzgrenze |

## Was dabei herauskommt

| Maß | Wert | gegen Grundform |
|---|--:|--:|
| Trefferquote, Familie | **0.483** | +0.433 (t +7.0, 10/10) |
| Trefferquote, streng | 0.000 | — |
| konservativ (−1 sd Seed-Rauschen) | **0.415** | |
| Genuineness | 2.28 | |
| Blend | 3.41 | |
| WER (Parakeet) | 0.520 | |
| DNSMOS | 3.13 | |

## Wie oft erzeugen

Bei einer Trefferquote von 0.48 braucht es **4 Kandidaten**, damit mit 90 %
Wahrscheinlichkeit mindestens einer den Laut realisiert. Konservativ gerechnet (0.41): **5 Kandidaten**.

Auswahl unter den Treffern nach Klang; wenn mehrere sitzen, den mit der höchsten
Genuineness nehmen. Best-of-N ist hier der wirksamere Hebel als jede Stärkeänderung.

## Achtung: die Unterart trifft er nicht

Streng gemessen liegt diese Klasse bei 0.000, familien-gelockert bei 0.483.
Das Modell erzeugt zuverlässig einen Laut **derselben Familie**, aber nicht die
etikettierte Unterart. Wer auf genau dieser Unterart besteht, wird enttäuscht — den
gewünschten Charakter deshalb über die Emotionsanweisung steuern, nicht über das Etikett.

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
| bester Adapter | **neu** `bulk_mix_full` (echt + DramaBox Rang ≤ 1) ⚠ |
| Skalierungsfaktor | **1,50** |
| Skriptart | **eingebettet** |
| Stapel | voller Produktions-Stapel |
| Trefferquote, Familie (grobe Tabelle) | **0,267** |
| dieselbe Zelle im **veröffentlichten 23-Gruppen-Schema** | 0,267 — bestes Rezept dort: `bulk` / inline / w = 1,50 |
| Trefferquote, streng | 0,000 — in **keiner** Zelle über null |
| Genuineness | 1,88 |
| WER (Parakeet) | 0,109, gepaart -0,018 gegen die eigene w = 0-Zelle |

**Entscheidung: die alte Prompt-Strategie bleibt stehen.** Sie misst 0,480 familienweit gegen 0,267 für das beste neue Adapter/Stärke-Paar. Ersetzt wird nur, was die alte Zahl um mehr als eine Seed-Rausch-Standardabweichung (0,068, §52) schlägt; das ist hier nicht der Fall. Das oben stehende Rezept gilt weiter.

### Wie oft erzeugen (neu gerechnet)

Es gilt weiter die Rechnung des alten Rezepts oben (4 Kandidaten, konservativ 5). Zum Vergleich: bei der neu gemessenen Quote von 0,27 wären es **8 Kandidaten**, konservativ (0,20) **11**.

Auswahl unter den Treffern nach Klang. Best-of-N bleibt der wirksamere Hebel als jede Stärkeänderung.

### Woher die Zahlen kommen

* **Messgerät:** `reward.RewardModel -> laion/vocal-burst-detector-v2` — dasselbe, das die Laufzeit selbst benutzt, und dasselbe, mit dem die Tabelle oben gemessen wurde.
* **Zweites Messgerät zur Kontrolle:** `laion/vocal-burst-detector-x2 (production, VoiceCLAP ensemble)`. Es kennt 16 der 45 Klassen; wo es diese Klasse kennt, steht sein Urteil in `VOCAL_BURSTS.md`. Keine Zeile mischt die beiden.
* **„Familie“** ist `burst_family.py` (md5 `19a0607b`), eine **gröbere** Einteilung als das veröffentlichte 23-Gruppen-Schema (`vm_groups.py` md5 `f83e3850`) — sie überschreitet dessen Grenzen, ist also systematisch großzügiger. Deshalb steht beides da.
* **„Streng“ ist streng bis auf 0,37 %:** `reward._same_class` ist ein Teilstring-Test, ein `Coughing` zählt also als Treffer für `cough`. Über 97.349 Ziel-Cues betrifft das 12 von 3.269 gezählten Erkennungen, **0** davon überschreiten eine 23-Gruppen-Grenze.

<!-- /vb_cls2:sec64 -->
