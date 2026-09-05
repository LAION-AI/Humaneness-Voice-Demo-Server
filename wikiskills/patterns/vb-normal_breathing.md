<!-- vb_grp:2026-09-05 -->

# vb/normal_breathing

> Stand 5. September 2026 · Gruppe `breath_calm` im 23-Gruppen-Schema · gemessen · eigener Adapter vorhanden: ja
>
> Gruppen-Mitglieder: `deep_breath`, `deep_breathing`, `normal_breathing`, `slow_breathing`

## Rezept

| | |
|---|---|
| Adapter | der ausgelieferte Klassen-Adapter |
| Gewicht | **1,50** |
| Skriptart | **eingebettet (inline)** |
| Best-of-N | **68** Kandidaten für 90 % (konservativ, eine Seed-Rausch-Standardabweichung abgezogen: 2302) |

Best-of-N ist hier der größere Hebel als jede Stärkeänderung.

## Was dabei herauskommt

Gemessen mit `laion/vocal-burst-detector-x2` (Produktion, VoiceCLAP-Ensemble, 16 Klassen), Gruppenebene nach dem 23-Gruppen-Schema.

| Maß | Wert |
|---|--:|
| Trefferquote, **streng** (exakt dieselbe Klasse) | **0,000** |
| Trefferquote, **Gruppe** (irgendein Mitglied) | **0,033** |
| größengleiche Zufallskontrolle | 0,062 |
| netto über der Zufallskontrolle | -0,029 |
| Genuineness (nur berichtet, kein Tor) | 2,11 |
| WER (Parakeet), absolut | 0,054 |
| WER gepaart gegen die eigene w = 0-Zelle | -0,109 (Grenze +0,104) |

Dieselbe Klasse, die drei Wege nebeneinander (jeweils die beste Zelle unter w ≤ 1,5):

| Weg | Adapter | Form / w | Gruppe | streng |
|---|---|---|--:|--:|
| eigener Adapter | `shipped` | inline / 1,50 | **0,033** | 0,000 |
| geliehen vom Gruppenmitglied | `bestmem` | inline / 0,50 | **0,000** | 0,000 |
| Gruppen-Adapter (gepoolt) | `grp25_alone` | inline / 1,00 | **0,033** | 0,000 |

Geliehen gegen eigen, gepaart bei gleicher Form und gleichem Gewicht: d = 0,0000, t = —, n = 10.

## Warum die Zahl so ist

Die Klasse bleibt unter 0,15. Der Detektor sieht sie (Boden nicht gemessen), das Modell erzeugt sie aber selten. Best-of-N mit 68 Kandidaten ist der einzige wirksame Hebel.

## Wenn es nicht geht

Wenn dieses Etikett nicht trifft: die Gruppe `breath_calm` enthält `deep_breath`, `deep_breathing`. Der Adapter des stärksten gemessenen Mitglieds — `vb/deep_breath` — ist für die ganze Gruppe eine belegte Alternative (dort gemessen: 0,200).

## Woher die Zahlen kommen

* **Messgerät:** `laion/vocal-burst-detector-x2` (Produktion, VoiceCLAP-Ensemble, 16 Klassen). Die beiden Detektoren sind **nicht** austauschbar; keine Zeile mischt sie.
* **Gruppen-Schema:** `vm_groups.py` md5 `f83e3850` (23 Gruppen, 117 Mitgliedsnamen).
* **Trägersatz:** `$SC/out/burst_dose2/prompt_sets.json`, 10 Prompts je (Skriptart, Klasse), Startwert hängt allein vom Prompt-Index ab — alle Arme ziehen dasselbe Rauschen.
* **Statistik:** die drei Stichproben eines Prompts werden zuerst gemittelt, n ist die Zahl der Prompts.
* **WER-Obergrenze:** w = 2,0 ist ausgeschlossen. Über die 28 Klassen der zehn zweiquelligen Gruppen reißen dort **alle vier** Adapter-Arme das Tor (nachtrainiert +0,167, geliehen +0,168, Gruppe-voll +0,123, Gruppe-25 % +0,109 gegen die Schranke +0,104). Bis w = 1,5 hält jeder Arm.
* Studie `vb_grp`, Zustand `~/reports/STATE_burst_group_lora.md`.
