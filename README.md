# Humaneness Voice Demo Server

A chat window that answers out loud, in character, with acted delivery.

You type a line. A language model writes the reply **and directs it** — a
standing description of the voice, plus a bracketed instruction on every
sentence saying how to perform it. That direction is then used twice: it is
embedded and matched against a corpus of real acted recordings to pick a
reference clip and an emotion adapter, and it is written into the prompt that
drives the speech model. Audio streams back frame by frame and starts playing
before the sentence is finished.

Two pages ship in the server:

| page | what it is |
|---|---|
| `/` | **the voice-acting demo** — the main one. Chat, autoplaying audio, latency panel, every adapter and reference clip shown per turn |
| `/studio` | the same engine with speech-recognition input, emotion and voice-quality scoring of *your* voice, and persona switching |
| `/report` | a static summary of the measurements |

---

## The models this runs on

Everything below is downloaded from the Hugging Face Hub. Nothing is trained here.

### Speech

| role | repository |
|---|---|
| **Speech model** (4.13 B, the one that speaks) | [`laion/moss-tts-local-transformer-4.55b-voice-acting-v2-sft3`](https://huggingface.co/laion/moss-tts-local-transformer-4.55b-voice-acting-v2-sft3) |
| Audio tokenizer / vocoder | [`OpenMOSS-Team/MOSS-Audio-Tokenizer-v2`](https://huggingface.co/OpenMOSS-Team/MOSS-Audio-Tokenizer-v2) |
| Quality adapter, rank 64 | [`laion/moss-va-sft3-dpo-lora-p2`](https://huggingface.co/laion/moss-va-sft3-dpo-lora-p2) — supersedes [`…-dpo-lora`](https://huggingface.co/laion/moss-va-sft3-dpo-lora) |
| Voice-identity adapters, 500 × rank 16 | [`laion/moss-va-sft3-voice-loras`](https://huggingface.co/laion/moss-va-sft3-voice-loras) |
| Emotion adapters, 40 × rank 16 | [`laion/moss-va-sft3-emotion-loras`](https://huggingface.co/laion/moss-va-sft3-emotion-loras) |
| Perceptual-quality adapters, 3 × rank 16 | local SFT3-native set (genuineness, vocal-burst blend, aesthetics) |
| Delivery-axis adapters, 17 × rank 16 | local SFT3-native set — replaces the 57-dimension VoiceNet adapters below |
| Vocal-burst adapters, 71 × rank 16 | local SFT3-native set — replaces the v2-era [`laion/vocal-burst-lora-adapters`](https://huggingface.co/laion/vocal-burst-lora-adapters) |
| Voice-quality adapters (57 dimensions) — **parked**, trained against v2 | [`laion/moss-voicenet-dimension-loras`](https://huggingface.co/laion/moss-voicenet-dimension-loras) |
| Character adapters | [`TTS-AGI/moss-character-loras-refined-public`](https://huggingface.co/TTS-AGI/moss-character-loras-refined-public) |
| Base checkpoint the older adapters were trained on | [`laion/moss-tts-local-transformer-4.55b-voice-acting-v2`](https://huggingface.co/laion/moss-tts-local-transformer-4.55b-voice-acting-v2) |

### Reference corpus

| role | repository |
|---|---|
| **The acted reference recordings** — 10 voices × 842 conditions × 48 takes, with every take scored | [`TTS-AGI/moss-voice-profile-references`](https://huggingface.co/datasets/TTS-AGI/moss-voice-profile-references) |
| Profile adapters for those voices (alternative set) | [`laion/moss-voice-profile-loras-500`](https://huggingface.co/laion/moss-voice-profile-loras-500) |

### Retrieval and measurement

| role | repository |
|---|---|
| **Voice–text embedding model** used to match direction prose to recordings | [`laion/voiceclap-commercial`](https://huggingface.co/laion/voiceclap-commercial) |
| Naturalness head | [`laion/voiceclap-commercial-genuineness`](https://huggingface.co/laion/voiceclap-commercial-genuineness) |
| Vocal-burst blend head | [`laion/voiceclap-commercial-vocalburst-blend`](https://huggingface.co/laion/voiceclap-commercial-vocalburst-blend) |
| Emotion scoring of the user's voice (`/studio`) | [`laion/Empathic-Insight-Voice-Small`](https://huggingface.co/laion/Empathic-Insight-Voice-Small) |
| Voice-quality predictors (57 dimensions) | [`laion/voicenet-dimension-predictors-commercial`](https://huggingface.co/laion/voicenet-dimension-predictors-commercial) |
| Speech recognition | [`nvidia/parakeet-tdt-0.6b-v3`](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) |
| Speaker-similarity check | [`speechbrain/spkrec-ecapa-voxceleb`](https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb) |

### The language model that writes and directs

Hosted by default (`gpt-5.6-luna`), switchable in the UI to `gemini-3-flash` or
`gemini-3.5-flash-lite`. A fully local option runs
[`unsloth/gemma-4-12B-it-qat-GGUF`](https://huggingface.co/unsloth/gemma-4-12B-it-qat-GGUF)
through `llama.cpp`, which is what `./run.sh llm` starts.

> The hosted route needs an API key. It is read from `$HYPRLAB_API_KEY` or a file
> path given by `$MOSS_LUNA_KEY_FILE`. **No key is stored in this repository**,
> and none is needed if you use the local model.

---

## How one turn works

```
browser ──POST /api/turn──> FastAPI
                              │
                              │ 1. director LLM writes: reply + GENERAL + SCRIPT with cues
                              │
                              │ 2. retrieval: cue text ──VoiceCLAP text tower──> nearest
                              │    emotion + nearest reference clip of the chosen voice
                              │
                              │ 3. adapters merged into the speech model
                              │
                              │ 4. timing worked out, prompt assembled
                              ▼
                     MOSS SFT3 (4.13 B, 12 codebooks @ 12.5 Hz)
                     frame-by-frame ──PCM chunks──> Web Audio, autoplay at 48 kHz
```

**1 — The director.** The language model gets the character brief, the
conversation so far, and a system prompt that is mostly about *how to write a
performance*: one bracketed cue per sentence, vocal bursts from the 22 labels
the speech model was actually trained on, an intensity adverb on every cue
(`barely` / `clearly` / `intensely` / `utterly`), never a capital letter inside
the spoken text, never a number inside a bracket. The full prompts are in
[`docs/SYSTEM_PROMPTS.md`](docs/SYSTEM_PROMPTS.md), generated from the code so
they cannot drift.

**2 — Retrieval.** Described in its own section below.

**3 — Adapters.** Described in its own section below.

**4 — Timing and the prompt.** `timed_script.py` converts the director's script
into the timed format the speech model was fine-tuned on, and computes every
number so that they add up exactly to the length budget.

---

## The prompt that reaches the speech model

SFT3 takes one `<user_inst>` block with a fixed set of fields. The demo shows
this block verbatim in the UI — what you read in the page is exactly what the
model was handed. A real turn:

```
<user_inst>
- Reference(s):
<|audio|>
<|audio|>
- Instruction:
GENERAL: a woman's voice, in their thirties, speaking with Standard American, a clear,
measured voice …; close conversational volume, unforced; same speaker throughout;
genuine, not acted; clean studio recording; reads as amusement; 13.9s, DE.
SCRIPT:
[0.3 seconds pause] (klar amüsiert, leicht verschwörerisch) [6.5 seconds duration] Also,
ich finde es herrlich, dass mein staubsauger immer genau dann dramatisch den dienst
quittiert, wenn besuch kommt. (chuckle, 0.3 seconds) [6.5 seconds duration] Dann stehe ich
da, nicke würdevoll und tue so, als hätte ich gerade eine sehr moderne wohnästhetik
erfunden. [0.3 seconds pause]
- Tokens:
174
- Quality:
None
- Sound Event:
None
- Ambient Sound:
None
- Language:
German
- Text:
[… byte-identical copy of the SCRIPT block …]
</user_inst>
```

The rules, and how this server satisfies them:

| rule | how it is met |
|---|---|
| square bracket = a number of seconds | `[N.N seconds duration]` before each sentence, `[N.N seconds pause]` for every gap ≥ 0.2 s, including before the first word and after the last |
| round bracket **with** a number = a vocal burst | bursts are emitted as `(chuckle, 0.3 seconds)`; length defaults to the training median 0.28 s and is clamped to 0.14–1.2 s |
| round bracket **without** a number = a delivery direction | the director is explicitly forbidden from writing numbers inside brackets, so a direction can never be misread as a burst |
| the numbers must add up to `Tokens` | computed, not generated. 0.3 + 6.5 + 0.3 + 6.5 + 0.3 = 13.9 s × 12.5 frames/s = **174** |
| segments over 12 s are split | enforced in `timed_script.render` |
| `Text` byte-identical to `SCRIPT` | the same rendered string is passed to both fields |
| `GENERAL` ends with the emotions, length and language | `…; reads as <emotion>; <seconds>s, <EN\|DE>.` |

**Why the numbers are computed rather than written by the language model.** The
model card is explicit that when the arithmetic disagrees with the budget, the
speech model has to choose which to honour — and length control is what it
honours best. Asking a language model to produce a set of decimals that sums to
a given figure is a bad bet, so the director writes the *performance* (where the
silences fall, which bursts, how each line is delivered) and `timed_script.py`
does the arithmetic. Speech length is derived at 4.5 frames per word, which is
the rate of the format's own worked example.

---

## Which adapters get merged, and when

> The full protocol — the merge arithmetic, the tied-weight exception, every set,
> every slider, and how to reproduce the whole stack — is in
> [`docs/ADAPTERS.md`](docs/ADAPTERS.md). This section is the summary.

Adapters are **merged as weighted deltas** into the model weights for the
duration of one turn, then unmerged. This matters: PEFT's `add_weighted_adapter`
refuses this combination, because the quality adapter is rank 64 while the voice
and emotion adapters are rank 16. Merging deltas has no such constraint. Each
adapter's own `alpha/r` is applied first (2.0 for every set here), and the weight
below is on top of that.

### Default stack — one turn, nothing ticked or unticked

| order | adapter | weight | why |
|---|---|---|---|
| 1 | `sft3_dpo:p2` | **1.0** | general quality, the published weight |
| 2 | `sft3_voice:<profile>` | **1.0** | speaker identity. 1.0 is the trained value and has not been swept |
| 3 | `burst:<label>` | 0.25 | only when the script contains a burst that has an adapter. 0.5 when the burst stands alone (a line under 14 words) |
| 4 | `sft3_quality:genuineness_high` | **1.0** | perceptual quality, on by default at the trained value |
| 5 | `sft3_quality:blend_high` | **1.0** | vocal-burst blend, likewise |
| 6 | `sft3_quality:esthetics_high` | **1.0** | aesthetics, likewise |
| 7–8 | `sft3_voicenet:<axis>` | 0.25 / 0.5 / 0.75 | up to two delivery axes, only when the director asks for them |
| 9 | `sft3_emotion:<Emotion>` | **1.5** | the emotion retrieval picked |

Rows 1, 2, 4, 5 and 6 are on every turn; the rest are conditional. Ordering has
no effect on the arithmetic — the deltas are summed into one weight per module.

The three base-style VoiceNet adapters that used to sit in this list are gone: the
57-dimension set they came from was trained against the untuned v2 checkpoint and
is parked. The conversational register is carried by the prompt instead.

The quality adapter is `p2`, the best checkpoint measured in this line: reward
0.4757 against 0.4708 for its predecessor, the highest emotion percentile of any
preference-tuned model here (0.3541), and — uniquely — a word error rate (0.0977)
slightly better than the supervised baseline it is built on (0.0987).

### Tied weights: why twelve modules are not merged

`MossTTSLocalModel.tie_weights()` makes `audio_lm_heads.N.weight` and
`audio_embeddings.N.weight` **the same tensor**. Folding a head delta into the
weight therefore rewrites the audio embedding too and corrupts the model — the
adapter card measures both tensors moving by exactly 6.103515625e-05 while the
text embedding does not move at all. Both DPO adapters carry LoRA on all twelve
heads, so this is not hypothetical.

`lora_bank.py` detects those modules (`LoraBank.TIED`) and runs them as **forward
hooks** instead: the same arithmetic, `h + scaling·B(A(x))`, without writing to
any stored weight. Everything else stays merged. Hooks were rejected for the
model as a whole because 536 of them cost more in kernel launches than the
arithmetic saves at batch 1 — but twelve is not 536, and the measured GPU
realtime factor is unchanged at 0.99.

The emotion weight of 1.5 is the operating point from the adapter card's own
scale sweep: emotion 0.408 → 0.471, genuineness and burst blend both rise with
it, median word error rate still 0.000 and mean at its lowest. It breaks between
1.5 and 2.0, and as a tail of a few derailed clips rather than general decay.

### What the switches do

| switch | default | effect |
|---|---|---|
| **Emotion nuances** | on | off ⇒ no emotion adapter. The turn runs on the base checkpoint, the quality and voice adapters, and the retrieved reference clip |
| **Character LoRA** | on | off ⇒ no voice-identity adapter; identity then comes only from the reference recordings |
| **Pure** | off | on ⇒ drops everything the v2-era planner would have added (v2 emotion, character, burst) and halves the voice adapter to 0.5. The DPO adapter, the quality trio, the delivery axes and the emotion adapter still apply |
| **Quality axes** (three sliders) | **1.0 each, on** | genuineness, vocal-burst blend, aesthetics. These are the only sliders where 0 really means off |
| **Delivery axes** (17 sliders) | 0 | 0 means *leave it to the director*, not "force off". A slider above 0 forces that axis on at that weight |
| **Aesthetics** (`vn_ESTH__high`) | **0.0, off** | trained against the untuned v2 weights. The set it belongs to is parked, so this dial currently resolves to nothing |
| **Speaker LoRA** (velvet-sage) | off when a profile is active | superseded by the per-profile voice adapter |
| **Sentence-end brake** | 3.0 | additive pressure in nats against the stop token, so a line is not cut off early |

The adapter overlay is populated from `GET /api/adapters` and its sliders are
posted back as `quality_lams` and `adapter_overrides`. Full semantics in
[`docs/ADAPTERS.md`](docs/ADAPTERS.md).

### An honest note on provenance

Six of the adapter sets — `sft3_dpo`, `sft3_voice`, `sft3_emotion`,
`sft3_quality`, `sft3_voicenet` and the 71 SFT3 burst adapters — were trained
against the SFT3 weights and are in distribution. The character, profile, speaker
and legacy emotion sets were trained against the untuned v2 checkpoint; the
57-dimension VoiceNet set was too, and has been parked rather than deleted.

In distribution is not the same as evaluated. Only `sft3_dpo`, `sft3_voice` and
`sft3_emotion` have published measurements. The quality trio, the delivery axes
and the burst set are **unevaluated** — 1.0 and 0.25/0.5/0.75 are the values they
were trained at, or a deliberately conservative fraction of them, not weights
shown to be best.

---

## Retrieval: choosing the reference clip and the emotion

The reference corpus holds ten voices, each rendered through the same 842 acting
conditions (40 emotions × 2 intensity bands, 57 voice-quality dimensions at
several levels, characters, vocal bursts, edge cases) in English and German. The
demo keeps the **best three takes of every condition**, ranked by the corpus's
own reward — 25 260 clips.

At turn time the director's prose is matched against this corpus with the
VoiceCLAP text tower, on two axes:

* **the emotion** is read off the **round-bracket cues alone**, matched against
  40 emotion text anchors (each the mean of six caption templates);
* **the clip** is matched against per-condition **centroids of the audio
  embeddings** the corpus ships, using the cues *plus* the emotion-bearing part
  of GENERAL.

Language is a **hard filter**, not a preference.

### What was measured, and what it cost

Held-out set of director-style prose with a known target, 40 emotions
(chance 0.025):

| approach | top-1 |
|---|---|
| text → a single clip's audio embedding | 0.071 |
| text → condition centroid, raw | 0.22 |
| text → condition centroid, mean-centred | 0.44 |
| text → emotion text anchor, 6 templates, mean-centred | **0.61** |
| any variant, for the 57 voice-quality dimensions | ≤ 0.08 |

Four findings shaped the design:

1. **0.071 for a single clip is not a bug.** It is exactly the `emonet top-1 =
   0.0721` on the model's own card. Averaging a condition's takes into a
   centroid is what makes the audio side usable at all.
2. **The embeddings are strongly anisotropic** — raw cosines sit in a narrow band
   around 0.9 and a few conditions are near-neighbours of everything. Centring
   both sides moves 0.35 → 0.61 and 0.22 → 0.44.
3. **The text tower is `all-MiniLM-L6-v2`**, trained on short caption sentences.
   Long structured GENERAL blocks are far outside that distribution and score
   0.12.
4. **Voice-quality dimensions do not survive the text tower** — everything
   collapses onto one dimension. Those still come from explicit codes and the
   base style, not from retrieval.

Because the emotion axis is more than twice as strong as the audio axis, it
leads: conditions matching the winning emotion get a bonus of 0.5, and audio
similarity then picks the intensity band and the take within it. Swept: 0.1 →
0.33, 0.3 → 0.50, **0.5 → 0.61**, flat above.

### Two failure modes that had to be handled

* **The director misreports the language.** A turn written entirely in German
  came back declared as English and pulled an English reference clip — the exact
  setup that put an audible English accent on German output earlier in this
  project. The language is now decided from the words themselves.
* **German cues retrieve the wrong emotion, not merely a weaker one.** „Stimme
  brüchig vor zurückgehaltener Trauer" came back as `Teasing`. When the cues are
  not English, the emotion falls back to the English label the director names
  from a fixed vocabulary.

---

## The ten voices

The profile cards shipped with the corpus **disagree with the audio**: three of
the ten carry the wrong gender. That is not cosmetic — the card text becomes
"a woman's voice" inside the GENERAL block, where it argues with the reference
recording.

`setup/profile_traits.py` derives gender, age and a timbre keyword from the
VoiceNet predictions the corpus already carries for every take, calibrated
against the corpus's own deliberately manipulated conditions (the only labelled
points available: `GEND` runs 1.45 at its most feminine to 4.31 at its most
masculine, so neutral is near 3.0, not 0). Clips that manipulate `GEND` or
`AGEV` are excluded from a voice's own average.

| name | profile id | measured | the card said |
|---|---|---|---|
| Selma | `emolia_c0542` | f, 20s, bright | **m, 40s-50s** ✗ |
| Mira | `emolia_c1699` | f, 30s, full | f, 20s-30s |
| Nora | `k10_age3_bg1` | f, 60s, light | no gender given |
| Robin | `k91_age5_bg0` | 70s+, hushed (androgynous) | f, 70s-80s |
| Cormac | `emolia_c1682` | m, 30s, deep | m, 20s |
| Béla | `k325_age3_bg1` | m, 40s-50s, warm | m, 40s-60s |
| Idris | `anime_088` | m, 40s-50s, even | m, 30s-40s |
| Rasmus | `emolia_c2570` | m, 60s, deep | **f, 60s-70s** ✗ |
| Anton | `k395_age3_bg1` | m, 60s, muffled | **f, 40s-60s** ✗ |
| Osku | `mediathek_0184` | m, 60s, hushed | m, 60s-70s |

Default voice is **Mira** (`emolia_c1699`). The age bands are a translation of a
narrow measured scale into decades — the ordering is solid, the decades are an
interpretation. The assignment was computed, not listened to.

---

## Characters

Five briefs ship, all in [`personas.py`](personas.py) and reproduced in
[`docs/SYSTEM_PROMPTS.md`](docs/SYSTEM_PROMPTS.md): **The Host** (default),
**Count Dracula**, **Orc Warlord**, **Cookie Monster**, **The Counsellor**. A
free-text custom persona is accepted too. A brief is only a character
description — the acting machinery underneath is identical for all of them.

---

## Running it

### Hardware

Two 24 GB GPUs. The speech model takes about 10 GB in bfloat16 on one card; the
language model, speech recognition and scoring models sit on the other. One card
works if you use a hosted language model and accept a smaller adapter cache.

### Install

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

`flash-attn 2` is **not** compatible with this architecture — the model is loaded
with `attn_implementation="sdpa"`.

### Fetch the assets

```bash
export HF_HOME=/path/with/space          # the corpus shards are large
python setup/fetch_profile_refs3.py      # best 3 takes per condition, ~3.5 GB kept
python setup/build_retrieval_index.py    # condition centroids + emotion anchors
python setup/profile_traits.py           # measured gender/age/timbre per voice
```

`fetch_profile_refs3.py` streams one WebDataset shard at a time and deletes it
after extracting the takes it wants, so peak disk stays at about one shard
(~1.4 GB) instead of the 70 GB the full download would need.

The adapters are fetched with `huggingface_hub` into
`$MOSS_LORA_ROOT`-style directories listed in `config.LORA_ROOTS`; the ten voice
adapters and forty emotion adapters together are about 6.5 GB.

### Start

```bash
./run.sh llm     # local language model on GPU $MOSS_LLM_GPU, port 8790  (optional)
./run.sh app     # speech model + web UI on GPU $MOSS_TTS_GPU, port 8792
./run.sh both
```

Then open <http://localhost:8792>.

### Caches that make it fast

Tokenised reference codes are cached on disk (`config.CODE_CACHE`). Without that
cache, every restart re-tokenised the corpus and any clip the retrieval reached
for that the preload had not yet covered cost a full mp3 decode plus a GPU codec
pass, queued behind the preload's own work — one turn spent **60 s** choosing its
reference. With the cache and a preload that covers the voice actually being
spoken, reference selection is **0.02–0.06 s**. The codes are tiny: 1 804 clips
occupy 8.8 MB.

---

## Repository layout

| file | what it does |
|---|---|
| `app.py` | FastAPI server, the turn pipeline, binary streaming protocol |
| `config.py` | every setting, all overridable by environment variable |
| `llm_agent.py` | the director: system prompts, schema, output cleaning, hosted and local backends |
| `retrieval.py` | direction → VoiceCLAP embedding → nearest emotion and reference clip |
| `timed_script.py` | the SFT3 timed-script format and its arithmetic |
| `tts_engine.py` | prompt assembly, frame-by-frame generation, streaming with crossfade |
| `voice_bank.py` | the reference corpus: indexing, tokenising, disk cache, selection |
| `lora_bank.py` | adapter discovery, RAM/GPU caching, delta merge and unmerge |
| `voice_profiles.py` | the ten voices and their measured descriptions |
| `personas.py` | character briefs |
| `voice_codes.py` | the emotion / voice-quality code language and its expansions |
| `score_engine.py` | emotion and voice-quality scoring for `/studio` |
| `asr_engine.py`, `sim_engine.py`, `vc_engine.py`, `sidon_restore.py` | speech recognition, speaker similarity, optional voice conversion and restoration |
| `index.html`, `studio.html`, `report.html` | the three pages |
| `levers.py` | which of the three generation levers this turn gets, and why |
| `steer_engine.py` | the steering vectors and their injection points |
| `setup/` | corpus extraction, retrieval index, profile traits, the steering pack, `check_levers.py` |
| `eval/` | consistency and completeness checks |
| `docs/` | [`ADAPTERS.md`](docs/ADAPTERS.md) (the adapter protocol), [`LEVERS.md`](docs/LEVERS.md) (the generation modes), generated defaults, verbatim system prompts, measurement log |

---

## Three levers, not one

Loading adapters and writing a good prompt used to be the only way to shape a
performance here. Two more levers have since been measured on this checkpoint —
a **steering vector** added to the hidden state while the model speaks, and
**classifier-free guidance** on the delivery condition — together with how all
three combine. They are exposed as switchable generation modes, and the director
picks between them with a `choose_generation_mode` tool call.

The best single lever **flips by family**, which is the whole reason there is a
mode selector rather than a global switch:

| family | adapter | steering | guidance |
|---|--:|--:|--:|
| emotion | +0.077 (t 2.8) | **+0.384** (t 9.4) | +0.050 (t 1.8) |
| delivery | +0.377 (t 7.1) | **+0.614** (t 9.6) | +0.026 (t 0.4) |
| quality | **+0.399** (t 6.0) | +0.006 (t 0.0) | +0.062 (t 0.9) |

So `auto` — the default — gives an **emotion** the adapter and the steering
vector together, because on emotions the two are cleanly additive; gives a
**delivery axis** the adapter alone, because there the two are significantly
*sub*-additive and doing the same job; gives a **quality axis** the adapter
alone, because steering does not move it at all; and never spends guidance,
which costs **1.93×** and therefore does not stream.

Every mode is switchable off, and both new levers need an asset that is not in
this repository — a 5.3 MB vector pack and the measured coefficient table. With
neither present the server behaves exactly as it did before, and says so in
`/api/state` and in every response payload.

> The evidence for each of those defaults, what the modes cost, why guidance is
> rendered rather than streamed, and where the assets come from, are in
> [`docs/LEVERS.md`](docs/LEVERS.md).

---

## Measured adapter costs

Every adapter in this stack was swept across six merge weights on ten fixed
utterances, and scored for intelligibility, naturalness, vocal-burst blend and
speaker similarity. The headline: **SFT3 + DPO-p2 alone is clean — word error
0.013 and not one invented word in ten takes** — and every further adapter
degrades that, monotonically in both count and weight.

If you are new to the project, start with
[`docs/LEARNINGS.md`](docs/LEARNINGS.md) — a plain-language account of the
trailing-speech bug, how it was chased, which suspicions were wrong, and what
finally fixed it.

See [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md) for the method, all prompts, all
hyper-parameters and the full tables, and `eval/results/` for the raw per-take
data including every transcript.

## Known limits

* Emotion retrieval is right about 61 % of the time over 40 classes. A wrong pick
  merged at 1.5 is audible. Gating the adapter on a retrieval-score threshold is
  the obvious next step and is not implemented.
* Voice-quality dimensions cannot be retrieved from prose with this embedding
  model at all.
* The character, profile, speaker and legacy emotion sets are off-distribution on
  SFT3, and the quality, delivery-axis and burst sets are in distribution but
  unevaluated (see above, and [`docs/ADAPTERS.md`](docs/ADAPTERS.md)).
* The corpus's own release notes record two defects in the generation run behind
  these recordings: 99.96 % of burst tags are Title-Case, which the speech model
  spells out letter by letter, and burst density came out at 33.7 % of lines
  instead of the intended 50 %. Measurements downstream of burst realisation are
  affected; speaker identity, the 57 voice dimensions, the emotion scores and
  ASR are measurements of the audio actually produced and are not.
* Age bands for the ten voices are an interpretation of a narrow scale.

---

## Licence and credits

**CC BY 4.0** — © LAION e.V. and Humaneness Labs.

You may share and adapt this work, including commercially, provided you give
appropriate credit. See [`LICENSE`](LICENSE).

The models, adapters and reference corpus this server loads carry their own
licences; follow the links in the tables above. The speech model, the adapters,
the reference corpus and VoiceCLAP-commercial are CC BY 4.0 at the time of
writing; the reference dataset is Apache-2.0.

Built on MOSS-TTS-Local by the OpenMOSS team.
