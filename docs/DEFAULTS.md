# Default settings

Generated from `config.py`. Every one of these is an
environment variable too, so nothing here needs a code edit to change.

## Models

| setting | value |
|---|---|
| `TTS_REPO` | `laion/moss-tts-local-transformer-4.55b-voice-acting-v2-sft3` |
| `TTS_REPO_BASE` | `laion/moss-tts-local-transformer-4.55b-voice-acting-v2` |
| `TTS_REPO_DPO` | `laion/moss-tts-local-transformer-4.55b-voice-acting-v2-sft-dpo` |
| `CODEC_REPO` | `OpenMOSS-Team/MOSS-Audio-Tokenizer-v2` |
| `VOICECLAP_REPO` | `laion/voiceclap-commercial` |
| `ASR_MODEL` | `nvidia/parakeet-tdt-0.6b-v3` |
| `HOSTED_MODELS` | `{'luna': 'gpt-5.6-luna', 'gemini-flash': 'gemini-3-flash', 'gemini-flash-lite': 'gemini-3.5-flash-lite'}` |
| `DEFAULT_BRAIN` | `luna` |
| `HOSTED_REASONING` | `none` |

## Adapters

| setting | value |
|---|---|
| `USE_LORA` | `True` |
| `LORA_ROOTS` | `{'character': '/home/c4r33u19/.cache/huggingface/hub/models--TTS-AGI--moss-character-loras-refined-public/snapshots/6f794348824f0c26cc87a2ae5c9ef828393b9b22/', 'burst': '/mnt/nvme/moss-15-v2-assets/loras/sft3_burst', 'sft3_voicenet': '/mnt/nvme/moss-15-v2-assets/loras/sft3_voicenet', 'sft3_quality': …` |
| `PROFILE_LORA_KIND` | `sft3_voice` |
| `SFT3_DPO_LORA` | `sft3_dpo:p2` |
| `SFT3_DPO_LAM` | `1.0` |
| `SFT3_VOICE_LAM` | `1.0` |
| `SFT3_EMOTION_LAM` | `1.0` |
| `PROFILE_LORA_LAM` | `0.25` |
| `PURE_PROFILE_LAM` | `0.5` |
| `BASE_STYLE_LORAS` | `()` |
| `AESTH_LORA` | `` |
| `AESTH_LORA_LAM` | `0.0` |
| `SPEAKER_LORA` | `speaker:velvet-sage-baritone` |
| `SPEAKER_LORA_LAM` | `1.0` |
| `MAX_CPU_ADAPTERS` | `64` |
| `PRELOAD_LORA_KINDS` | `('emotion', 'speaker')` |

## Retrieval

| setting | value |
|---|---|
| `RETRIEVAL_ON` | `True` |
| `EMOTION_NUANCE_ON` | `True` |
| `RETRIEVAL_DIR` | `/mnt/nvme/moss-15-v2-assets/retrieval` |
| `RETRIEVAL_EMO_BONUS` | `0.5` |
| `RETRIEVAL_LEVEL_PENALTY` | `0.05` |
| `REF3_DIR` | `/mnt/nvme/moss-15-v2-assets/refs3` |
| `REF_DIR` | `/mnt/nvme/moss-15-v2-assets/refs2` |
| `REF_VARIANT` | `vc_sidon` |

## Prompt format

| setting | value |
|---|---|
| `TIMED_SCRIPT` | `True` |
| `TIMED_FRAMES_PER_WORD` | `4.0` |
| `FRAME_RATE` | `12.5` |
| `SPLIT_MIN_WORDS` | `100000` |
| `BASE_REGISTER` | `spoken softly and naturally at close conversational volume, relaxed and unforced, the way someone actually talks to one person in a quiet room rather than performing to a room full of them.` |

## Generation

| setting | value |
|---|---|
| `DEFAULTS` | `{'language': 'English', 'audio_temperature': 1.0, 'audio_top_p': 0.95, 'audio_top_k': 25, 'audio_repetition_penalty': 1.1, 'text_temperature': 1.0, 'text_top_p': 1.0, 'text_top_k': 50, 'max_new_tokens': 0, 'chunk_frames': 12, 'stop_bias': None, 'seed': 0}` |
| `STOP_BIAS` | `2.0` |
| `MIN_FRAME_FRACTION` | `0.55` |
| `HOLDBACK_S` | `0.08` |
| `CROSSFADE_S` | `0.06` |
| `CTX_FRAMES` | `160` |

## Generation modes

Three levers exist, not one: the adapter merge weight this server always had, a steering
vector added to the hidden state, and classifier-free guidance. The write-up and the
evidence for every default here are in [`LEVERS.md`](LEVERS.md).

| setting | value | why |
|---|---|---|
| `GEN_MODE` | `auto` | which levers run; `auto` resolves per family from the measurements |
| `STEER_ENABLED` | `True` | steering off entirely when false |
| `CFG_ENABLED` | `True` | guidance off entirely when false |
| `AGENT_PICKS_MODE` | `True` | may the director choose the mode, or does `GEN_MODE` decide |
| `DELIVERY_LEVER` | `adapter` | on a delivery axis the adapter and the steering vector are sub-additive (-0.164, t -3.7); this picks which one runs |
| `STEER_PACK` | `/mnt/nvme/moss-15-v2-assets/steering/p3_vectors_server.npz` | the 5.3 MB distilled vector pack; **not in this repository**, see docs/LEVERS.md |
| `STEER_TAP_RANK` | `/mnt/nvme/moss-15-v2-assets/steering/tap_rank.json` | only needed when `STEER_PACK` points at the raw 112 MB research file |
| `STEER_PACK_K` | `5` | layers kept per attribute; 5 covers every shipped k |
| `WIKI_COEFFICIENTS` | `/mnt/nvme/moss-15-v2-assets/wikiskills/coefficients.json` | the measured operating point per attribute; absent, the levers are refused rather than guessed |
| `STEER_ALPHA` | `0.1` | the free setting: emotion percentile 0.4354 -> 0.5840 with word error falling |
| `STEER_ALPHA_CEILING` | `0.15` | per component; half the 0.3 at which steering collapses |
| `STEER_REALISED_CEILING` | `0.25` | per layer after components sum; the measured recipes reach 0.1926 |
| `STEER_K` | `{'emo': 1, 'vn': 3, 'qual': 0}` | layers per attribute: emotion is free only at 1, quality breaks at 2, delivery wants 3-5 |
| `STRENGTH_ALPHA_SCALE` | `{'gentle': 0.5, 'moderate': 1.0, 'strong': 1.0}` | the director's three words; it never sends a number |
| `NUMBNESS_SUBTRACTION` | `with_steer` | `with_steer` attaches -0.10 of Emotional_Numbness to a steered emotion: +0.60 genuineness (t 9.64) at no cost in emotion |
| `CFG_G` | `{'emo': 3.0, 'vn': 2.5, 'qual': 2.5}` | g = 3.0 for emotion, 2.5 for delivery, at word error <= 0.20 |
| `CFG_G_MIN` | `1.5` | below g = 1 guidance actively hurts (-0.0370 at 0.5, t -2.56) |
| `CFG_G_MAX` | `3.0` | the top of the measured ladder |
| `CFG_COST_FACTOR` | `1.93` | measured at batch 1, 1.89-1.94 over four cells; this is why guidance does not stream |
| `CFG_STEER_BRANCH` | `both` | steering both branches keeps 82 % of the effect and returns 0.209 of word error and 0.75 of genuineness |
| `QUALITY_AXES` | `('genuineness_high', 'blend_high', 'esthetics_high')` | the three perceptual axes, by the name the director uses |

With no `STEER_PACK` and no `WIKI_COEFFICIENTS` on disk the server behaves exactly as it
did before generation modes existed: every mode that needs them degrades to `adapter`,
and `/api/state` and the response payload both say so.
## Profiles & caches

| setting | value |
|---|---|
| `DEFAULT_PROFILE` | `emolia_c1699` |
| `PROFILE_LORAS` | `/mnt/nvme/moss-15-v2-assets/loras/profiles` |
| `PROFILE_REFS` | `/mnt/nvme/moss-15-v2-assets/refs2` |
| `CODE_CACHE` | `/mnt/nvme/moss-15-v2-assets/code_cache` |
| `WAV_CACHE` | `/mnt/nvme/moss-15-v2-assets/ref_wav_cache` |
| `PRELOAD_LANGS` | `('en', 'de')` |
| `TTS_GPU` | `1` |
| `LLM_GPU` | `0` |

## Everything else

| setting | value |
|---|---|
| `APP_PORT` | `8792` |
| `ASR_DEVICE` | `cuda:1` |
| `ASSETS` | `/mnt/nvme/moss-15-v2-assets/loras` |
| `BURST_LAM` | `0.25` |
| `BURST_LAM_INTENSE` | `0.5` |
| `CONTINUITY` | `the same speaker continues without interruption: identical voice, identical person, same microphone and same room.` |
| `EIV_DIR` | `/mnt/nvme/empathic-insights-voice-small` |
| `EMOTION_NAMES` | `{'Shame', 'Elation', 'Disappointment', 'Sexual_Lust', 'Sourness', 'Intoxication_Altered_States_of_Consciousness', 'Relief', 'Affection', 'Anger', 'Thankfulness_Gratitude', 'Pain', 'Sadness', 'Disgust' …` |
| `HISTORY_TURNS_LOCAL` | `8` |
| `HISTORY_TURNS_LUNA` | `40` |
| `LLM_BASE` | `http://127.0.0.1:8790` |
| `LLM_MODEL` | `gemma-4-12b-it-qat` |
| `LUNA_BASE` | `https://api.hyprlab.io` |
| `LUNA_MODEL` | `gpt-5.6-luna` |
| `MAX_SESSIONS` | `200` |
| `MEANVC2_ROOT` | `/mnt/nvme/moss-15-v2-assets/MeanVC2` |
| `QUALITY_CONFLICTS` | `{'sft3_quality:esthetics_high': {'S_RANT_high': 0.0, 'S_DRAM_high': 0.5}}` |
| `QUALITY_LABELS` | `{'sft3_quality:genuineness_high': 'Genuineness', 'sft3_quality:blend_high': 'Burst blend', 'sft3_quality:esthetics_high': 'Aesthetics'}` |
| `QUALITY_LORAS` | `{'sft3_quality:genuineness_high': 0.25, 'sft3_quality:blend_high': 0.5, 'sft3_quality:esthetics_high': 0.5}` |
| `SCORE_ATTRS` | `('Arousal', 'Valence', 'Authenticity', 'Confident_vs._Hesitant')` |
| `SCORE_DEVICE` | `cuda:1` |
| `SFT3` | `True` |
| `SFT3_VN_ADAPTERS` | `{'AROU_high': 'highly aroused, very dominant, tense, elated, thin', 'AROU_low': 'dialled down, not performed at full size; narrow pitch range, submissive, slow', 'ARSH_high': 'energised, slightly domi …` |
| `SFT3_VN_LEVELS` | `(0.5, 0.75, 1.0, 1.25, 1.5)` |
| `SFT3_VN_MAX` | `1` |
| `SIDON_CKPTS` | `/mnt/nvme/moss-15-v2-assets/sidon-ckpts` |
| `SIDON_GPU` | `0` |
| `SIDON_OUT_SR` | `48000` |
| `SIDON_SRC` | `/mnt/nvme/moss-15-v2-assets/sidon/src` |
| `SPEAKER_IDENTITY` | `the voice of one man in his early fifties. a warm, unhurried baritone that sits low and forward in the chest, like aged oak and morning mist. the timbre is dark and resonant with a soft gravel at the  …` |
| `SPEEDS` | `(0.5, 0.75, 1.0, 1.25, 1.5)` |
| `SPEED_WORDS` | `{'much_slower': 0.5, 'slower': 0.75, 'normal': 1.0, 'faster': 1.25, 'much_faster': 1.5}` |
| `TAIL_FRAMES` | `50` |
| `TAIL_TURNS` | `2` |
| `USE_ANCHOR` | `True` |
| `USE_TAIL_CONTEXT` | `True` |
| `VC_CONTEXT_S` | `1.5` |
| `VC_CROSSFADE_S` | `0.04` |
| `VC_DEVICE` | `cuda:1` |
| `VN_BASELINE` | `/mnt/nvme/moss-15-v2-assets/vn_baseline.json` |
| `VN_DIR` | `/mnt/nvme/moss-15-v2-assets/voicenet-pred` |
| `WHISPER_DIR` | `/mnt/nvme/moss-15-v2-assets/bude-whisper` |
| `_OLD_BASE_STYLE_LORAS` | `(('voicenet:vn_S_CONV__high', 0.25), ('voicenet:vn_S_CASU__high', 0.5), ('voicenet:vn_WARM__high', 0.25))` |
