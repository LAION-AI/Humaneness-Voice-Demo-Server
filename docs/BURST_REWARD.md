# The burst term in the best-of-N reward

Added 2026-09-07. Study `vb_opt`, protocol §71. This page says what changed, what
is measured, and **what is deliberately left to the server that has the models**.

## The problem

`bestofn.rank` scored four things — genuineness, burst blend, CLAP agreement and
a word-error gate — and **none of them asks whether the sound the script names is
actually in the audio.**

Measured over 1,940 candidate sets and 15,517 candidates under the full
production stack, of the four terms only `clap` tracks burst presence at all
(within-set r **+0.148**); `blend` points the **wrong way** (−0.084) and
`genuineness` does nothing (−0.009, CI straddles zero).

Pooled, the old reward still picks better than chance: the delivered take hits
0.1531 against 0.1183 for a random pick, a lift of **+0.0348 (t 5.47)**.

**But restricted to the configuration the server is always in it does not.** On
the six carrier voices that have an `sft3_voice` adapter — and one is always
loaded, because the server falls back to the speaker adapter otherwise — the
lift is **+0.0104 (t 1.51)**, not distinguishable from zero. On the four
carriers without one it is +0.0714 (t 5.97). The pooled number is carried
entirely by material that is off the shipped configuration.

## What changed in this repository

| file | change |
|---|---|
| `config.py` | `BON_BURST_WEIGHT` (2.0), `BON_BURST_DETECTOR`, `BON_BURST_ENCODER`, `BON_BURST_MODE`, `BON_BURST_WIN_S`, `BON_BURST_HOP_S` |
| `config.py` | `BURST_LAM_MAX_SOLO` (1.5) — the ceiling for a reply with exactly one burst adapter |
| `bestofn.py` | fifth summand in `rank()`, `n_burst` emitted per candidate |
| `app.py` | applies the solo ceiling when exactly one burst is tagged, best-of-N is on and the burst term is non-zero |
| `llm_agent.py` | director guidance: when in doubt write one burst, not two |
| `wikiskills/VOCAL_BURSTS.md` | the solo ceiling, and the `bestmem` entry rewritten with both stacks |

**`MOSS_BON` is unchanged and still `0`.** Best-of-N stays off in the chat path.
That is deliberate: everything below is measured **unguided**, the chat path
would run at guidance 3.0, and the thin guided sub-arm suggests guidance already
recovers much of the same gain (+0.0125, t 0.30, against +0.1125, t 2.39
unguided, on 80 sets). **Turn best-of-N on first and measure; judge the term
after.** Not both at once.

## What is NOT done here, and is the next commit

`rank()` reads `c["burst"]`. **Nothing populates it yet**, and `rank` forces the
term to exactly 0 when no candidate carries the key, so the ranking of every
turn is byte-identical to before this commit — verified on a fixture.

That guard is not cosmetic and is worth knowing about before anyone simplifies
it away: `_norm` of a constant vector returns **0.5, not 0**, and a constant 0.5
inside the sum is *not* harmless, because the sum is multiplied by a
per-candidate WER gate afterwards. Without the guard the inert term silently
re-weighted every candidate by its own word error rate, and on a three-candidate
fixture it changed the winner.

Leaving it inert is intentional: this side has
no GPU and none of the assets under `/mnt/nvme/moss-15-v2-assets`, so shipping an
untested model load would have been worse than shipping an inert term.

**To finish it**, `Judge.score` needs one more per-candidate field:

```
burst = mean over the bursts the turn requested of
        s_strict + 0.5 * (s_fam - s_strict) + 0.25 * s_pres + 0.5 * agree
```

* `s_strict` — the detector's probability for the requested class.
* `s_fam` — the same summed over that class's burst family. The failure is
  granularity, not deafness: family-relaxed scoring adds 16–21 points in every
  cross-source cell.
* `s_pres` — probability that any burst is present.
* `agree` — 1.0 when the detector's top-1 is in the requested family.
* `0.0` for a turn that requests no burst, so the term drops out.

Windows of `BON_BURST_WIN_S` at `BON_BURST_HOP_S`, restricted to
`[t − 1.0, t + 2.0]` around each bracket's expected onset — `timed_script.render`
already returns those onsets. Localised beats whole-clip, 0.2082 to 0.1907.

Encoder: `BON_BURST_ENCODER = "commercial"` is the drop-in, because that tower is
already loaded for retrieval and the marginal cost is one 768→256→18 MLP on an
embedding computed per candidate anyway. `large-v2` scores better (+0.0454
against +0.0314, both crossed) at the price of a second encoder on the same card.

## What it buys, and what it costs

Every figure crossed — ranked with one detector, scored by the other:

| | value | t | n |
|---|--:|--:|--:|
| strict hit rate of the delivered take, before | 0.1242 | — | 1940 |
| **Δ hit at weight 2.0** | **+0.0454** | **7.60** | 1940 |
| — relative | **+37 %** | | |
| Δ Parakeet WER (gate is +0.104) | +0.0040 | 2.49 | 1940 |
| Δ CLAP agreement | −0.0055 | −6.82 | 1940 |
| Δ genuineness | −0.067 | −7.24 | 1940 |

**This is a trade, not a free win, and the traded quantity is CLAP** — 3.6 % of
the 0.1507 within-set range a re-ranker can actually move, bought for a 37 %
relative increase in delivered bursts.

Why 2.0 and not 3.0: the exchange rate has a knee. In hit gained per unit of CLAP
lost, 1→2 buys **3.82**, 2→3 buys 2.09, 3→5 buys 1.16.

Rejected after measuring: **tiered ranking** (WER +0.046, t 3.55, against soft's
+0.004, for 0.002 of extra hit) and the **`agree` sweep** (moves the outcome by
0.002 — harmless, useless).

## No recipe changes

No weight in `VOCAL_BURSTS.md` moves. The change is to the ranker, not to any
recipe. What changes is which of the N candidates is delivered.
