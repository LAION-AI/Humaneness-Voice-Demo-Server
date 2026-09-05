# SIDON restoration: it fixes the sound, not the performance

[`sarulab-speech/sidon-v0.1`](https://huggingface.co/sarulab-speech/sidon-v0.1)
is a speech restoration model — MIT licensed, `w2v-bert-2.0` as a feature
extractor into a DAC decoder, both shipped as TorchScript. It takes 16 kHz in
and returns 48 kHz, which matches this server's rate exactly.

It was tested because the arena run kept saying the same thing about our output:
of 1,140 clips, **`pleasant` returned a 5 exactly five times**. The ceiling was
the sound, so it was worth asking whether cleaning the sound raised the ceiling.

## How it was measured

Twenty-one clips drawn across the whole score range (totals 0 through 15), each
judged twice by `gemini-3.8-flash` with the identical rubric prompt: once as
generated, once after restoration. **Both sides were judged fresh.** Reusing the
stored score would have charged all of the judge's own run-to-run noise to the
enhancement, which is how a null becomes a result.

## What it does

| rubric | original | SIDON | delta | t | p |
|---|--:|--:|--:|--:|--:|
| pleasant | 2.71 | 3.14 | **+0.43** | 3.87 | **0.000** |
| fit | 2.19 | 2.38 | +0.19 | 0.85 | 0.397 |
| natural | 2.10 | 2.14 | +0.05 | 0.24 | 0.813 |
| total | 7.00 | 7.67 | +0.67 | 1.48 | 0.138 |

Better on 10 of 21, worse on 4.

**One dimension moves, and it is the one the model is for.** `pleasant` gains
0.43 of 5 at p < 0.001. `natural` does not move at all, and the justifications
say why in almost the same words as before:

> *original:* "It sounds like a speed-read text-to-speech model that completely
> breaks down into synthetic babble."
> *restored:* "The pacing is unnaturally rapid and metronomic before completely
> devolving into synthetic gibberish at the end."

Restoration cleans the signal. It does not change the timing, the phrasing or
the over-generation, so every complaint about the *performance* survives it
intact — including the trailing babble, which comes back sounding tidier.

## When to use it

**Offline, on a take worth keeping.** 7.3 s per clip on CPU, so it is far too
slow to stream, but it is a reasonable last step before exporting a chosen
take — the audible gain is real and it costs nothing but time.

**Not as a fix for anything the director controls.** If a take is rushed,
metronomic or runs past its script, restoration will hand back the same take
with a better noise floor.

Reproduce with `eval/sidon_test.py <n>`; the per-clip pairs land in
`runs/sidon_test.json`.
