<!-- vb_grp:2026-09-05 -->

# vb/quiet_sob

> Stand 5. September 2026 · Gruppe `sob` im 23-Gruppen-Schema · **nicht einzeln gemessen** · eigener Adapter vorhanden: ja
>
> Gruppen-Mitglieder: `convulsive_sob`, `quiet_sob`, `sob`, `sobs`, `trembling_whimper`, `weep`, `whimper`

## Rezept

Diese Bezeichnung wurde **nicht einzeln gemessen**. Sie gehört zur Gruppe `sob`; dort sind gemessen: `sobs`.


In dieser Gruppe funktioniert **nichts**: das gemessene Mitglied kommt nicht über 0,000. Für diesen Laut gibt es kein Rezept, das etwas bringt — siehe `vb-sobs.md`.


## Warum die Zahl so ist

Für diese Bezeichnung selbst gibt es **keine Messung**. Was unten steht, gilt für das gemessene Gruppenmitglied, nicht für dieses Etikett. Ob der Detektor diese Schreibweise überhaupt jemals vergibt, ist ebenfalls ungeprüft.

## Wenn es nicht geht

Die Gruppe `sob` hilft hier nicht: auch ihre gemessenen Mitglieder (`sobs`) kommen nicht über 0,000. Für diesen Laut gibt es derzeit **kein funktionierendes Rezept**; den Charakter über die Emotionsanweisung zu steuern ist der ehrliche Rat.

## Woher die Zahlen kommen

* **Messgerät:** `laion/vocal-burst-detector-v2` (83 Klassen, das Instrument der Laufzeit). Die beiden Detektoren sind **nicht** austauschbar; keine Zeile mischt sie.
* **Gruppen-Schema:** `vm_groups.py` md5 `f83e3850` (23 Gruppen, 117 Mitgliedsnamen).
* **Trägersatz:** `$SC/out/burst_dose2/prompt_sets.json`, 10 Prompts je (Skriptart, Klasse), Startwert hängt allein vom Prompt-Index ab — alle Arme ziehen dasselbe Rauschen.
* **Statistik:** die drei Stichproben eines Prompts werden zuerst gemittelt, n ist die Zahl der Prompts.
* **WER-Obergrenze:** w = 2,0 ist ausgeschlossen. Über die 28 Klassen der zehn zweiquelligen Gruppen reißen dort **alle vier** Adapter-Arme das Tor (nachtrainiert +0,167, geliehen +0,168, Gruppe-voll +0,123, Gruppe-25 % +0,109 gegen die Schranke +0,104). Bis w = 1,5 hält jeder Arm.
* Studie `vb_grp`, Zustand `~/reports/STATE_burst_group_lora.md`.
