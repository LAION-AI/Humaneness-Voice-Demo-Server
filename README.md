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

## Quick start

```bash
git clone https://github.com/LAION-AI/Humaneness-Voice-Demo-Server
cd Humaneness-Voice-Demo-Server
pip install -r requirements.txt

python setup/fetch_all.py            # every model, with a table of what is missing
python setup/fetch_profile_refs3.py  # the reference recordings
python setup/build_retrieval_index.py

./run.sh both                        # language model + voice model + web UI
```

Then open `http://localhost:8792`, or say something without the browser:

```bash
curl -s localhost:8792/api/speak -H 'content-type: application/json' \
  -d '{"text": "Tell me the worst thing that happened this week."}' -o reply.mp3
```

**No API key is needed.** The director runs locally on `gemma-4-12B-it-qat`
through llama.cpp. A hosted model is an option, not a requirement — see
[`docs/SERVER.md`](docs/SERVER.md).

Two 24 GB cards is what this is tuned for: the language model on one, the
speech model on the other. `python setup/fetch_all.py --check` prints what is
present without downloading anything.

---

## Where to start

| you want to | read |
|---|---|
| **get acted speech out of it with curl** — the cookbook | [`docs/VOICE_ACTING_TASKS.md`](docs/VOICE_ACTING_TASKS.md) |
| **use the server over HTTP** — every endpoint, every parameter, with curl | [`docs/SERVER.md`](docs/SERVER.md) |
| know exactly what the director is told, and why | [`docs/PROMPTING.md`](docs/PROMPTING.md), [`docs/SYSTEM_PROMPTS.md`](docs/SYSTEM_PROMPTS.md) |
| **know exactly which models this loads, with URLs** | [`docs/DEPENDENCIES.md`](docs/DEPENDENCIES.md) |
| reproduce this configuration elsewhere | [`docs/DEFAULTS.md`](docs/DEFAULTS.md), then `setup/fetch_all.py` |
| understand how adapters are loaded and weighted | [`docs/ADAPTERS.md`](docs/ADAPTERS.md) |
| see what was measured, and what turned out to be wrong | [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md), [`docs/LEARNINGS.md`](docs/LEARNINGS.md) |

### The rest of the documentation

| page | what it is |
|---|---|
| [`docs/SERVER.md`](docs/SERVER.md) | the HTTP surface: `/api/speak`, the streaming turn, and everything under them |
| [`docs/API.md`](docs/API.md) | the lower-level endpoints in more detail |
| [`docs/PROMPTING.md`](docs/PROMPTING.md) | the timed-script format the speech model was trained on |
| [`docs/SYSTEM_PROMPTS.md`](docs/SYSTEM_PROMPTS.md) | the director's prompts, generated from the code so they cannot drift |
| [`docs/ADAPTERS.md`](docs/ADAPTERS.md) | every adapter set, its weight, and why merging is unsafe on this checkpoint |
| [`docs/DEFAULTS.md`](docs/DEFAULTS.md) | every shipped setting and what changed it |
| [`docs/BEST_OF_N.md`](docs/BEST_OF_N.md) | how candidates are generated and ranked |
| [`docs/GUIDANCE.md`](docs/GUIDANCE.md) | classifier-free guidance: measured twice, 3.0 beats both 1.0 and 4.0 |
| [`docs/ALIGNMENT.md`](docs/ALIGNMENT.md) | end trimming with a forced aligner |
| [`docs/SIDON.md`](docs/SIDON.md) | speech restoration: what it improves, and what it leaves exactly as it was |
| [`docs/BABBLE.md`](docs/BABBLE.md) | two ways a line came back unintelligible, and the budgets that fix them |
| [`docs/SEPTEMBER.md`](docs/SEPTEMBER.md) | a working log of 5-6 September: every change, the measurement behind it, and the script that reproduces it |
| [`docs/CONTEXT.md`](docs/CONTEXT.md) | the context window, the 400 it caused, and the guard |
| [`docs/BENCHMARK.md`](docs/BENCHMARK.md) | performing a JSON benchmark item, and the verbatim guarantee |
| [`docs/SKILLS.md`](docs/SKILLS.md) | the measured vocal-burst recipes and where they come from |
| [`docs/ARENA.md`](docs/ARENA.md) | an evolutionary search for a better director prompt, and why it came back null |
| [`docs/ARENA_PROMPTS.md`](docs/ARENA_PROMPTS.md) | every prompt used in that search, verbatim |
| [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md), [`docs/LEARNINGS.md`](docs/LEARNINGS.md), [`docs/FIELD_NOTES.md`](docs/FIELD_NOTES.md) | what was measured, what was believed and turned out wrong |
| [`docs/LEVERS.md`](docs/LEVERS.md), [`docs/TIPS.md`](docs/TIPS.md), [`docs/DIRECTOR.md`](docs/DIRECTOR.md), [`docs/ENSEMBLE.md`](docs/ENSEMBLE.md) | notes from the team that trained the adapters |

## The models this runs on

Every repository below was checked against the Hub on 7 September 2026 and
resolves. Nothing here exists only on the machine this was built on — the
`/mnt/nvme/…` paths in `config.py` are caches, and `config._root()` falls back
to the Hub copy when a local directory is absent.
[`docs/DEPENDENCIES.md`](docs/DEPENDENCIES.md) is the complete table, including
the two things that ship inside this repository rather than on the Hub, and the
exact adapter stack every burst measurement was made under.
