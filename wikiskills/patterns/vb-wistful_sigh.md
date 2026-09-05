# vb/wistful_sigh

> Gemessen 2026-09-02 im vollen Server-Stapel, gepaart gegen dieselben 10 Trägersätze
> mit gleichem Seed. Protokoll §52, Studie `~/reports/burst_ext.md`.

## Rezept

| | |
|---|---|
| Skriptart | **eingebettet** |
| Burst-Adapter | `vb/wistful_sigh` bei Gewicht **1.0** |
| Burst+Stop-DPO | keiner |
| Prompt-Form | **P0** — Grundform aus §43 — Hinweis als Etikett, Standarddauer |

## Was dabei herauskommt

| Maß | Wert | gegen Grundform |
|---|--:|--:|
| Trefferquote, Familie | **0.550** | +0.117 (t +2.7, 5/10) |
| Trefferquote, streng | 0.067 | — |
| konservativ (−1 sd Seed-Rauschen) | **0.482** | |
| Genuineness | 2.58 | |
| Blend | 5.24 | |
| WER (Parakeet) | 0.107 | |
| DNSMOS | 3.37 | |

## Wie oft erzeugen

Bei einer Trefferquote von 0.55 braucht es **3 Kandidaten**, damit mit 90 %
Wahrscheinlichkeit mindestens einer den Laut realisiert. Konservativ gerechnet (0.48): **4 Kandidaten**.

Auswahl unter den Treffern nach Klang; wenn mehrere sitzen, den mit der höchsten
Genuineness nehmen. Best-of-N ist hier der wirksamere Hebel als jede Stärkeänderung.

## Der Verlauf über die Stärke

Grundform: w 0.5: 0.42 · w 1.0: 0.55 · w 1.5: 0.45 · w 2.0: 0.30.

§43 hatte für diese Klasse 1.0 empfohlen und dort 0.633 gemessen.

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
| Skalierungsfaktor | **1,00** |
| Skriptart | **eingebettet** |
| Stapel | voller Produktions-Stapel |
| Trefferquote, Familie (grobe Tabelle) | **0,633** |
| dieselbe Zelle im **veröffentlichten 23-Gruppen-Schema** | 0,633 — bestes Rezept dort: `shipped` / inline / w = 1,00 |
| Trefferquote, streng | 0,167 — aber in einer anderen Zelle: `shipped`, allein stehend, w = 2,00 |
| Genuineness | 2,63 |
| WER (Parakeet) | 0,115, gepaart +0,024 gegen die eigene w = 0-Zelle |
| Detektor-Boden (echte Sprache) | streng 0,143, Familie 0,393 — **nicht belastbar** (n < 30) |

**Die strenge Quote ist hier nach oben gedeckelt.** Der Produktionsdetektor erkennt diese Klasse auf echter Sprache nur zu 14,3 % (familienweit 39,3 %). Eine strenge Trefferquote unterhalb dieses Werts ist eine **Ablesung am Messgerät, kein Urteil über den Adapter**. Für diese Klasse ist die familienweite Quote die primäre Zahl.

**Entscheidung: das neue Rezept ersetzt das alte.** 0,633 gegen 0,550 familienweit, also mehr als eine Seed-Rausch-Standardabweichung (0,068) besser.

### Wie oft erzeugen (neu gerechnet)

Bei einer Trefferquote von 0,63 braucht es **3 Kandidaten**, damit mit 90 % Wahrscheinlichkeit mindestens einer den Laut realisiert. Konservativ gerechnet (0,57, eine Seed-Rausch-Standardabweichung abgezogen): **3 Kandidaten**.

Auswahl unter den Treffern nach Klang. Best-of-N bleibt der wirksamere Hebel als jede Stärkeänderung.

### Woher die Zahlen kommen

* **Messgerät:** `reward.RewardModel -> laion/vocal-burst-detector-v2` — dasselbe, das die Laufzeit selbst benutzt, und dasselbe, mit dem die Tabelle oben gemessen wurde.
* **Zweites Messgerät zur Kontrolle:** `laion/vocal-burst-detector-x2 (production, VoiceCLAP ensemble)`. Es kennt 16 der 45 Klassen; wo es diese Klasse kennt, steht sein Urteil in `VOCAL_BURSTS.md`. Keine Zeile mischt die beiden.
* **„Familie“** ist `burst_family.py` (md5 `19a0607b`), eine **gröbere** Einteilung als das veröffentlichte 23-Gruppen-Schema (`vm_groups.py` md5 `f83e3850`) — sie überschreitet dessen Grenzen, ist also systematisch großzügiger. Deshalb steht beides da.
* **„Streng“ ist streng bis auf 0,37 %:** `reward._same_class` ist ein Teilstring-Test, ein `Coughing` zählt also als Treffer für `cough`. Über 97.349 Ziel-Cues betrifft das 12 von 3.269 gezählten Erkennungen, **0** davon überschreiten eine 23-Gruppen-Grenze.

<!-- /vb_cls2:sec64 -->
