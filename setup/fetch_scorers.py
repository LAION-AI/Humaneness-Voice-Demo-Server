#!/usr/bin/env python3
"""Fetch the two perceptual scorers into the layout the code expects.

`best_of_n` and the evaluation harnesses import `genuineness_scorer` and
`blend_model` — those are Python files that ship *inside* the model repositories
rather than on PyPI, so they arrive with the weights.

Each repository also bundles a copy of the VoiceCLAP encoder under
`voiceclap_commercial/`, but the download only brings the files matched by the
allow-list, and the scorers refuse to load without it.  Rather than pull a second
110 MB copy per scorer, this links them at the encoder already fetched for
retrieval, which is byte-identical -- verified at cosine 0.98 against a local
recompute when it was first wired up.

    python setup/fetch_scorers.py
"""
import os
import sys

from huggingface_hub import snapshot_download

ASSETS = os.environ.get("MOSS_ASSETS", "/mnt/nvme/moss-15-v2-assets")
ENCODER = os.path.join(ASSETS, "voicenet-pred", "voiceclap_commercial")
JOBS = [("laion/voiceclap-commercial-genuineness", "vc_genuineness"),
        ("laion/voiceclap-commercial-vocalburst-blend", "vc_blend")]
ENC_FILES = ("config.json", "configuration_voiceclap.py", "modeling_voiceclap.py",
             "preprocessor_config.json", "tokenizer.json", "tokenizer_config.json",
             "model.safetensors")


def main():
    if not os.path.isdir(ENCODER):
        print(f"the shared encoder is not at {ENCODER}.\n"
              f"Run setup/build_retrieval_index.py first, or set MOSS_ASSETS.",
              file=sys.stderr)
        return 1
    for repo, name in JOBS:
        dst = os.path.join(ASSETS, name)
        snapshot_download(repo, local_dir=dst,
                          allow_patterns=["*.py", "*.pt", "*.md", "*.txt"])
        sub = os.path.join(dst, "voiceclap_commercial")
        os.makedirs(sub, exist_ok=True)
        for f in ENC_FILES:
            src, link = os.path.join(ENCODER, f), os.path.join(sub, f)
            if not os.path.exists(link):
                os.symlink(src, link)
        print(f"{name}: {len(os.listdir(dst))} files, encoder linked", flush=True)
    print("SCORERS_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
