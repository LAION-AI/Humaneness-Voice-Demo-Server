<!-- vb_grp:2026-09-05 -->

# vb/hiss

> Stand 5. September 2026 · Gruppe `hiss` im 23-Gruppen-Schema · gemessen · eigener Adapter vorhanden: ja
>
> Gruppen-Mitglieder: `hiss`

## Rezept

| | |
|---|---|
| Adapter | der nachtrainierte Klassen-Adapter (`vb_cls2/loras/bulk_mix_full`) |
| Gewicht | **1,00** |
| Skriptart | **allein stehend (solo)** |
| Best-of-N | **68** Kandidaten für 90 % (konservativ, eine Seed-Rausch-Standardabweichung abgezogen: 2302) |

Best-of-N ist hier der größere Hebel als jede Stärkeänderung.


⚠ **Lizenz.** Dieser Adapter ist auf DramaBox-TTS-Audio mittrainiert; die LTX-2 Community Licence ist dafür **nicht geprüft** (§61). Solange das offen ist, bleibt der ausgelieferte Adapter (`shipped`) die freigegebene Rückfallvariante.

## Was dabei herauskommt

Gemessen mit `laion/vocal-burst-detector-v2` (83 Klassen, das Instrument der Laufzeit), Gruppenebene nach dem 23-Gruppen-Schema.

| Maß | Wert |
|---|--:|
| Trefferquote, **streng** (exakt dieselbe Klasse) | **0,033** |
| Trefferquote, **Gruppe** (irgendein Mitglied) | **0,033** — *Gruppe = streng, die Gruppe hat nur diese gemessene Klasse* |
| größengleiche Zufallskontrolle | 0,033 |
| netto über der Zufallskontrolle | 0,000 |
| Genuineness (nur berichtet, kein Tor) | 2,16 |
| WER (Parakeet), absolut | 0,300 |
| WER gepaart gegen die eigene w = 0-Zelle | -0,153 (Grenze +0,104) |

Dieselbe Klasse, die drei Wege nebeneinander (jeweils die beste Zelle unter w ≤ 1,5):

| Weg | Adapter | Form / w | Gruppe | streng |
|---|---|---|--:|--:|
| eigener Adapter | `percls` | solo / 1,00 | **0,033** | 0,033 |
| Gruppen-Adapter (gepoolt) | `grpfull_alone` | solo / 1,00 | **0,033** | 0,033 |

## Warum die Zahl so ist

Die Klasse bleibt unter 0,15. Der Detektor sieht sie (Boden nicht gemessen), das Modell erzeugt sie aber selten. Best-of-N mit 68 Kandidaten ist der einzige wirksame Hebel.

*Hinweis:* Diese Gruppe enthält nur eine gemessene Klasse. Ihre Gruppen-Trefferquote ist deshalb **per Konstruktion** gleich der strengen; eine Null dort ist kein Beleg über die Gruppierung.

## Wenn es nicht geht

Diese Gruppe hat kein zweites gemessenes Mitglied, auf das man ausweichen könnte. Wenn das Etikett nicht trifft, bleibt Best-of-N oder der Verzicht auf die Anforderung.

## Woher die Zahlen kommen

* **Messgerät:** `laion/vocal-burst-detector-v2` (83 Klassen, das Instrument der Laufzeit). Die beiden Detektoren sind **nicht** austauschbar; keine Zeile mischt sie.
* **Gruppen-Schema:** `vm_groups.py` md5 `f83e3850` (23 Gruppen, 117 Mitgliedsnamen).
* **Trägersatz:** `$SC/out/burst_dose2/prompt_sets.json`, 10 Prompts je (Skriptart, Klasse), Startwert hängt allein vom Prompt-Index ab — alle Arme ziehen dasselbe Rauschen.
* **Statistik:** die drei Stichproben eines Prompts werden zuerst gemittelt, n ist die Zahl der Prompts.
* **WER-Obergrenze:** w = 2,0 ist ausgeschlossen. Über die 28 Klassen der zehn zweiquelligen Gruppen reißen dort **alle vier** Adapter-Arme das Tor (nachtrainiert +0,167, geliehen +0,168, Gruppe-voll +0,123, Gruppe-25 % +0,109 gegen die Schranke +0,104). Bis w = 1,5 hält jeder Arm.
* Studie `vb_grp`, Zustand `~/reports/STATE_burst_group_lora.md`.
