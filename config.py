"""Central configuration for the MOSS voice-acting demo."""
import os, glob

# ---------------------------------------------------------------- models
# Full-parameter SFT + DPO tuning of the v2 base — same architecture, tokenizer
# and prompt format, so it swaps in directly.  Note the character adapters were
# trained against the *untuned* v2 weights, so stacking one on this checkpoint is
# off-distribution; it is offered as a switch rather than a default.
# SFT round 3: the round that trained the inline delivery directions back in.
# Word error rate on direction-carrying prompts 0.447 -> 0.099, vocal-burst hit
# rate 0.516 -> 0.666, every clip within 0.5 s of the requested length.  Since
# this demo writes a direction into every single sentence, that is the whole
# ballgame.  Same architecture and prompt format, so it swaps in directly.
TTS_REPO = os.environ.get(
    "MOSS_TTS_REPO",
    "laion/moss-tts-local-transformer-4.55b-voice-acting-v2-sft3")
TTS_REPO_DPO = "laion/moss-tts-local-transformer-4.55b-voice-acting-v2-sft-dpo"
TTS_REPO_BASE = "laion/moss-tts-local-transformer-4.55b-voice-acting-v2"
CODEC_REPO = os.environ.get("MOSS_CODEC_REPO", "OpenMOSS-Team/MOSS-Audio-Tokenizer-v2")

# GPU split: language model on one card, voice-acting model on the other.
# The app is launched with CUDA_VISIBLE_DEVICES=1,0 so cuda:0 is the voice card
# and cuda:1 is the one the language model sits on, which still has room for the
# small speech-recognition and voice-conversion models.
TTS_GPU = os.environ.get("MOSS_TTS_GPU", "1")
LLM_GPU = os.environ.get("MOSS_LLM_GPU", "0")

ASR_MODEL = os.environ.get("MOSS_ASR_MODEL", "nvidia/parakeet-tdt-0.6b-v3")
ASR_DEVICE = os.environ.get("MOSS_ASR_DEVICE", "cuda:1")

# optional voice conversion, off unless the user ticks the box
MEANVC2_ROOT = os.environ.get("MOSS_MEANVC2_ROOT",
                              "/mnt/nvme/moss-15-v2-assets/MeanVC2")
VC_DEVICE = os.environ.get("MOSS_VC_DEVICE", "cuda:1")
VC_CONTEXT_S = float(os.environ.get("MOSS_VC_CONTEXT_S", "1.5"))
# short equal-power join between converted chunks, hides residual drift
VC_CROSSFADE_S = float(os.environ.get("MOSS_VC_CROSSFADE_S", "0.04"))

# ---------------------------------------------------------------- reference bank
def _find_refs():
    p = os.environ.get("MOSS_REF_DIR")
    if p:
        return p
    hits = sorted(glob.glob(os.path.expanduser(
        "~/.cache/huggingface/hub/datasets--TTS-AGI--moss-voice-profile-references"
        "/snapshots/*/")))
    return hits[-1] if hits else ""

REF_DIR = os.environ.get("MOSS_REF_DIR_OVERRIDE") or "/mnt/nvme/moss-15-v2-assets/refs2"
# decoded-to-wav cache so the codec never has to touch mp3
# on /mnt/nvme, not the root fs: five tempo variants of 832 clips is ~3.4 GB and
# / is down to single-digit gigabytes
WAV_CACHE = os.environ.get("MOSS_WAV_CACHE",
                           "/mnt/nvme/moss-15-v2-assets/ref_wav_cache")
# only these languages are pre-tokenized into RAM (the demo speaks en/de)
PRELOAD_LANGS = tuple(os.environ.get("MOSS_PRELOAD_LANGS", "en,de").split(","))

# "voice_converted" pushes every condition onto the same target speaker
# (similarity to the anchor 0.726 vs 0.507 for "original", improved in 100% of
# groups) at the cost of ~0.057 emotional cosine.  Identity across turns is what
# this demo needs, so it is the default.
REF_VARIANT = os.environ.get("MOSS_REF_VARIANT", "vc_sidon")

# ---------------------------------------------------------------- identity
# The manual's first rule for consistency across clips: keep the GENERAL voice
# description BYTE-IDENTICAL and vary only the delivery.  A model that rewrites
# its own voice every turn recasts the part every turn, which is exactly the
# drift we are avoiding.  The language model writes only the delivery half.
# This must describe the ACTUAL anchor speaker of the reference corpus
# (index.json -> _speaker: "Velvet Sage Baritone", male, late 40s-60s).  A
# description that contradicts the reference codes fights them instead of
# reinforcing them, and speaker similarity collapses.
# Fallback only: with a voice profile selected (the normal case) the identity
# sentence comes from that profile's own speaker card instead.
SPEAKER_IDENTITY = os.environ.get("MOSS_SPEAKER_IDENTITY", (
    "the voice of one man in his early fifties. a warm, unhurried baritone that "
    "sits low and forward in the chest, like aged oak and morning mist. the "
    "timbre is dark and resonant with a soft gravel at the bottom of the "
    "register, the vowels are round and slightly drawn out, and consonants land "
    "softly rather than sharply. he speaks in an easy, measured, conversational "
    "manner, commanding without ever raising his voice for effect, and deeply "
    "contemplative between phrases — he thinks before he speaks and it is "
    "audible. this is always the same speaker, the same person, the same age and "
    "the same throat, recorded on the same microphone in the same room, no cut, "
    "no new narrator, no change of casting, no matter what he is feeling."
))
# appended to every instruction so the model is told the take continues the voice
CONTINUITY = ("the same speaker continues without interruption: identical voice, "
              "identical person, same microphone and same room.")

# The baseline register, appended to every GENERAL block.  Without it the model
# performs at the volume of a stage actor by default; this asks for the register
# of someone talking to one person in a room.  It is a floor, not a ceiling —
# the director's own delivery line sits before it and an explicit "roaring" or
# "screaming" there still wins, because it is the more specific instruction.
BASE_REGISTER = os.environ.get("MOSS_BASE_REGISTER", (
    "spoken softly and naturally at close conversational volume, relaxed and "
    "unforced, the way someone actually talks to one person in a quiet room "
    "rather than performing to a room full of them."))

# Stack the corpus anchor clip in front of the delivery clip as a second
# reference, so identity and performance come from separate recordings.
USE_ANCHOR = os.environ.get("MOSS_USE_ANCHOR", "1") not in ("0", "false", "")

# ---------------------------------------------------------------- tempo
# Every reference is also kept at four other tempi (pitch preserved, via
# audiostretchy), so "say that faster" swaps in a genuinely faster take of the
# same performance instead of just asking the model to hurry.
SPEEDS = (0.5, 0.75, 1.0, 1.25, 1.5)
SPEED_WORDS = {"much_slower": 0.5, "slower": 0.75, "normal": 1.0,
               "faster": 1.25, "much_faster": 1.5}

# ---------------------------------------------------------------- adapters
ASSETS = os.environ.get("MOSS_ASSETS", "/mnt/nvme/moss-15-v2-assets/loras")


def _snap(repo, local=None):
    """Prefer a plain directory under ASSETS, fall back to the HF cache.

    The full adapter collection does not fit on the root filesystem, so the big
    sets live on /mnt/nvme instead.
    """
    if local:
        d = os.path.join(ASSETS, local)
        if os.path.isdir(d):
            return d
    hits = sorted(glob.glob(os.path.expanduser(
        f"~/.cache/huggingface/hub/models--{repo.replace('/', '--')}/snapshots/*/")))
    return hits[-1] if hits else ""

# Only what fits: the full 168 GB of published adapters does not go on this disk.
# See PLAN_LORA.md for what was left out and why.
LORA_ROOTS = {
    "emotion":   _snap("TTS-AGI/moss-emotion-loras-v3"),
    "character": _snap("TTS-AGI/moss-character-loras-refined-public"),
    "burst":     _snap("laion/vocal-burst-lora-adapters", "bursts"),
    "voicenet":  _snap("laion/moss-voicenet-dimension-loras", "voicenet"),
    "sports":    _snap("laion/moss-sports-commentator-lora"),
    # the anchor speaker as a trained adapter — the direct route to a consistent
    # voice, as opposed to converting after the fact
    "speaker":   _snap("TTS-AGI/moss-voice-lora-velvet-sage-baritone", "speaker"),
    "profile":   os.environ.get("MOSS_PROFILE_LORAS",
                                "/mnt/nvme/moss-15-v2-assets/loras/profiles"),
    # Trained against sft3 itself, so these are the in-distribution pair for the
    # checkpoint above.  Voice adapters carry identity and no affect; emotion
    # adapters carry affect and no identity; they stack.
    # rank 64 where the other two are rank 16 — which is exactly why PEFT's
    # add_weighted_adapter refuses the combination and the three are activated
    # and scaled separately.  Merging deltas, as this bank does, has no such
    # constraint.
    "sft3_dpo":     "/mnt/nvme/moss-15-v2-assets/loras/sft3_dpo",
    "sft3_voice":   "/mnt/nvme/moss-15-v2-assets/loras/sft3_voice",
    "sft3_emotion": "/mnt/nvme/moss-15-v2-assets/loras/sft3_emotion",
}

# Which adapter set the speaker comes from.  The sft3 voice adapters were trained
# against the sft3 weights; the older profile adapters were not, so they are
# off-distribution on this checkpoint.
SFT3 = "sft3" in TTS_REPO
PROFILE_LORA_KIND = os.environ.get("MOSS_PROFILE_LORA_KIND",
                                   "sft3_voice" if SFT3 else "profile")
# 1.0 is the trained value for the voice adapters and has not been swept.
SFT3_VOICE_LAM = float(os.environ.get("MOSS_SFT3_VOICE_LAM", "1.0"))
# The general-quality adapter of the recommended three-way stack, at its
# published weight.
SFT3_DPO_LORA = os.environ.get("MOSS_SFT3_DPO_LORA", "sft3_dpo:dpo")
SFT3_DPO_LAM = float(os.environ.get("MOSS_SFT3_DPO_LAM", "1.0"))
# 1.5 is the published operating point from a 31-adapter scale sweep: emotion
# 0.408 -> 0.471, genuineness and burst blend both rise with it, median word
# error rate still 0.000 and mean at its lowest.  Intelligibility only breaks
# between 1.5 and 2.0, and as a tail of derailed clips rather than general decay.
SFT3_EMOTION_LAM = float(os.environ.get("MOSS_SFT3_EMOTION_LAM", "1.5"))
USE_LORA = os.environ.get("MOSS_USE_LORA", "1") not in ("0", "false", "")
# emotion adapters are the ones the agent reaches for most, so they sit in RAM
PRELOAD_LORA_KINDS = tuple(
    os.environ.get("MOSS_PRELOAD_LORA", "emotion,speaker").split(","))

# Speaker adapter: merged into every turn unless the demo switches it off.
# Its own config carries alpha/r = 2.0; this is the extra dose on top.
SPEAKER_LORA = os.environ.get("MOSS_SPEAKER_LORA", "speaker:velvet-sage-baritone")
SPEAKER_LORA_LAM = float(os.environ.get("MOSS_SPEAKER_LORA_LAM", "1.0"))

# Aesthetics adapter, off by default: it is a quality/polish dimension rather
# than a per-moment acting choice, so it gets its own dial instead of being
# something the director picks.
AESTH_LORA = os.environ.get("MOSS_AESTH_LORA", "voicenet:vn_ESTH__high")
# Off by default on SFT3: it was trained against the untuned v2 weights, so on
# this checkpoint it is off-distribution, and at 1.1 it was the strongest
# such adapter in the stack.  The slider still turns it back on.
AESTH_LORA_LAM = float(os.environ.get("MOSS_AESTH_LORA_LAM", "0.0"))

# Merged into every turn unless the request overrides them: without these the
# delivery leans formal and read-aloud, and "looser" is what a chat should sound
# like.  A persona that wants a different register just names other codes, which
# stack on top rather than fighting these.
BASE_STYLE_LORAS = (("voicenet:vn_S_CONV__high", 0.25),
                    ("voicenet:vn_S_CASU__high", 0.5),
                    ("voicenet:vn_WARM__high", 0.25))

# ---------------------------------------------------------------- services
LLM_BASE = os.environ.get("MOSS_LLM_BASE", "http://127.0.0.1:8790")
LLM_MODEL = os.environ.get("MOSS_LLM_MODEL", "gemma-4-12b-it-qat")
APP_PORT = int(os.environ.get("MOSS_APP_PORT", "8792"))

# hosted alternative brain.  The key is read from a 0600 file outside the repo and
# never leaves the server — the browser only ever sends the string "luna".
LUNA_BASE = os.environ.get("MOSS_LUNA_BASE", "https://api.hyprlab.io")
LUNA_MODEL = os.environ.get("MOSS_LUNA_MODEL", "gpt-5.6-luna")
LUNA_KEY_FILE = os.environ.get("MOSS_LUNA_KEY_FILE",
                               "/home/c4r33u19/moss15v2/.hyprlab_key")


def luna_key():
    try:
        with open(LUNA_KEY_FILE) as f:
            return f.read().strip()
    except Exception:
        return os.environ.get("HYPRLAB_API_KEY", "")

# ---------------------------------------------------------------- generation
# 12.5 Hz codec frames.  chunk_frames sets how often a partial decode is emitted.
DEFAULTS = dict(
    language="English",
    audio_temperature=1.0,
    audio_top_p=0.95,
    audio_top_k=25,
    audio_repetition_penalty=1.1,
    text_temperature=1.0,
    text_top_p=1.0,
    text_top_k=50,
    max_new_tokens=0,     # derived from the duration budget, see TOKEN_HEADROOM
    chunk_frames=12,      # ~1 s of audio per streamed chunk
    stop_bias=None,       # None -> config.STOP_BIAS
    seed=0,
)

# streaming decode window (see tts_engine): 80 ms hold-back, 30 ms crossfade,
# 48 frames (~4 s) of left context keeps timbre stable and seams click-free.
# duration control.  The model card: "pass tokens ~= words * 6 (12.5 Hz codec
# frames) via build_user_message to avoid rushed pacing".  Without it the model
# chooses its own length and often stops mid-line.
TOKENS_PER_WORD = float(os.environ.get("MOSS_TOKENS_PER_WORD", "6"))
# hard generation cap as a multiple of the requested duration, so cues, pauses
# and bursts have room without letting a runaway take go forever
TOKEN_HEADROOM = float(os.environ.get("MOSS_TOKEN_HEADROOM", "2.5"))
# below this many spoken words a reply is generated in one take: truncation was
# only ever observed on longer, multi-sentence replies, and splitting costs a
# full re-prefill per part
# Never split a reply into separate generations by default: separate takes are
# sampled independently and the voice and emotion visibly jump at the seam.
# Truncation is handled inside the single take instead (MIN_FRAME_FRACTION).
SPLIT_MIN_WORDS = int(os.environ.get("MOSS_SPLIT_MIN_WORDS", "100000"))
# refuse the end token below this fraction of the requested duration
MIN_FRAME_FRACTION = float(os.environ.get("MOSS_MIN_FRAME_FRACTION", "0.55"))
# Logit bias on the token that ends a take, in nats, subtracted before sampling.
# The floor above is all-or-nothing — below it the end token cannot win at all,
# above it nothing is changed — so a take that runs past the floor and then stops
# a few words early is untouched by it.  A gentle constant bias leans against
# stopping everywhere instead, without ever forbidding it.
STOP_BIAS = float(os.environ.get("MOSS_STOP_BIAS", "3.0"))

FRAME_RATE = 12.5          # RVQ frames per second
HOLDBACK_S = 0.08
CROSSFADE_S = 0.06         # wider seam: 30 ms left an audible edge on long takes
# Left context for each partial decode.  At 48 frames (~3.8 s) the window starts
# sliding partway through a normal reply, and from that point the decoded audio
# diverges from a full decode — measured max deviation 0.91 late in a 6.8 s take.
# 160 frames covers ~13 s, so most replies never slide at all.
CTX_FRAMES = int(os.environ.get("MOSS_CTX_FRAMES", "160"))

# how much conversation the director keeps in view (messages, not turns)
HISTORY_TURNS_LUNA = int(os.environ.get("MOSS_HISTORY_LUNA", "40"))
HISTORY_TURNS_LOCAL = int(os.environ.get("MOSS_HISTORY_LOCAL", "8"))

# Sidon speech restoration, used once to turn the quiet 16 kHz corpus anchor into
# a full-bandwidth conversion target
SIDON_SRC = os.environ.get("MOSS_SIDON_SRC", "/mnt/nvme/moss-15-v2-assets/sidon/src")
SIDON_CKPTS = os.environ.get("MOSS_SIDON_CKPTS",
                             "/mnt/nvme/moss-15-v2-assets/sidon-ckpts")
SIDON_OUT_SR = int(os.environ.get("MOSS_SIDON_OUT_SR", "48000"))
SIDON_GPU = os.environ.get("MOSS_SIDON_GPU", "0")

# ---------------------------------------------------------------- scoring
# points at the copy that already existed on this box; a second one was
# downloaded by mistake and removed again (16 GB, byte-identical)
EIV_DIR = os.environ.get("MOSS_EIV_DIR", "/mnt/nvme/empathic-insights-voice-small")
WHISPER_DIR = os.environ.get("MOSS_WHISPER_DIR",
                             "/mnt/nvme/moss-15-v2-assets/bude-whisper")
VN_DIR = os.environ.get("MOSS_VN_DIR", "/mnt/nvme/moss-15-v2-assets/voicenet-pred")
SCORE_DEVICE = os.environ.get("MOSS_SCORE_DEVICE", "cuda:1")
# the EIV suite mixes 40 emotions with attributes (Age, Arousal, ...); only the
# emotions are ranked as "what it heard"
EMOTION_NAMES = {
    "Affection", "Amusement", "Anger", "Astonishment_Surprise", "Awe",
    "Bitterness", "Concentration", "Confusion", "Contemplation", "Contempt",
    "Contentment", "Disappointment", "Disgust", "Distress", "Doubt", "Elation",
    "Embarrassment", "Emotional_Numbness", "Fatigue_Exhaustion", "Fear",
    "Helplessness", "Hope_Enthusiasm_Optimism", "Impatience_and_Irritability",
    "Infatuation", "Interest", "Intoxication_Altered_States_of_Consciousness",
    "Jealousy_and_Envy", "Longing", "Malevolence_Malice", "Pain",
    "Pleasure_Ecstasy", "Pride", "Relief", "Sadness", "Sexual_Lust", "Shame",
    "Sourness", "Teasing", "Thankfulness_Gratitude", "Triumph",
}
# a few attributes are worth showing next to the emotions
SCORE_ATTRS = ("Arousal", "Valence", "Authenticity", "Confident_vs._Hesitant")
VN_BASELINE = os.environ.get("MOSS_VN_BASELINE",
                             "/mnt/nvme/moss-15-v2-assets/vn_baseline.json")

# hosted brains, all through the same OpenAI-compatible endpoint
HOSTED_MODELS = {
    "luna": "gpt-5.6-luna",
    "gemini-flash": "gemini-3-flash",
    "gemini-flash-lite": "gemini-3.5-flash-lite",
}
# no deliberation needed for a character decision, and it halves the latency
HOSTED_REASONING = os.environ.get("MOSS_HOSTED_REASONING", "none")
HOSTED_MAX_TOKENS = int(os.environ.get("MOSS_HOSTED_MAX_TOKENS", "3000"))
# gemini-3.5-flash-lite with reasoning off: measured 1.5 s against luna's 2.4 s
# and gemini-3-flash's 3.2 s, and this turn needs a character decision, not
# deliberation
DEFAULT_BRAIN = os.environ.get("MOSS_DEFAULT_BRAIN", "luna")

# ---------------------------------------------------------------- continuity
# Carry a short tail of the previous replies into the next generation, so the
# voice continues rather than restarts.  Tails only: the manual measured whole-
# clip chaining collapsing speaker similarity from 0.777 to 0.280 by clip four.
USE_TAIL_CONTEXT = os.environ.get("MOSS_TAIL_CONTEXT", "1") not in ("0", "false", "")
TAIL_FRAMES = int(os.environ.get("MOSS_TAIL_FRAMES", "50"))   # 50 / 12.5 Hz = 4 s
TAIL_TURNS = int(os.environ.get("MOSS_TAIL_TURNS", "2"))
MAX_SESSIONS = int(os.environ.get("MOSS_MAX_SESSIONS", "200"))

# ---------------------------------------------------------------- profiles
# Ten speaker profiles: one adapter and one anchor recording each.  The adapter
# collection is small (0.38 GB for all ten at the shipped rank) because only the
# top level of each voice folder is used — the ranks/ tree is an audit trail,
# not a menu.
PROFILE_LORAS = os.environ.get("MOSS_PROFILE_LORAS",
                               "/mnt/nvme/moss-15-v2-assets/loras/profiles")
PROFILE_REFS = os.environ.get("MOSS_PROFILE_REFS",
                              "/mnt/nvme/moss-15-v2-assets/refs2")
DEFAULT_PROFILE = os.environ.get("MOSS_DEFAULT_PROFILE", "emolia_c1699")
# The profile adapter is the speaker; at 0.25 the identity barely came through.
# It also replaces the standalone velvet-sage dial rather than stacking with it.
PROFILE_LORA_LAM = float(os.environ.get("MOSS_PROFILE_LORA_LAM", "1.0"))

# Host-RAM cache bound for adapters.  65 GB exist on disk; without a cap a long
# session loads its way through them until the kernel intervenes.
MAX_CPU_ADAPTERS = int(os.environ.get("MOSS_MAX_CPU_ADAPTERS", "64"))

# Pure mode: base model + retrieved reference clips + the voice's own character
# adapter, nothing else.  The 500-voice release measured its adapters at scale
# 1.0 only, but with no expressive adapters underneath, a lighter dose keeps more
# of the base model's own acting; 0.5 is the starting point.
PURE_PROFILE_LAM = float(os.environ.get("MOSS_PURE_PROFILE_LAM", "0.5"))

# ---------------------------------------------------------------- retrieval
# The director's prose, matched against the corpus rather than decoded into
# codes.  See retrieval.py for the measurements that set the shape of this.
RETRIEVAL_DIR = os.environ.get("MOSS_RETRIEVAL_DIR",
                               "/mnt/nvme/moss-15-v2-assets/retrieval")
VOICECLAP_REPO = os.environ.get("MOSS_VOICECLAP", "laion/voiceclap-commercial")
REF3_DIR = os.environ.get("MOSS_REF3_DIR", "/mnt/nvme/moss-15-v2-assets/refs3")
# on by default: retrieval picks the reference clip and the emotion adapter.
# Turned off, the turn runs on the base checkpoint and the retrieved clip alone.
RETRIEVAL_ON = os.environ.get("MOSS_RETRIEVAL", "1") not in ("0", "false", "")
EMOTION_NUANCE_ON = os.environ.get("MOSS_EMOTION_NUANCE", "1") not in ("0", "false", "")
# The two axes are not equally good, so they are not equally weighted.  Matching
# the cues against the emotion text anchors scores 0.61 top-1; matching the full
# direction against the audio centroids scores 0.28.  A bonus for conditions of
# the winning emotion lets the clip choice inherit the stronger axis while audio
# similarity still picks the level and the take within it.  Swept on the same
# held-out set: 0.0 -> 0.17, 0.15 -> 0.39, 0.3 -> 0.61, and flat above that.
# 0.3 was the knee while the raw GENERAL went into the query.  With the static
# identity clauses filtered out the audio side is cleaner but weaker on its own,
# and the knee moves to 0.5: 0.1 -> 0.33, 0.3 -> 0.50, 0.5 -> 0.61, flat above.
RETRIEVAL_EMO_BONUS = float(os.environ.get("MOSS_RETRIEVAL_EMO_BONUS", "0.5"))
RETRIEVAL_LEVEL_PENALTY = float(os.environ.get("MOSS_RETRIEVAL_LEVEL_PEN", "0.05"))

# Tokenised reference codes, kept on disk so a restart does not re-encode the
# corpus and an un-preloaded clip costs a file read rather than a GPU pass.
CODE_CACHE = os.environ.get("MOSS_CODE_CACHE",
                            "/mnt/nvme/moss-15-v2-assets/code_cache")

# Speech rate for the timed script format, in frames per word.  TOKENS_PER_WORD
# (6) is the model card's budget for an *untimed* prompt, where overshooting
# only costs headroom.  Here the number is an instruction the checkpoint obeys,
# and 6 frames a word drags: the format's own worked example runs 13 words in
# 4.7 s, which is 4.5 frames a word.
TIMED_FRAMES_PER_WORD = float(os.environ.get("MOSS_TIMED_FPW", "4.5"))
# The SFT3 timed script: durations, pauses and burst lengths that add up to the
# Tokens budget, with the script repeated byte-identically into the Text field.
TIMED_SCRIPT = os.environ.get("MOSS_TIMED_SCRIPT", "1") not in ("0", "false", "")
