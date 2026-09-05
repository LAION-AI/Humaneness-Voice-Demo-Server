"""Build docs/PROMPTING.md — the director's contract, with the prompt verbatim."""
import json, sys, os
sys.path.insert(0, "/mnt/nvme/moss-15-v2")
import config, llm_agent, personas, skills, timed_script

OUT = "/mnt/nvme/moss-15-v2-release/docs/PROMPTING.md"
sk = skills.load()
import glob
have = [os.path.basename(os.path.dirname(f)) for f in
        glob.glob(config.LORA_ROOTS["burst"] + "/*/adapter_model.safetensors")]

ex_in = "(clearly amused, letting it out, warm and unguarded; bright, relaxed) I still cannot believe the cat opened that door by herself. (short chuckle) She is far too clever for this house."
tagged, frames, plain = timed_script.render(ex_in)
gl = timed_script.general_line(
    "a woman's voice, in their thirties, speaking with Standard American; "
    "close conversational volume, unforced; genuine, not acted; clean studio recording",
    frames / config.FRAME_RATE, "EN", "Amusement")

P = []
P.append(f"""# Prompting the director

Everything the language model is told, why each rule is there, and what the
server does with the answer. The prompt itself is reproduced verbatim at the
bottom — it is generated from `llm_agent.SYSTEM`, so it cannot drift from what is
actually sent.

Two models are involved and it is worth keeping them apart:

* the **director** — a language model that writes the reply and decides how it is
  performed. It never produces audio.
* the **voice model** — `{config.TTS_REPO}`,
  which turns the director's script into sound and has its own strict prompt
  format.

The director does **not** write the voice model's prompt. It writes a script with
cues; `timed_script.render()` computes every number and assembles the block. That
separation is deliberate: the format's own documentation says that when the
arithmetic disagrees with the length budget the model has to choose which to
honour, and asking a language model to produce decimals that sum to a given
figure is a bad bet.

---

## 1. What the director returns

One JSON object. Every field is required, because left optional the model simply
stopped emitting them.

| field | what it decides |
|---|---|
| `voice` | which reference recording the take is conditioned on — an emotion at an intensity and containment, a voice-quality dimension, a character, or an edge case |
| `voice2` | an optional second reference, concatenated after the first, for a line that moves through two states |
| `style` | up to {config.SFT3_VN_MAX} delivery adapter(s) from the 17 measured axes, each at 0.5–1.5 |
| `perform` | which of the three generation levers runs: adapters alone, plus steering, plus guidance |
| `speed` | a faster or slower take of the same reference |
| `language` | `English` or `German` |
| `delivery` | the standing description of the voice — becomes the `GENERAL:` line |
| `script` | the words, with a delivery cue before each sentence and vocal bursts between them |

## 2. The three kinds of bracket

This is the one rule that everything else rests on, and it comes from the voice
model's training format rather than from this server:

| written | is | because |
|---|---|---|
| `[0.8 seconds pause]` `[3.9 seconds duration]` | timing | square bracket = a number of seconds |
| `(chuckle, 0.3 seconds)` | a **vocal burst** — an actual sound | round bracket **with** a number |
| `(clearly amused, letting it out)` | a **delivery direction** — how to speak | round bracket **without** a number |

A burst named inside a direction produces no sound at all: the whole bracket is
read as an instruction. The director is told this, and the server repairs it when
it happens anyway.

**The director never writes a number inside a bracket.** It writes
`(chuckle)`, optionally `(short chuckle)` or `(long chuckle)`, and the server
supplies {config.TIMED_FRAMES_PER_WORD:g} frames per word for speech and
{timed_script.BURST_DEFAULT}s / {timed_script.BURST_SHORT}s / {timed_script.BURST_LONG}s
for bursts.

## 3. How a delivery direction is built

Four pieces in a fixed order, taken from the voice model's round-3 scheme:

```
intensity adverb + emotion name (+ second emotion) + how it is held + manner
```

| band | adverbs | means |
|---|---|---|
| faint | barely, faintly, only slightly, just a little | present but held down |
| moderate | clearly, plainly, noticeably, unmistakably | plainly audible, controlled |
| intense | strongly, intensely, very, deeply | running hard, difficult to contain |
| extreme | overwhelmingly, extremely, utterly, completely | at the limit |

Three rules that are easy to get wrong:

* **Name the emotion in the direction**, not only in `GENERAL`. A direction that
  describes how the voice moves without saying what it feels arrives as manner
  and not as feeling — the failure mode round 2 of the voice model measured when
  it dropped directions and emotional control fell to the corpus median.
* **Say whether it is let out or held in.** That is a fork in the training data,
  not a shade: *"letting it out, not hiding it, unguarded"* against *"fought down
  rather than shown, only leaking at the edges of phrases"*.
* **Full direction on the first sentence only.** Later sentences get a short
  reminder — `(still clearly amused)`, `(malicious, still kept under)`. A
  thirty-word note in front of a 0.6 second line buries the line.

**Cues are written in English even when the line is German.** The corpus is
written that way: its German rows read
`Das zerreisst einen einfach, weisst du? (relief sigh)`. A German cue is out of
distribution. Observed in practice: burst labels follow this reliably, delivery
directions only partly.

## 4. Vocal bursts

Of the {len(have)} burst adapters on disk, **{len(sk.offerable(have))} are
offered** — the rest are measured never to realise at any weight, or to sit below
the shipping bar. Every mouth sound and every whistle in the bank is in that
excluded group. The offered list is ordered by measured hit rate and split at
0.40 so the director reaches for the reliable sounds first.

Five rules, each with the measurement behind it:

| rule | measured |
|---|---|
| the burst goes **between** sentences, not inside one | worse on 15 of 15 classes; hit −0.07…−0.12, misses +0.31…+0.37 |
| name the sound's **cause** in the `GENERAL` line | +0.026 hit rate |
| a burst that matters gets a longer stated duration | +0.022, and +0.044 with the cause sentence |
| write the sound, never the action | `(he chuckles)` degrades to silence, −0.08…−0.11 |
| never substitute a neighbouring class | null on family, a significant harm on strict (−0.021, t −2.9) |

The merge weight is **per class**, from that class's own recipe, capped at
{config.BURST_LAM_MAX} — see `SKILLS.md` for why the published weights of up to
2.3 do not survive this stack.

## 5. What the server does with the answer

```
director's script
      │  timed_script.render()   — durations, pauses, burst lengths, Tokens
      │  skills.repair_script()  — a burst named inside a direction gets its own bracket
      ▼
GENERAL: <delivery>; <register>; <continuity>; reads as <emotion>; <N>s, <EN|DE>.
SCRIPT:  [pause] (direction) [duration] words (burst, secs) [duration] words
Tokens:  <the sum of every number above, in frames>
Text:    <the SCRIPT block, byte for byte>
```

A worked example. The director writes

```
{ex_in}
```

and the voice model receives

```
- Instruction:
GENERAL: {gl}
SCRIPT:
{tagged}
- Tokens:
{frames}
- Language:
English
- Text:
{tagged}
```

{sum(1 for _ in [1])and ''}The numbers add up to {frames / config.FRAME_RATE:.1f} s × {config.FRAME_RATE:g} = **{frames} frames**, which is
what the `Tokens` field states. `Text` repeats `SCRIPT` exactly, so the two can
never disagree.

## 6. The character brief

Prepended to the prompt. A brief is only a character description — the acting
machinery underneath is identical for all of them, and the director keeps every
choice it normally has. {len(personas.BUILTIN)} ship
({', '.join(p['name'] for p in personas.BUILTIN)}), a free-text one is accepted,
and the default is `{personas.DEFAULT}`. They are reproduced in full in
[`SYSTEM_PROMPTS.md`](SYSTEM_PROMPTS.md).

## 7. Which model, and what it costs

`{config.DEFAULT_BRAIN}` by default, switchable per request to
{', '.join('`'+k+'`' for k in config.HOSTED_MODELS if k != config.DEFAULT_BRAIN)}
or to a local model. Reasoning is set to `{config.HOSTED_REASONING}`: this turn
needs a character decision, not deliberation, and turning it off measured 5.3 s →
1.5 s on flash-lite and 4.4 s → 2.4 s on luna.

The hosted route needs `$HYPRLAB_API_KEY` or a key file at
`$MOSS_LUNA_KEY_FILE`. **No key is stored in this repository.**

---

## 8. The prompt itself

Verbatim from `llm_agent.SYSTEM`. The reference bank, the burst list and the
delivery-axis glossary are appended to it at runtime from what is actually on
disk, so they are not reproduced here — `GET /api/voices` and
`GET /api/adapters` return them.

```
{llm_agent.SYSTEM}
```

### The burst block, as generated today

```
{sk.prompt_block(have) if sk and sk.ok else '(skills not loaded)'}
```
""")
open(OUT, "w", encoding="utf-8").write("\n".join(P))
print("wrote", OUT, len("\n".join(P).splitlines()), "lines")
