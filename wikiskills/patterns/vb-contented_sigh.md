# vb/contented_sigh

> Gemessen 2026-09-02 im vollen Server-Stapel, gepaart gegen dieselben 10 Trägersätze
> mit gleichem Seed. Protokoll §51, Studie `~/reports/burst_levers.md`.

## Rezept

| | |
|---|---|
| Skriptart | **eingebettet** |
| Burst-Adapter | `vb/contented_sigh` bei Gewicht **1.5** |
| Burst+Stop-DPO | keiner |
| Prompt-Form | **C_gl** — C_gl |

## Was dabei herauskommt

| Maß | Wert | gegen Grundform |
|---|--:|--:|
| Trefferquote, Familie | **0.683** | +0.233 (t +2.1, 7/10) |
| Trefferquote, streng | 0.683 | — |
| konservativ (−1 sd Seed-Rauschen) | **0.615** | |
| Genuineness | 2.55 | |
| Blend | 5.16 | |
| WER (Parakeet) | 0.126 | |
| DNSMOS | 3.32 | |

## Wie oft erzeugen

Bei einer Trefferquote von 0.68 braucht es **3 Kandidaten**, damit mit 90 %
Wahrscheinlichkeit mindestens einer den Laut realisiert. Konservativ gerechnet (0.61): **3 Kandidaten**.

Auswahl unter den Treffern nach Klang; wenn mehrere sitzen, den mit der höchsten
Genuineness nehmen. Best-of-N ist hier der wirksamere Hebel als jede Stärkeänderung.

<!-- vb_cls2:sec64 -->

## Nachtrag §64 (2026-09-04)

Diese Klasse war in der Studie `vb_cls2` **nicht im Umfang** — sie erreicht die Zeilenschwelle von 100 kombinierten Trainingszeilen nicht, es gibt also keinen neuen Adapter und keine neue Messung. **Das Rezept oben gilt unverändert weiter**, einschließlich seiner Kandidatenzahl.

<!-- /vb_cls2:sec64 -->

<!-- vb_grp:2026-09-05 -->

## Nachtrag 2026-09-05 — Gruppen, geliehene Adapter, WER-Obergrenze

> Studie `vb_grp`. **Das bestehende Rezept oben bleibt gültig**, wenn es besser gemessen hat: die älteren Studien variieren die *Prompt-Form* und werden von einer Adapter-Messung nicht überholt. Neu ist hier, was die Gruppe beiträgt und wo die WER-Obergrenze liegt.

## Rezept

Diese Bezeichnung wurde **nicht einzeln gemessen**. Sie gehört zur Gruppe `sigh_pos`; dort sind gemessen: `relief_sigh`, `wistful_sigh`.


Wer diesen Laut braucht, nimmt den Adapter des stärksten gemessenen Geschwisters, `vb/wistful_sigh`, mit der dort belegten Einstellung — siehe `vb-wistful_sigh.md` (dort gemessen: 0,200 auf Gruppenebene).


## Warum die Zahl so ist

Für diese Bezeichnung selbst gibt es **keine Messung**. Was unten steht, gilt für das gemessene Gruppenmitglied, nicht für dieses Etikett. Ob der Detektor diese Schreibweise überhaupt jemals vergibt, ist ebenfalls ungeprüft.

## Wenn es nicht geht

Wenn dieses Etikett nicht trifft: die Gruppe `sigh_pos` enthält `relief_sigh`, `wistful_sigh`. Der Adapter des stärksten gemessenen Mitglieds — `vb/wistful_sigh` — ist für die ganze Gruppe eine belegte Alternative (dort gemessen: 0,200).

## Woher die Zahlen kommen

* **Messgerät:** `laion/vocal-burst-detector-x2` (Produktion, VoiceCLAP-Ensemble, 16 Klassen). Die beiden Detektoren sind **nicht** austauschbar; keine Zeile mischt sie.
* **Gruppen-Schema:** `vm_groups.py` md5 `f83e3850` (23 Gruppen, 117 Mitgliedsnamen).
* **Trägersatz:** `$SC/out/burst_dose2/prompt_sets.json`, 10 Prompts je (Skriptart, Klasse), Startwert hängt allein vom Prompt-Index ab — alle Arme ziehen dasselbe Rauschen.
* **Statistik:** die drei Stichproben eines Prompts werden zuerst gemittelt, n ist die Zahl der Prompts.
* **WER-Obergrenze:** w = 2,0 ist ausgeschlossen. Über die 28 Klassen der zehn zweiquelligen Gruppen reißen dort **alle vier** Adapter-Arme das Tor (nachtrainiert +0,167, geliehen +0,168, Gruppe-voll +0,123, Gruppe-25 % +0,109 gegen die Schranke +0,104). Bis w = 1,5 hält jeder Arm.
* Studie `vb_grp`, Zustand `~/reports/STATE_burst_group_lora.md`.

<!-- /vb_grp:2026-09-05 -->
