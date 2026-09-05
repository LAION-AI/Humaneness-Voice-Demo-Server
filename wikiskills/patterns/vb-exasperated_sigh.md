# vb/exasperated_sigh

> Gemessen 2026-09-02 im vollen Server-Stapel, gepaart gegen dieselben 10 Trägersätze
> mit gleichem Seed. Protokoll §52, Studie `~/reports/burst_ext.md`.

## Rezept

| | |
|---|---|
| Skriptart | **eingebettet** |
| Burst-Adapter | `vb/exasperated_sigh` bei Gewicht **1.25** |
| Burst+Stop-DPO | keiner |
| Prompt-Form | **P0** — Grundform aus §43 — Hinweis als Etikett, Standarddauer |

## Was dabei herauskommt

| Maß | Wert | gegen Grundform |
|---|--:|--:|
| Trefferquote, Familie | **0.450** | +0.133 (t +1.6, 7/10) |
| Trefferquote, streng | 0.050 | — |
| konservativ (−1 sd Seed-Rauschen) | **0.382** | |
| Genuineness | 2.36 | |
| Blend | 5.46 | |
| WER (Parakeet) | 0.110 | |
| DNSMOS | 3.29 | |

## Wie oft erzeugen

Bei einer Trefferquote von 0.45 braucht es **4 Kandidaten**, damit mit 90 %
Wahrscheinlichkeit mindestens einer den Laut realisiert. Konservativ gerechnet (0.38): **5 Kandidaten**.

Auswahl unter den Treffern nach Klang; wenn mehrere sitzen, den mit der höchsten
Genuineness nehmen. Best-of-N ist hier der wirksamere Hebel als jede Stärkeänderung.

## Der Verlauf über die Stärke

Grundform: w 0.8: 0.42 · w 1.25: 0.45 · w 1.8: 0.37 · w 2.3: 0.38.

§43 hatte für diese Klasse 1.25 empfohlen und dort 0.467 gemessen.

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
| Skalierungsfaktor | **1,00** |
| Skriptart | **eingebettet** |
| Stapel | voller Produktions-Stapel |
| Trefferquote, Familie (grobe Tabelle) | **0,833** |
| dieselbe Zelle im **veröffentlichten 23-Gruppen-Schema** | 0,200 — bestes Rezept dort: `dose25` / inline / w = 1,50 |
| Trefferquote, streng | 0,067 — aber in einer anderen Zelle: `shipped`, eingebettet, w = 1,50 |
| Genuineness | 1,60 |
| WER (Parakeet) | 0,113, gepaart -0,108 gegen die eigene w = 0-Zelle |
| Detektor-Boden (echte Sprache) | streng 0,226, Familie 0,340 |

**Die strenge Quote ist hier nach oben gedeckelt.** Der Produktionsdetektor erkennt diese Klasse auf echter Sprache nur zu 22,6 % (familienweit 34,0 %). Eine strenge Trefferquote unterhalb dieses Werts ist eine **Ablesung am Messgerät, kein Urteil über den Adapter**. Für diese Klasse ist die familienweite Quote die primäre Zahl.

**Entscheidung: das neue Rezept ersetzt das alte.** 0,833 gegen 0,450 familienweit, also mehr als eine Seed-Rausch-Standardabweichung (0,068) besser.

⚠ **Lizenz.** Dieser Adapter ist auf DramaBox-TTS-Audio mittrainiert; die LTX-2 Community Licence ist dafür **nicht geprüft** (§61). Solange das offen ist, bleibt das alte Rezept die freigegebene Rückfallvariante.

### Wie oft erzeugen (neu gerechnet)

Bei einer Trefferquote von 0,83 braucht es **2 Kandidaten**, damit mit 90 % Wahrscheinlichkeit mindestens einer den Laut realisiert. Konservativ gerechnet (0,77, eine Seed-Rausch-Standardabweichung abgezogen): **2 Kandidaten**.

Auswahl unter den Treffern nach Klang. Best-of-N bleibt der wirksamere Hebel als jede Stärkeänderung.

### Woher die Zahlen kommen

* **Messgerät:** `reward.RewardModel -> laion/vocal-burst-detector-v2` — dasselbe, das die Laufzeit selbst benutzt, und dasselbe, mit dem die Tabelle oben gemessen wurde.
* **Zweites Messgerät zur Kontrolle:** `laion/vocal-burst-detector-x2 (production, VoiceCLAP ensemble)`. Es kennt 16 der 45 Klassen; wo es diese Klasse kennt, steht sein Urteil in `VOCAL_BURSTS.md`. Keine Zeile mischt die beiden.
* **„Familie“** ist `burst_family.py` (md5 `19a0607b`), eine **gröbere** Einteilung als das veröffentlichte 23-Gruppen-Schema (`vm_groups.py` md5 `f83e3850`) — sie überschreitet dessen Grenzen, ist also systematisch großzügiger. Deshalb steht beides da.
* **„Streng“ ist streng bis auf 0,37 %:** `reward._same_class` ist ein Teilstring-Test, ein `Coughing` zählt also als Treffer für `cough`. Über 97.349 Ziel-Cues betrifft das 12 von 3.269 gezählten Erkennungen, **0** davon überschreiten eine 23-Gruppen-Grenze.

<!-- /vb_cls2:sec64 -->
