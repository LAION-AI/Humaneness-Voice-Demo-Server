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
| `LORA_ROOTS` | `{'emotion': '/home/c4r33u19/.cache/huggingface/hub/models--TTS-AGI--moss-emotion-loras-v3/snapshots/6fb7de6247c833ef4e1686f7932432374d27218a/', 'character': '/home/c4r33u19/.cache/huggingface/hub/models--TTS-AGI--moss-character-loras-refined-public/snapshots/6f794348824f0c26cc87a2ae5c9ef828393b9b22/ …` |
| `PROFILE_LORA_KIND` | `sft3_voice` |
| `SFT3_DPO_LORA` | `sft3_dpo:dpo` |
| `SFT3_DPO_LAM` | `1.0` |
| `SFT3_VOICE_LAM` | `1.0` |
| `SFT3_EMOTION_LAM` | `1.5` |
| `PROFILE_LORA_LAM` | `1.0` |
| `PURE_PROFILE_LAM` | `0.5` |
| `BASE_STYLE_LORAS` | `(('voicenet:vn_S_CONV__high', 0.25), ('voicenet:vn_S_CASU__high', 0.5), ('voicenet:vn_WARM__high', 0.25))` |
| `AESTH_LORA` | `voicenet:vn_ESTH__high` |
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
| `TIMED_FRAMES_PER_WORD` | `4.5` |
| `FRAME_RATE` | `12.5` |
| `SPLIT_MIN_WORDS` | `100000` |
| `BASE_REGISTER` | `spoken softly and naturally at close conversational volume, relaxed and unforced, the way someone actually talks to one person in a quiet room rather than performing to a room full of them.` |

## Generation

| setting | value |
|---|---|
| `DEFAULTS` | `{'language': 'English', 'audio_temperature': 1.0, 'audio_top_p': 0.95, 'audio_top_k': 25, 'audio_repetition_penalty': 1.1, 'text_temperature': 1.0, 'text_top_p': 1.0, 'text_top_k': 50, 'max_new_tokens': 0, 'chunk_frames': 12, 'stop_bias': None, 'seed': 0}` |
| `STOP_BIAS` | `3.0` |
| `MIN_FRAME_FRACTION` | `0.55` |
| `HOLDBACK_S` | `0.08` |
| `CROSSFADE_S` | `0.06` |
| `CTX_FRAMES` | `160` |

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
| `CONTINUITY` | `the same speaker continues without interruption: identical voice, identical person, same microphone and same room.` |
| `EIV_DIR` | `/mnt/nvme/empathic-insights-voice-small` |
| `EMOTION_NAMES` | `{'Longing', 'Bitterness', 'Pleasure_Ecstasy', 'Pain', 'Malevolence_Malice', 'Disgust', 'Fatigue_Exhaustion', 'Interest', 'Relief', 'Intoxication_Altered_States_of_Consciousness', 'Pride', 'Impatience_ …` |
| `HISTORY_TURNS_LOCAL` | `8` |
| `HISTORY_TURNS_LUNA` | `40` |
| `LLM_BASE` | `http://127.0.0.1:8790` |
| `LLM_MODEL` | `gemma-4-12b-it-qat` |
| `LUNA_BASE` | `https://api.hyprlab.io` |
| `LUNA_MODEL` | `gpt-5.6-luna` |
| `MAX_SESSIONS` | `200` |
| `MEANVC2_ROOT` | `/mnt/nvme/moss-15-v2-assets/MeanVC2` |
| `SCORE_ATTRS` | `('Arousal', 'Valence', 'Authenticity', 'Confident_vs._Hesitant')` |
| `SCORE_DEVICE` | `cuda:1` |
| `SFT3` | `True` |
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
