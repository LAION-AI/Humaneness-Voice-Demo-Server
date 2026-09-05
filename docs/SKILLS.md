# The measured knowledge layer, and what it changed

`wikiskills/` is a generated corpus of everything six weeks of experiments
established: sixty attribute pages, a machine-readable `coefficients.json` that
the lever planner already reads, and `VOCAL_BURSTS.md`, which is the part that
changes what the **director** writes.

`skills.py` parses those burst tables at boot and uses them in three places. The
tables are parsed rather than transcribed, for the same reason the wiki is
generated rather than typed: a copy stops agreeing with its source the moment
either moves.

## It corrects two things this server was getting wrong

**We were telling the director to do the one thing measured to hurt.** The
shipped instruction said to put bursts *mid-sentence*. Measured, mid-clause
placement is worse on **15 of 15** classes tested — hit rate −0.07 to −0.12, miss
rate +0.31 to +0.37, t 8–10. The single inversion is `clears_throat`, which is
genuinely better mid-sentence, and the new block says so.

**We were offering sounds that do not exist.** Of the 71 burst adapters on disk,
**36 are measured as never realising at any dose, or below the 0.15 shipping
bar** — every mouth class and every whistle class in the bank is among them. The
old prompt offered all 71. Asking for one produces a silent gap and no warning.
The new block offers 36 and names the rest as unavailable.

And one thing it did not know: **the useful merge weight is per class**, running
0.25 to 2.3 against the flat 0.25 / 0.5 shipped here. `chuckle` alone goes from
0.25 to its measured 2.0.

## What the director is now told

Beyond the list, five rules, each with the measurement behind it:

| rule | measured |
|---|---|
| put the burst between sentences, not inside one | −0.07…−0.12 hit, 15/15 classes worse |
| name the sound's **cause** in the GENERAL line | +0.026 hit |
| give a burst that matters a longer stated duration | +0.022, and +0.044 with the cause sentence |
| write the sound, never the action that makes it | "(he chuckles)" degrades to silence, −0.08…−0.11 |
| do not substitute a neighbouring class | null on family, a significant *harm* on strict (−0.021, t −2.9) |

The list itself is ordered by measured hit rate and split at 0.40, so the
director reaches for the reliable sounds first.

## The switch

Checkbox **Neue Skills** in the chat page, on by default; `MOSS_SKILLS=0` for the
server default. Off restores the previous hand-written block *and* the flat
0.25 / 0.5 dose, so the two are comparable rather than half-mixed. Agents are
built for both settings at boot — the flag changes only the system prompt, so it
costs a string each — and the choice is per request, without a restart.

## Measured so far

Ten prompts each way, one seed. Small, and reported as such:

| | skills on | skills off |
|---|--:|--:|
| bursts written | 9 | 9 |
| of those, from the reliable tier (hit ≥ 0.40) | **5** | 2 |
| impossible classes asked for | 0 | 0 |

The director writes about as many bursts either way but shifts toward the ones
that actually come out. Neither run asked for an impossible class, so the
36-class exclusion is unproven in behaviour here — it is a guard whose value
shows up in the tail, and ten prompts is not the tail.

**What is not measured yet:** whether the audio is better. Everything above is
what the director *writes* and which adapter is loaded at which weight. Whether
more bursts land, and whether the higher per-class doses cost intelligibility,
needs the detector and the transcription harness, and needs the listening the
recipes themselves were chosen with:
[laion/moss-vocal-burst-recipes](https://huggingface.co/spaces/laion/moss-vocal-burst-recipes).

## One correction from the same study

The burst+stop preference adapter is a **null on burst realisation**:
+0.007 / +0.017 / +0.006 at its three recommended checkpoints, none significant,
and the two adapters are redundant rather than additive — all of the gain is the
burst adapter. It is not harmful and step 896 buys genuineness (+0.044) on top,
so ship it for that if at all, never for bursts. It remains off by default with
its own checkbox, which the earlier preliminary signal in `ALIGNMENT.md` was
already too weak to justify changing.
