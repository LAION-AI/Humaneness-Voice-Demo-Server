# Searching for a better director prompt, and not finding one

An evolutionary search over additions to the system prompt, scored by a
listening model. Run 5 September 2026 against `voice_acting_arena_v0.2.json`
(374 tasks). **The headline is a null result, and the reason it is null is worth
more than the ranking it replaced.**

---

## The design

Twenty tasks, drawn stratified — every one a different emotion label, spread
across `emotion`, `voicenet` and `acting_challenge` and across intensities. The
pick is deterministic (seed 20260905) and saved with the run.

For each task and each of two directors — local `gemma-4-12B-it-qat` and hosted
`gpt-5.6-luna` — three generations of five prompt additions, three takes per
addition in one batched forward pass: **45 clips per task per director**.

A *prompt addition* is a block appended to the standing system prompt.
Generation 1 is five fixed hypotheses. Later generations keep the two best
verbatim and breed three new ones from the scores and the listener's own
justifications, written by `gemini-3.8-flash`.

Every clip was rated by `gemini-3.8-flash`, 0–5 on three rubrics with one
sentence of justification each: **pleasant** (how pleasant to listen to),
**fit** (how well it matches task, emotion, intensity, direction) and
**natural** (how much it sounds like a real spontaneous moment, with the
imperfections and micro-expressions that come with one).

Fitness was the **best of three takes**. That choice is the flaw the run
uncovered; see below.

## The judge discriminates

Rating our own output is worthless if the scale is pinned, so the judge was
calibrated first on audio it had not produced. A real candid recording came back
`natural 5` — *"the hesitation, breathing, spontaneous laughter and interactive
timing sound entirely candid and unforced"*. A read-aloud narration from the same
corpus came back `natural 1`. The scale works, and the `natural 1` our clips
often earn is an honest verdict with four points of headroom above it.

Across 1,140 clips the judge used the range: `fit` returned 83 fives and 51
zeros, `natural` 30 fives and 49 zeros. **`pleasant` returned five 5s in 1,140
clips.** The ceiling in this system is the sound, not the direction.

## What the naive ranking said, and why it was wrong

Pooled over everything, bred blocks looked spectacular:

| block | n | pleasant | fit | natural | total | t vs control |
|---|--:|--:|--:|--:|--:|--:|
| shifting-focus | 6 | 3.67 | 4.17 | 3.83 | **11.67** | +3.09 (p 0.002) |
| shared-room | 6 | 4.00 | 3.83 | 3.33 | 11.17 | +5.11 (p 0.000) |
| mental-friction | 6 | 4.00 | 3.33 | 3.50 | 10.83 | +3.58 (p 0.000) |
| control | 144 | 2.82 | 2.37 | 2.12 | 7.31 | — |

Every one of those p-values is an artefact. **Each task-arm breeds its own
children**, so a block with n = 6 was tried on exactly one task with one
director, while `control` is pooled over all of them. The comparison measures
task difficulty, not prompt quality.

## The comparisons that survive the design

**Generation 1 is balanced** — all five seeded blocks ran on the same cells —
so it is the clean test of the five hypotheses, paired within (task, director):

| block | cells | mean total | vs control | t | p |
|---|--:|--:|--:|--:|--:|
| control | 26 | 6.90 | — | | |
| imperfection | 26 | 7.38 | **+0.49** | 1.04 | 0.300 |
| subtext | 26 | 7.36 | **+0.46** | 1.03 | 0.305 |
| body | 26 | 6.78 | −0.12 | −0.21 | 0.830 |
| breath | 26 | 6.63 | −0.27 | −0.52 | 0.606 |

**None of the five beats the untouched prompt.** Two point the right way and
neither reaches significance at n = 26 arms.

**Breeding did not help.** Best variant per arm, by generation:

| generation | arms | best cell mean | best single take |
|---|--:|--:|--:|
| gen 1 | 25 | 8.88 | 11.40 |
| gen 2 | 25 | 9.28 | 11.40 |
| gen 3 | 25 | 8.93 | 10.96 |

gen2 − gen1 = +0.40 (t 1.12, p 0.27); gen3 − gen1 = +0.05 (t 0.16, p 0.87).

**And the children were coin flips.** Each of the 176 bred blocks against the
control *of its own cell*: mean gain **−0.01** (t −0.07, p 0.94), and **84 of
176 beat their control**.

## Why: the fitness function was selecting luck

| source of spread | SD (scale 0–15) |
|---|--:|
| between the three takes of **one cell** | **1.57** |
| between the variants of one arm | 1.75 |
| between tasks | 1.69 |

Take-to-take noise is as large as everything the search was trying to measure.
With fitness defined as *best of three*, drawing three clips at random from the
pool and keeping the maximum scores **+2.78 points** over a single take — before
any prompt has done anything. The search was climbing that gradient.

The direct check: the same block, run twice in different generations, correlates
at **r = +0.55** and differs by **2.16 points** on average. A single cell cannot
resolve a difference smaller than about two points, and no real prompt effect
here is that large.

## What is solid

* **Track differences are large and real.** `emotion` 7.78, `acting_challenge`
  7.57, `voicenet` **4.87** over 1,140 clips. The VoiceNet items — axis targets
  like `ARSH_low`, `S_DRAM_high` — are where the system is weakest, and no
  prompt addition closed that gap. This points at the adapters, not the prompt.
* **Luna edges out the local model**, 6.92 to 6.60 — smaller than expected, and
  the local model only became competitive once it was given the same `prose`
  style and the same guidance.
* **`breath` was the only block with a consistently negative sign on all three
  rubrics.** It asks for more pauses, which is exactly what `docs/PROMPTING.md`
  was changed to encourage the week before. That is a warning, not a refutation:
  it is not significant, and the block asks for *more* pauses than the standing
  prompt already produces.

## Recommendation, today

**Do not add any of these blocks to the shipped prompt.** The standing prompt
was not beaten by anything that survived a paired comparison.

If one must be chosen — for a demo where a single reply matters more than an
average — `imperfection` and `subtext` are the two with a positive sign, at
+0.49 and +0.46 of 15, both p ≈ 0.30. That is a preference, not a measurement.

**Do not push pauses further** until `breath` is retested. It is the only signed
warning in the run.

**The next run should measure the prompt, not the luck.** Same five blocks on
every task, fitness = *mean* of takes rather than maximum, and more takes per
cell. That is what is being run now; this page will be updated with its result.

## Everything is on disk

`/mnt/nvme/arena/runs/full/takes.jsonl`, one line per clip: task and track,
director, generation, variant, **the full text of the prompt addition**, the
script the director wrote, the chosen voice and reference clip, adapters and
weights, guidance, internal reward, word error, extra words, timings, and the
three rubric scores with their justifications. Audio beside it in
`audio/full/`, named so each clip traces back to its cell. `analyse.py` prints
the pooled tables, `paired.py` the ones above.

The exact prompts — the five seeded blocks, the breeding prompt and the judge's
rubric prompt — are in [`ARENA_PROMPTS.md`](ARENA_PROMPTS.md).
