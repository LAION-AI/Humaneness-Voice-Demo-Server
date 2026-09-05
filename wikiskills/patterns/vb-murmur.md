<!-- vb_grp:2026-09-05 -->

# vb/murmur

> Stand 5. September 2026 · Gruppe `hum` im 23-Gruppen-Schema · **nicht einzeln gemessen** · eigener Adapter vorhanden: nein
>
> Gruppen-Mitglieder: `humming`, `low_mumble`, `murmur`, `purr`, `resonant_hum`, `soft_hum`, `whispered_mumble`

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
