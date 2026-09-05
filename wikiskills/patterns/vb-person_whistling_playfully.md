<!-- vb_grp:2026-09-05 -->

# vb/person_whistling_playfully

> Stand 5. September 2026 · Gruppe `whistle` im 23-Gruppen-Schema · **nicht einzeln gemessen** · eigener Adapter vorhanden: nein
>
> Gruppen-Mitglieder: `person_whistling_playfully`, `person_whistling_to_get_attention`, `sharp_whistle`, `soft_whistle`, `whistle`, `whistling`, `wolf_whistle`

## Rezept

Diese Bezeichnung wurde **nicht gemessen**, und in ihrer Gruppe `whistle` ist ebenfalls keine Klasse gemessen. Es gibt dafür **kein belegtes Rezept**.


## Warum die Zahl so ist

Für diese Bezeichnung gibt es **keine Messung** — weder für sie selbst noch für ein Mitglied ihrer Gruppe. Es ist unbekannt, ob das Modell sie erzeugen kann; niemand hat es geprüft.

## Wenn es nicht geht

Diese Gruppe hat kein zweites gemessenes Mitglied, auf das man ausweichen könnte. Wenn das Etikett nicht trifft, bleibt Best-of-N oder der Verzicht auf die Anforderung.

## Woher die Zahlen kommen

* **Messgerät:** `laion/vocal-burst-detector-v2` (83 Klassen, das Instrument der Laufzeit). Die beiden Detektoren sind **nicht** austauschbar; keine Zeile mischt sie.
* **Gruppen-Schema:** `vm_groups.py` md5 `f83e3850` (23 Gruppen, 117 Mitgliedsnamen).
* **Trägersatz:** `$SC/out/burst_dose2/prompt_sets.json`, 10 Prompts je (Skriptart, Klasse), Startwert hängt allein vom Prompt-Index ab — alle Arme ziehen dasselbe Rauschen.
* **Statistik:** die drei Stichproben eines Prompts werden zuerst gemittelt, n ist die Zahl der Prompts.
* **WER-Obergrenze:** w = 2,0 ist ausgeschlossen. Über die 28 Klassen der zehn zweiquelligen Gruppen reißen dort **alle vier** Adapter-Arme das Tor (nachtrainiert +0,167, geliehen +0,168, Gruppe-voll +0,123, Gruppe-25 % +0,109 gegen die Schranke +0,104). Bis w = 1,5 hält jeder Arm.
* Studie `vb_grp`, Zustand `~/reports/STATE_burst_group_lora.md`.
