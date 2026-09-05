# vbr/whispered_mumble

> Gemessen 2026-09-02 im vollen Server-Stapel, gepaart gegen dieselben 10 Trägersätze
> mit gleichem Seed. Protokoll §52, Studie `~/reports/burst_ext.md`.

## Rezept

| | |
|---|---|
| Skriptart | **eingebettet** |
| Burst-Adapter | `vbr/whispered_mumble` bei Gewicht **0.25** |
| Burst+Stop-DPO | keiner |
| Prompt-Form | **P0** — Grundform aus §43 — Hinweis als Etikett, Standarddauer |

## Was dabei herauskommt

| Maß | Wert | gegen Grundform |
|---|--:|--:|
| Trefferquote, Familie | **0.233** | +0.050 (t +1.2, 3/10) |
| Trefferquote, streng | 0.000 | — |
| konservativ (−1 sd Seed-Rauschen) | **0.165** | |
| Genuineness | 2.70 | |
| Blend | 5.24 | |
| WER (Parakeet) | 0.223 | |
| DNSMOS | 3.30 | |

## Wie oft erzeugen

Bei einer Trefferquote von 0.23 braucht es **9 Kandidaten**, damit mit 90 %
Wahrscheinlichkeit mindestens einer den Laut realisiert. Konservativ gerechnet (0.17): **13 Kandidaten**.

Auswahl unter den Treffern nach Klang; wenn mehrere sitzen, den mit der höchsten
Genuineness nehmen. Best-of-N ist hier der wirksamere Hebel als jede Stärkeänderung.

## Achtung: die Unterart trifft er nicht

Streng gemessen liegt diese Klasse bei 0.000, familien-gelockert bei 0.233.
Das Modell erzeugt zuverlässig einen Laut **derselben Familie**, aber nicht die
etikettierte Unterart. Wer auf genau dieser Unterart besteht, wird enttäuscht — den
gewünschten Charakter deshalb über die Emotionsanweisung steuern, nicht über das Etikett.

## Der Verlauf über die Stärke

Grundform: w 0.25: 0.23 · w 0.8: 0.15 · w 1.3: 0.12.

§43 hatte für diese Klasse 0.25 empfohlen und dort 0.300 gemessen.

<!-- vb_cls2:sec64 -->

## Nachtrag §64 (2026-09-04)

Diese Klasse war in der Studie `vb_cls2` **nicht im Umfang** — sie erreicht die Zeilenschwelle von 100 kombinierten Trainingszeilen nicht, es gibt also keinen neuen Adapter und keine neue Messung. **Das Rezept oben gilt unverändert weiter**, einschließlich seiner Kandidatenzahl.

<!-- /vb_cls2:sec64 -->

<!-- vb_grp:2026-09-05 -->

## Nachtrag 2026-09-05 — Gruppen, geliehene Adapter, WER-Obergrenze

> Studie `vb_grp`. **Das bestehende Rezept oben bleibt gültig**, wenn es besser gemessen hat: die älteren Studien variieren die *Prompt-Form* und werden von einer Adapter-Messung nicht überholt. Neu ist hier, was die Gruppe beiträgt und wo die WER-Obergrenze liegt.

## Rezept

Diese Bezeichnung wurde **nicht einzeln gemessen**. Sie gehört zur Gruppe `hum`; dort sind gemessen: `humming`, `purr`, `soft_hum`.


Wer diesen Laut braucht, nimmt den Adapter des stärksten gemessenen Geschwisters, `vb/humming`, mit der dort belegten Einstellung — siehe `vb-humming.md` (dort gemessen: 0,400 auf Gruppenebene).


## Warum die Zahl so ist

Für diese Bezeichnung selbst gibt es **keine Messung**. Was unten steht, gilt für das gemessene Gruppenmitglied, nicht für dieses Etikett. Ob der Detektor diese Schreibweise überhaupt jemals vergibt, ist ebenfalls ungeprüft.

## Wenn es nicht geht

Wenn dieses Etikett nicht trifft: die Gruppe `hum` enthält `humming`, `purr`, `soft_hum`. Der Adapter des stärksten gemessenen Mitglieds — `vb/humming` — ist für die ganze Gruppe eine belegte Alternative (dort gemessen: 0,400).

## Woher die Zahlen kommen

* **Messgerät:** `laion/vocal-burst-detector-x2` (Produktion, VoiceCLAP-Ensemble, 16 Klassen). Die beiden Detektoren sind **nicht** austauschbar; keine Zeile mischt sie.
* **Gruppen-Schema:** `vm_groups.py` md5 `f83e3850` (23 Gruppen, 117 Mitgliedsnamen).
* **Trägersatz:** `$SC/out/burst_dose2/prompt_sets.json`, 10 Prompts je (Skriptart, Klasse), Startwert hängt allein vom Prompt-Index ab — alle Arme ziehen dasselbe Rauschen.
* **Statistik:** die drei Stichproben eines Prompts werden zuerst gemittelt, n ist die Zahl der Prompts.
* **WER-Obergrenze:** w = 2,0 ist ausgeschlossen. Über die 28 Klassen der zehn zweiquelligen Gruppen reißen dort **alle vier** Adapter-Arme das Tor (nachtrainiert +0,167, geliehen +0,168, Gruppe-voll +0,123, Gruppe-25 % +0,109 gegen die Schranke +0,104). Bis w = 1,5 hält jeder Arm.
* Studie `vb_grp`, Zustand `~/reports/STATE_burst_group_lora.md`.

<!-- /vb_grp:2026-09-05 -->
