"""Download every model this server needs, and say what is missing.

On a fresh machine:

    python setup/fetch_all.py            # everything
    python setup/fetch_all.py --check    # report only, download nothing
    python setup/fetch_all.py --minimal  # the speech model and what it cannot run without

The `need` column says whether the server starts without it. `--check` prints
the same table against what is already on disk, which is the quickest way to
find out why a fresh clone will not come up.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# (kind, repo, what it is, required to start?)
DEPS = [
    ("speech model", "laion/moss-tts-local-transformer-4.55b-voice-acting-v2-sft3",
     "the 4.55B voice-acting checkpoint everything else is trained against", True),
    ("codec", "OpenMOSS-Team/MOSS-Audio-Tokenizer-v2",
     "12-codebook RVQ at 12.5 Hz, 48 kHz", True),
    ("reference corpus", "TTS-AGI/moss-voice-profile-references",
     "the acted recordings the director's prose is matched against", True),
    ("adapter: preference", "laion/moss-va-sft3-dpo-lora-p2",
     "general quality, always on at 1.0", True),
    ("adapter: voice", "laion/moss-va-sft3-voice-loras",
     "speaker identity, one per profile, at 1.0", True),
    ("adapter: emotion", "laion/moss-va-sft3-emotion-loras",
     "40 emotions; the retrieved one at 1.0", True),
    ("adapter: delivery", "laion/moss-va-sft3-voicenet-lora-adapters",
     "17 VoiceNet axes; the director picks up to two", False),
    ("adapter: quality", "laion/moss-va-sft3-quality-lora-adapters",
     "genuineness 0.25, burst blend 0.5, aesthetics 0.5", False),
    ("adapter: preference 2", "laion/moss-va-sft3-quality-dpo-lora",
     "quality DPO, on at 1.5", False),
    ("adapter: preference 3", "laion/moss-va-sft3-burst-stop-dpo-lora",
     "burst and stop preferences; measured to change nothing, ships at 0.0", False),
    ("adapter: bursts", "laion/moss-va-sft3-vocal-burst-lora-adapters",
     "per-class burst adapters; budgeted to a total of 2.0", False),
    ("adapter: characters", "TTS-AGI/moss-character-loras-refined-public",
     "12 named characters, only when the director asks for one", False),
    ("scorer", "laion/voiceclap-commercial",
     "audio and text towers: retrieval, and part of the best-of-N reward", False),
    ("scorer", "laion/voiceclap-commercial-genuineness",
     "0-6 genuineness", False),
    ("scorer", "laion/voiceclap-commercial-vocalburst-blend",
     "0-10 burst blend", False),
    ("speech recognition", "nvidia/parakeet-tdt-0.6b-v3",
     "word error in the reward, and the microphone in /studio", False),
    ("forced aligner", "Qwen/Qwen3-ForcedAligner-0.6B-hf",
     "end trimming, Apache-2.0", False),
    ("restoration", "sarulab-speech/sidon-v0.1",
     "SIDON, off by default; see docs/SIDON.md", False),
    ("language model", "unsloth/gemma-4-12B-it-qat-GGUF",
     "the local director, if you are not using a hosted one", False),
]

MINIMAL = {"speech model", "codec", "reference corpus", "adapter: preference",
           "adapter: voice", "adapter: emotion"}


def on_disk(repo):
    from huggingface_hub import snapshot_download
    try:
        return snapshot_download(repo, local_files_only=True)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--minimal", action="store_true")
    a = ap.parse_args()
    from huggingface_hub import snapshot_download

    print(f"{'kind':<22}{'repo':<58}{'need':>6}  status")
    missing = 0
    for kind, repo, _what, req in DEPS:
        if a.minimal and kind not in MINIMAL:
            continue
        if on_disk(repo):
            status = "on disk"
        elif a.check:
            status = "MISSING"
            missing += int(req)
        else:
            try:
                snapshot_download(repo)
                status = "downloaded"
            except Exception as e:
                status = f"FAILED {type(e).__name__}"
                missing += int(req)
        print(f"{kind:<22}{repo:<58}{'yes' if req else 'no':>6}  {status}")
    print()
    if missing:
        print(f"{missing} required item(s) missing - the server will not start.")
    else:
        print("everything required is present.")
    print("\nFetched separately, not from the hub:")
    print("  voice profiles      python setup/fetch_profile_refs3.py")
    print("  retrieval index     python setup/build_retrieval_index.py")
    print("  burst recipes       see docs/SKILLS.md")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
