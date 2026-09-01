# End-trimming: fade in at the first word, cut after the last

## The problem, and why the obvious fix cannot work

Takes sometimes say the line and then keep going — a few more words, often not
real words. The tempting fix is to stop the audio at the duration the prompt
asked for.

That does not work, and the reason is the most useful fact in this document:
**the audio already matches the requested duration to within 0.02 s**, in every
condition ever measured, clean or degraded (`EXPERIMENTS.md` §8). The model does
not overrun. When it improvises it speaks the real line slightly faster and puts
the filler *inside* the same budget. There is no overhang to trim.

So the fix has to be content-based: something must notice that the words which
were asked for have been said.

## Why alignment rather than recognition

We already know which words were supposed to be spoken, so this is an alignment
problem, not a transcription problem. An aligner cannot invent a word that was
never in the script; a transcriber can, and then the trim point would be decided
by a hallucination.

| | |
|---|---|
| emissions | [`romara-labs/mms-300m-1130-forced-aligner-ONNX`](https://huggingface.co/romara-labs/mms-300m-1130-forced-aligner-ONNX) — Wav2Vec2 CTC, 31 tokens, 20 ms per frame at 16 kHz |
| Viterbi pass | `torchaudio.functional.forced_align` |

The Viterbi pass is deliberately not hand-rolled. A trellis is exactly the kind
of code that is subtly wrong for a long time, and torchaudio ships a tested one.

> **Licence.** The aligner is **CC BY-NC 4.0**, unlike everything else this server
> loads — the rest of the stack was chosen for commercial usability on purpose.
> It is fetched at runtime and not redistributed here, so this repository's
> licence is unaffected, but a commercial deployment must switch it off
> (`MOSS_ALIGN=0`, or the checkbox) or substitute another aligner.

## The two edges

**Lead-in.** If the script does not open on a vocal burst, everything before the
first word is throat-clearing nobody asked for. Fade in so full level is reached
exactly at the first word's onset. When the script *does* open on a burst, the
opening is left completely alone — the burst is the performance.

**Tail.** After the last scripted word, keep a little air, ramp down over 150 ms,
and drop the rest.

**A scripted closing burst is protected.** A line ending on `(breathy giggle)`
had 1.03 s removed and read as a clean success on every metric — extra words
1 → 0, word error 0.10 → 0.00 — while actually deleting the giggle the director
wrote. Burst tags carry their own lengths, so the allowance is now exact rather
than guessed. This was found by reading the per-take rows, not the summary.

## Streaming

A stream cannot retract what it has played, so the guard keeps a lookahead: audio
is held `ALIGN_LOOKAHEAD_S` (0.5 s) behind generation, and the aligner runs on
everything generated so far every `ALIGN_EVERY_S` of new audio. Once the last
word is found to have ended, the tail is faded and the remainder dropped.

Two things had to be different from the offline path, and both were bugs first:

* **The lead-in needs a longer first look.** Measured offline, first-word onsets
  run to 1.3 s. Deciding at 0.5 s asked the aligner to fit the whole script into
  half a second, which fails — so the fade silently never fired in the stream
  while firing 28 times in 36 takes offline. The first decision now waits for
  `ALIGN_LEAD_SCAN_S` (1.3 s) and asks about the first three words only.
* **The tail must not be looked for too early.** Forced alignment always places
  every target somewhere, so against a prefix it reports the last word as
  finished while half the line is unspoken — and that cut removes real speech.
  The tail is only considered once `ALIGN_TAIL_AFTER` (60 %) of the requested
  duration exists, which the duration contract makes reliable.

Cost: the aligner runs on CUDA at **50 ms per 10 s of audio**, against 1000 ms on
CPU. That difference decides whether streaming is possible at all, and it depends
on load order — `onnxruntime` finds cuDNN and cuBLAS because torch has already
pulled them into the process, so the aligner is constructed *after* the TTS model.
Loaded first it falls back to CPU without failing.

Time to first audio grows by the lead-in scan, about 0.7 s, once per reply.

## Measured

36 takes: twelve scripts × three seeds, on the shipped stack. Each line was
generated once with trimming off and the trim then applied to that same audio, so
both halves are the identical take and the only difference is the edit.

| | |
|---|--:|
| takes edited | 32 / 36 (89 %) |
| lead-in fired | 28 / 36 |
| tail cut fired | 26 / 36 |
| removed, mean | 0.366 s |
| removed, max | 1.790 s |
| **invented words** | **0.22 → 0.03** |
| word error | 0.033 → 0.020 |

The invented-word column is the point: `extra_w` counts words transcribed after
the last one still matching the script, and it falls by 86 %. Word error falling
too says the trim is not eating real speech — if it were, that number would rise.

Both `opens_burst` scripts were left alone at the lead-in on every seed, which is
the rule working rather than a coincidence.

### A preliminary signal worth following up

An interrupted run with the burst+stop preference adapter loaded showed **0.09
invented words before any trimming**, against 0.22 without it — the adapter
appears to reduce the improvisation itself. That was 11 takes against 36 and the
run did not finish, so it is a signal and not a result. It agrees with what that
adapter was trained for, which is a reason to test it properly rather than a
reason to believe it.

## Switching it off

Checkbox in the chat page, on by default. `MOSS_ALIGN=0` for the server default.
With the aligner absent the guard is never constructed and the streaming path is
exactly what it was.

Every edit is reported per turn — which edges fired, where, how much went away,
and how many alignment passes it took — in the `align` block of the final event
and as one `[align]` line in the log.
