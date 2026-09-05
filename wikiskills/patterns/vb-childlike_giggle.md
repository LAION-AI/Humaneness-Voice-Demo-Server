# vb/childlike_giggle

> Gemessen 2026-09-02 im vollen Server-Stapel, gepaart gegen dieselben 10 Trägersätze
> mit gleichem Seed. Protokoll §51, Studie `~/reports/burst_levers.md`.

## Rezept

| | |
|---|---|
| Skriptart | **eingebettet** |
| Burst-Adapter | `vb/childlike_giggle` bei Gewicht **0.8** |
| Burst+Stop-DPO | 336 |
| Prompt-Form | **P0** — Grundform aus §43 — Hinweis als Etikett, Standarddauer |

## Was dabei herauskommt

| Maß | Wert | gegen Grundform |
|---|--:|--:|
| Trefferquote, Familie | **0.467** | +0.250 (t +2.8, 7/10) |
| Trefferquote, streng | 0.050 | — |
| konservativ (−1 sd Seed-Rauschen) | **0.398** | |
| Genuineness | 2.83 | |
| Blend | 3.89 | |
| WER (Parakeet) | 0.122 | |
| DNSMOS | 3.36 | |

## Wie oft erzeugen

Bei einer Trefferquote von 0.47 braucht es **4 Kandidaten**, damit mit 90 %
Wahrscheinlichkeit mindestens einer den Laut realisiert. Konservativ gerechnet (0.40): **5 Kandidaten**.

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
| bester Adapter | **neu** `bulk_mix_full` (echt + DramaBox Rang ≤ 1) ⚠ |
| Skalierungsfaktor | **1,00** |
| Skriptart | **eingebettet** |
| Stapel | **nur der Adapter**, ohne Produktions-Stapel |
| Trefferquote, Familie (grobe Tabelle) | **0,567** |
| dieselbe Zelle im **veröffentlichten 23-Gruppen-Schema** | 0,567 — bestes Rezept dort: `bulk_alone` / inline / w = 1,00 |
| Trefferquote, streng | 0,350 — aber in einer anderen Zelle: `bulk` (allein), allein stehend, w = 1,50 |
| Genuineness | 1,37 |
| WER (Parakeet) | 0,146, gepaart +0,015 gegen die eigene w = 0-Zelle |

**Entscheidung: das neue Rezept ersetzt das alte.** 0,567 gegen 0,470 familienweit, also mehr als eine Seed-Rausch-Standardabweichung (0,068) besser.

⚠ **Lizenz.** Dieser Adapter ist auf DramaBox-TTS-Audio mittrainiert; die LTX-2 Community Licence ist dafür **nicht geprüft** (§61). Solange das offen ist, bleibt das alte Rezept die freigegebene Rückfallvariante.

### Wie oft erzeugen (neu gerechnet)

Bei einer Trefferquote von 0,57 braucht es **3 Kandidaten**, damit mit 90 % Wahrscheinlichkeit mindestens einer den Laut realisiert. Konservativ gerechnet (0,50, eine Seed-Rausch-Standardabweichung abgezogen): **4 Kandidaten**.

Auswahl unter den Treffern nach Klang. Best-of-N bleibt der wirksamere Hebel als jede Stärkeänderung.

### Woher die Zahlen kommen

* **Messgerät:** `reward.RewardModel -> laion/vocal-burst-detector-v2` — dasselbe, das die Laufzeit selbst benutzt, und dasselbe, mit dem die Tabelle oben gemessen wurde.
* **Zweites Messgerät zur Kontrolle:** `laion/vocal-burst-detector-x2 (production, VoiceCLAP ensemble)`. Es kennt 16 der 45 Klassen; wo es diese Klasse kennt, steht sein Urteil in `VOCAL_BURSTS.md`. Keine Zeile mischt die beiden.
* **„Familie“** ist `burst_family.py` (md5 `19a0607b`), eine **gröbere** Einteilung als das veröffentlichte 23-Gruppen-Schema (`vm_groups.py` md5 `f83e3850`) — sie überschreitet dessen Grenzen, ist also systematisch großzügiger. Deshalb steht beides da.
* **„Streng“ ist streng bis auf 0,37 %:** `reward._same_class` ist ein Teilstring-Test, ein `Coughing` zählt also als Treffer für `cough`. Über 97.349 Ziel-Cues betrifft das 12 von 3.269 gezählten Erkennungen, **0** davon überschreiten eine 23-Gruppen-Grenze.

<!-- /vb_cls2:sec64 -->
