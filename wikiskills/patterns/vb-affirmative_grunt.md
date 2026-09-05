<!-- vb_grp:2026-09-05 -->

# vb/affirmative_grunt

> Stand 5. September 2026 · Gruppe `grunt` im 23-Gruppen-Schema · gemessen · eigener Adapter vorhanden: ja
>
> Gruppen-Mitglieder: `affirmative_grunt`, `effort_grunt`

## Rezept

| | |
|---|---|
| Adapter | der nachtrainierte Klassen-Adapter (`vb_cls2/loras/bulk_mix_full`) |
| Gewicht | **1,50** |
| Skriptart | **eingebettet (inline)** |
| Best-of-N | **6** Kandidaten für 90 % (konservativ, eine Seed-Rausch-Standardabweichung abgezogen: 7) |

Best-of-N ist hier der größere Hebel als jede Stärkeänderung.


⚠ **Lizenz.** Dieser Adapter ist auf DramaBox-TTS-Audio mittrainiert; die LTX-2 Community Licence ist dafür **nicht geprüft** (§61). Solange das offen ist, bleibt der ausgelieferte Adapter (`shipped`) die freigegebene Rückfallvariante.

## Was dabei herauskommt

Gemessen mit `laion/vocal-burst-detector-x2` (Produktion, VoiceCLAP-Ensemble, 16 Klassen), Gruppenebene nach dem 23-Gruppen-Schema.

| Maß | Wert |
|---|--:|
| Trefferquote, **streng** (exakt dieselbe Klasse) | **0,367** |
| Trefferquote, **Gruppe** (irgendein Mitglied) | **0,367** |
| größengleiche Zufallskontrolle | 0,378 |
| netto über der Zufallskontrolle | -0,012 |
| Genuineness (nur berichtet, kein Tor) | 2,45 |
| WER (Parakeet), absolut | 0,233 |
| WER gepaart gegen die eigene w = 0-Zelle | 0,033 (Grenze +0,104) |
| **Detektor-Boden**, echte Sprache, streng | 0,700 |

Dieselbe Klasse, die drei Wege nebeneinander (jeweils die beste Zelle unter w ≤ 1,5):

| Weg | Adapter | Form / w | Gruppe | streng |
|---|---|---|--:|--:|
| eigener Adapter | `percls` | inline / 1,50 | **0,367** | 0,367 |
| geliehen vom Gruppenmitglied | `bestmem` | solo / 1,00 | **0,133** | 0,133 |
| Gruppen-Adapter (gepoolt) | `grpfull_alone` | solo / 1,50 | **0,167** | 0,167 |

Geliehen gegen eigen, gepaart bei gleicher Form und gleichem Gewicht: d = -0,0333, t = -0,56, n = 10.

## Warum die Zahl so ist

Die Klasse ist erreichbar; der Wert oben ist unter der WER-Obergrenze gemessen und hält das Tor.

## Wenn es nicht geht

Wenn dieses Etikett nicht trifft: die Gruppe `grunt` enthält `effort_grunt`. Der Adapter des stärksten gemessenen Mitglieds — `vb/effort_grunt` — ist für die ganze Gruppe eine belegte Alternative (dort gemessen: 0,367).

## Woher die Zahlen kommen

* **Messgerät:** `laion/vocal-burst-detector-x2` (Produktion, VoiceCLAP-Ensemble, 16 Klassen). Die beiden Detektoren sind **nicht** austauschbar; keine Zeile mischt sie.
* **Gruppen-Schema:** `vm_groups.py` md5 `f83e3850` (23 Gruppen, 117 Mitgliedsnamen).
* **Trägersatz:** `$SC/out/burst_dose2/prompt_sets.json`, 10 Prompts je (Skriptart, Klasse), Startwert hängt allein vom Prompt-Index ab — alle Arme ziehen dasselbe Rauschen.
* **Statistik:** die drei Stichproben eines Prompts werden zuerst gemittelt, n ist die Zahl der Prompts.
* **WER-Obergrenze:** w = 2,0 ist ausgeschlossen. Über die 28 Klassen der zehn zweiquelligen Gruppen reißen dort **alle vier** Adapter-Arme das Tor (nachtrainiert +0,167, geliehen +0,168, Gruppe-voll +0,123, Gruppe-25 % +0,109 gegen die Schranke +0,104). Bis w = 1,5 hält jeder Arm.
* Studie `vb_grp`, Zustand `~/reports/STATE_burst_group_lora.md`.
