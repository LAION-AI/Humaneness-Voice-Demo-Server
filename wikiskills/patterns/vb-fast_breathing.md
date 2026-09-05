<!-- vb_grp:2026-09-05 -->

# vb/fast_breathing

> Stand 5. September 2026 · Gruppe `breath_fast` im 23-Gruppen-Schema · gemessen · eigener Adapter vorhanden: ja
>
> Gruppen-Mitglieder: `fast_breathing`, `heavy_breathing`, `pant`, `panting`

## Rezept

| | |
|---|---|
| Adapter | der nachtrainierte Klassen-Adapter (`vb_cls2/loras/bulk_mix_full`) |
| Gewicht | **1,00** |
| Skriptart | **eingebettet (inline)** |
| Best-of-N | **22** Kandidaten für 90 % (konservativ, eine Seed-Rausch-Standardabweichung abgezogen: 71) |

Best-of-N ist hier der größere Hebel als jede Stärkeänderung.


⚠ **Lizenz.** Dieser Adapter ist auf DramaBox-TTS-Audio mittrainiert; die LTX-2 Community Licence ist dafür **nicht geprüft** (§61). Solange das offen ist, bleibt der ausgelieferte Adapter (`shipped`) die freigegebene Rückfallvariante.

## Was dabei herauskommt

Gemessen mit `laion/vocal-burst-detector-x2` (Produktion, VoiceCLAP-Ensemble, 16 Klassen), Gruppenebene nach dem 23-Gruppen-Schema.

| Maß | Wert |
|---|--:|
| Trefferquote, **streng** (exakt dieselbe Klasse) | **0,000** |
| Trefferquote, **Gruppe** (irgendein Mitglied) | **0,100** |
| größengleiche Zufallskontrolle | 0,063 |
| netto über der Zufallskontrolle | 0,037 |
| Genuineness (nur berichtet, kein Tor) | 1,70 |
| WER (Parakeet), absolut | 0,052 |
| WER gepaart gegen die eigene w = 0-Zelle | -0,076 (Grenze +0,104) |

Dieselbe Klasse, die drei Wege nebeneinander (jeweils die beste Zelle unter w ≤ 1,5):

| Weg | Adapter | Form / w | Gruppe | streng |
|---|---|---|--:|--:|
| eigener Adapter | `percls` | inline / 1,00 | **0,100** | 0,000 |
| geliehen vom Gruppenmitglied | `bestmem` | inline / 1,00 | **0,033** | 0,000 |
| Gruppen-Adapter (gepoolt) | `grpfull` | solo / 0,50 | **0,067** | 0,000 |

Geliehen gegen eigen, gepaart bei gleicher Form und gleichem Gewicht: d = -0,0667, t = -1,50, n = 10.

## Warum die Zahl so ist

Die Klasse bleibt unter 0,15. Der Detektor sieht sie (Boden nicht gemessen), das Modell erzeugt sie aber selten. Best-of-N mit 22 Kandidaten ist der einzige wirksame Hebel.

## Wenn es nicht geht

Wenn dieses Etikett nicht trifft: die Gruppe `breath_fast` enthält `heavy_breathing`, `panting`. Der Adapter des stärksten gemessenen Mitglieds — `vb/panting` — ist für die ganze Gruppe eine belegte Alternative (dort gemessen: 0,100).

## Woher die Zahlen kommen

* **Messgerät:** `laion/vocal-burst-detector-x2` (Produktion, VoiceCLAP-Ensemble, 16 Klassen). Die beiden Detektoren sind **nicht** austauschbar; keine Zeile mischt sie.
* **Gruppen-Schema:** `vm_groups.py` md5 `f83e3850` (23 Gruppen, 117 Mitgliedsnamen).
* **Trägersatz:** `$SC/out/burst_dose2/prompt_sets.json`, 10 Prompts je (Skriptart, Klasse), Startwert hängt allein vom Prompt-Index ab — alle Arme ziehen dasselbe Rauschen.
* **Statistik:** die drei Stichproben eines Prompts werden zuerst gemittelt, n ist die Zahl der Prompts.
* **WER-Obergrenze:** w = 2,0 ist ausgeschlossen. Über die 28 Klassen der zehn zweiquelligen Gruppen reißen dort **alle vier** Adapter-Arme das Tor (nachtrainiert +0,167, geliehen +0,168, Gruppe-voll +0,123, Gruppe-25 % +0,109 gegen die Schranke +0,104). Bis w = 1,5 hält jeder Arm.
* Studie `vb_grp`, Zustand `~/reports/STATE_burst_group_lora.md`.
