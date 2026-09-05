# Best-of-N

Generate the turn N times, score every candidate, keep one. The case for it is
already written into the material this server loads: the burst recipes quote an
`N` per class — *"at a hit rate of 0.27 it takes 8 candidates for 90 %
confidence"* — and the emotion adapter card says to generate several and rank
them because the base model drifts under strong emotion. Without this, that
column is advice nobody can act on.

All N candidates are **one batched forward pass**. The streaming path is batch 1
by necessity, because audio has to start before the line ends; choosing between
candidates is the opposite situation. Measured: **8 candidates in 14.9 s without
guidance, 29.2 s with it** — about one take's worth of wall clock per two or
three candidates, not per candidate.

## The reward

```
R = ( norm(genuineness) + norm(blend) + 2 · norm(clap) ) · gate(WER)
```

| term | what it is |
|---|---|
| `genuineness` | `laion/voiceclap-commercial-genuineness`, 0–6 |
| `blend` | `laion/voiceclap-commercial-vocalburst-blend`, 0–10 |
| `clap` | cosine between the take's VoiceCLAP **audio** embedding and the **text** embedding of GENERAL plus every round bracket in the script |
| `gate` | inverse word error rate, flattened to 1.0 above 0.85 |

`clap` carries double weight because it is the only term that asks whether this
is *the performance that was requested*. The other two ask whether it is a good
take of anything.

Normalisation is **within the candidate set**, not against an absolute scale.
Only the ranking matters, the three scorers have unrelated ranges, and their
absolute values are not calibrated against human judgement anyway.

The gate is a threshold rather than a preference: a take everyone can understand
should not beat another take everyone can understand for being marginally more
understandable, but a take that garbles the line has to lose however good it
sounds. Seen working in a real run — six candidates at gate 1.0, two at 0.85.

## Guidance

Independent of N. `1.0` is off; the default when the box is ticked is **3.0**,
the family default for emotion and the value the crossfade study separated
emotions best at. The batched loop runs the same two-branch guided decode as the
streaming path, with the neutralised branch built as its own batch so both halves
pad to the same width.

## What this does not do

* **It does not stream.** Nothing plays until every candidate is finished, which
  is the whole point: choosing needs all of them. Time to first audio is the
  full batch time.
* **It has never been listened to.** Every number in the reward is a model
  scoring another model's output. Whether the top-ranked candidate is the one a
  person would pick is unmeasured, and it is the obvious next experiment: the
  ranking is reported per turn precisely so it can be checked against an ear.
* **N is not free of the director.** Every candidate speaks the same script; the
  variation is in the performance, not the words.

## Using it

Checkbox and an N slider (2–12) in the chat page, off by default;
`MOSS_BON=1` and `MOSS_BON_N` for the server default. The full ranking — reward,
gate, word error and all three terms per candidate — arrives as a `best_of`
event and is shown in the chat, so a bad choice can be traced to its numbers
rather than guessed at.
