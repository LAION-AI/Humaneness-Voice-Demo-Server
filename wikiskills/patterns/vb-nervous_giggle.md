# vbr/nervous_giggle

> Gemessen 2026-09-02 im vollen Server-Stapel, gepaart gegen dieselben 10 Trägersätze
> mit gleichem Seed. Protokoll §52, Studie `~/reports/burst_ext.md`.

## Rezept

| | |
|---|---|
| Skriptart | **allein stehend** |
| Burst-Adapter | `vbr/nervous_giggle` bei Gewicht **1.5** |
| Burst+Stop-DPO | keiner |
| Prompt-Form | **C_gl** — GENERAL-Zeile nennt Ursache und Wirkung des Lauts, **und** die angegebene Dauer ist verlängert |

## Was dabei herauskommt

| Maß | Wert | gegen Grundform |
|---|--:|--:|
| Trefferquote, Familie | **0.333** | +0.083 (t +1.2, 5/10) |
| Trefferquote, streng | 0.000 | — |
| konservativ (−1 sd Seed-Rauschen) | **0.265** | |
| Genuineness | 3.39 | |
| Blend | 5.10 | |
| WER (Parakeet) | 0.280 | |
| DNSMOS | 2.97 | |

## Wie oft erzeugen

Bei einer Trefferquote von 0.33 braucht es **6 Kandidaten**, damit mit 90 %
Wahrscheinlichkeit mindestens einer den Laut realisiert. Konservativ gerechnet (0.27): **8 Kandidaten**.

Auswahl unter den Treffern nach Klang; wenn mehrere sitzen, den mit der höchsten
Genuineness nehmen. Best-of-N ist hier der wirksamere Hebel als jede Stärkeänderung.

## Achtung: die Unterart trifft er nicht

Streng gemessen liegt diese Klasse bei 0.000, familien-gelockert bei 0.333.
Das Modell erzeugt zuverlässig einen Laut **derselben Familie**, aber nicht die
etikettierte Unterart. Wer auf genau dieser Unterart besteht, wird enttäuscht — den
gewünschten Charakter deshalb über die Emotionsanweisung steuern, nicht über das Etikett.

## Der Verlauf über die Stärke

Grundform: w 0.5: 0.28 · w 1.0: 0.30 · w 1.5: 0.27 · w 2.0: 0.20.

§43 hatte für diese Klasse 1.0 empfohlen und dort 0.400 gemessen.

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
| Trefferquote, Familie (grobe Tabelle) | **0,633** |
| dieselbe Zelle im **veröffentlichten 23-Gruppen-Schema** | 0,633 — bestes Rezept dort: `bulk` / inline / w = 1,50 |
| Trefferquote, streng | 0,000 — in **keiner** Zelle über null |
| Genuineness | 2,24 |
| WER (Parakeet) | 0,152, gepaart +0,029 gegen die eigene w = 0-Zelle |

**Entscheidung: das neue Rezept ersetzt das alte.** 0,633 gegen 0,330 familienweit, also mehr als eine Seed-Rausch-Standardabweichung (0,068) besser.

⚠ **Lizenz.** Dieser Adapter ist auf DramaBox-TTS-Audio mittrainiert; die LTX-2 Community Licence ist dafür **nicht geprüft** (§61). Solange das offen ist, bleibt das alte Rezept die freigegebene Rückfallvariante.

### Wie oft erzeugen (neu gerechnet)

Bei einer Trefferquote von 0,63 braucht es **3 Kandidaten**, damit mit 90 % Wahrscheinlichkeit mindestens einer den Laut realisiert. Konservativ gerechnet (0,57, eine Seed-Rausch-Standardabweichung abgezogen): **3 Kandidaten**.

Auswahl unter den Treffern nach Klang. Best-of-N bleibt der wirksamere Hebel als jede Stärkeänderung.

### Woher die Zahlen kommen

* **Messgerät:** `reward.RewardModel -> laion/vocal-burst-detector-v2` — dasselbe, das die Laufzeit selbst benutzt, und dasselbe, mit dem die Tabelle oben gemessen wurde.
* **Zweites Messgerät zur Kontrolle:** `laion/vocal-burst-detector-x2 (production, VoiceCLAP ensemble)`. Es kennt 16 der 45 Klassen; wo es diese Klasse kennt, steht sein Urteil in `VOCAL_BURSTS.md`. Keine Zeile mischt die beiden.
* **„Familie“** ist `burst_family.py` (md5 `19a0607b`), eine **gröbere** Einteilung als das veröffentlichte 23-Gruppen-Schema (`vm_groups.py` md5 `f83e3850`) — sie überschreitet dessen Grenzen, ist also systematisch großzügiger. Deshalb steht beides da.
* **„Streng“ ist streng bis auf 0,37 %:** `reward._same_class` ist ein Teilstring-Test, ein `Coughing` zählt also als Treffer für `cough`. Über 97.349 Ziel-Cues betrifft das 12 von 3.269 gezählten Erkennungen, **0** davon überschreiten eine 23-Gruppen-Grenze.

<!-- /vb_cls2:sec64 -->
