<!-- vb_grp:2026-09-05 -->

# vb/yawn

> Stand 5. September 2026 · Gruppe `yawn` im 23-Gruppen-Schema · gemessen · eigener Adapter vorhanden: ja
>
> Gruppen-Mitglieder: `yawn`

## Rezept

| | |
|---|---|
| Adapter | der ausgelieferte Klassen-Adapter |
| Gewicht | **1,50** |
| Skriptart | **allein stehend (solo)** |
| Best-of-N | **34** Kandidaten für 90 % (konservativ, eine Seed-Rausch-Standardabweichung abgezogen: 2302) |

Best-of-N ist hier der größere Hebel als jede Stärkeänderung.

## Was dabei herauskommt

Gemessen mit `laion/vocal-burst-detector-x2` (Produktion, VoiceCLAP-Ensemble, 16 Klassen), Gruppenebene nach dem 23-Gruppen-Schema.

| Maß | Wert |
|---|--:|
| Trefferquote, **streng** (exakt dieselbe Klasse) | **0,067** |
| Trefferquote, **Gruppe** (irgendein Mitglied) | **0,067** — *Gruppe = streng, die Gruppe hat nur diese gemessene Klasse* |
| größengleiche Zufallskontrolle | 0,067 |
| netto über der Zufallskontrolle | 0,000 |
| Genuineness (nur berichtet, kein Tor) | 3,15 |
| WER (Parakeet), absolut | 0,313 |
| WER gepaart gegen die eigene w = 0-Zelle | 0,013 (Grenze +0,104) |
| **Detektor-Boden**, echte Sprache, streng | 0,460 |

Dieselbe Klasse, die drei Wege nebeneinander (jeweils die beste Zelle unter w ≤ 1,5):

| Weg | Adapter | Form / w | Gruppe | streng |
|---|---|---|--:|--:|
| eigener Adapter | `shipped` | solo / 1,50 | **0,067** | 0,067 |
| geliehen vom Gruppenmitglied | `bestmem_alone` | inline / 1,50 | **0,033** | 0,033 |
| Gruppen-Adapter (gepoolt) | `grp25` | inline / 1,50 | **0,067** | 0,067 |

Geliehen gegen eigen, gepaart bei gleicher Form und gleichem Gewicht: d = 0,0000, t = —, n = 10.

## Warum die Zahl so ist

Die Klasse bleibt unter 0,15. Der Detektor sieht sie (Boden 0,460), das Modell erzeugt sie aber selten. Best-of-N mit 34 Kandidaten ist der einzige wirksame Hebel.

*Hinweis:* Diese Gruppe enthält nur eine gemessene Klasse. Ihre Gruppen-Trefferquote ist deshalb **per Konstruktion** gleich der strengen; eine Null dort ist kein Beleg über die Gruppierung.

## Wenn es nicht geht

Diese Gruppe hat kein zweites gemessenes Mitglied, auf das man ausweichen könnte. Wenn das Etikett nicht trifft, bleibt Best-of-N oder der Verzicht auf die Anforderung.

## Woher die Zahlen kommen

* **Messgerät:** `laion/vocal-burst-detector-x2` (Produktion, VoiceCLAP-Ensemble, 16 Klassen). Die beiden Detektoren sind **nicht** austauschbar; keine Zeile mischt sie.
* **Gruppen-Schema:** `vm_groups.py` md5 `f83e3850` (23 Gruppen, 117 Mitgliedsnamen).
* **Trägersatz:** `$SC/out/burst_dose2/prompt_sets.json`, 10 Prompts je (Skriptart, Klasse), Startwert hängt allein vom Prompt-Index ab — alle Arme ziehen dasselbe Rauschen.
* **Statistik:** die drei Stichproben eines Prompts werden zuerst gemittelt, n ist die Zahl der Prompts.
* **WER-Obergrenze:** w = 2,0 ist ausgeschlossen. Über die 28 Klassen der zehn zweiquelligen Gruppen reißen dort **alle vier** Adapter-Arme das Tor (nachtrainiert +0,167, geliehen +0,168, Gruppe-voll +0,123, Gruppe-25 % +0,109 gegen die Schranke +0,104). Bis w = 1,5 hält jeder Arm.
* Studie `vb_grp`, Zustand `~/reports/STATE_burst_group_lora.md`.
