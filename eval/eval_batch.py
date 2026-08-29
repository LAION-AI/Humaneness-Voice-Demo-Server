#!/usr/bin/env python3
"""Adapter sweeps over /api/say_batch — one forward pass per condition.

Every condition is the same ten utterances on top of SFT3 + DPO-p2, with one
adapter added at one weight.  Four measurements per take:

  wer, extra_w   intelligibility and words invented past the end of the line
  genuineness    laion/voiceclap-commercial-genuineness, 0-6
  blend          laion/voiceclap-commercial-vocalburst-blend, 0-10
  spk_sim        ECAPA cosine against the voice's own reference recording

The point of the batch endpoint is throughput: the streaming path is batch 1
because audio has to start before the line ends, which a sweep does not need.
"""
import argparse, base64, json, os, sys, time

import numpy as np
import requests

sys.path.insert(0, "/mnt/nvme/moss-15-v2")
import config
import timed_script
from eval_tail import ASR, PROMPTS, GENERAL, wer, trailing_words, resample_48k_to_16k
from eval_scale import Scorers, ANCHOR, DPO

URL = "http://127.0.0.1:8792/api/say_batch"


def build_items(n):
    items, refs = [], []
    for line, cue in PROMPTS[:n]:
        tagged, frames, _ = timed_script.render(f"{cue} {line}")
        items.append({"text": tagged, "tokens": frames, "language": "English",
                      "instruction": f"GENERAL: {GENERAL}; {frames/12.5:.1f}s, EN."
                                     f"\nSCRIPT:\n{tagged}"})
        refs.append(line)
    return items, refs


def run(cond, loras, items, refs, asr, sc, seed=1234):
    r = requests.post(URL, json={"items": items, "loras": [[n, l] for n, l in loras],
                                 "seed": seed, "anchor_path": ANCHOR}, timeout=3600)
    r.raise_for_status()
    j = r.json()
    rows = []
    for i, b64 in enumerate(j["pcm"]):
        pcm = np.frombuffer(base64.b64decode(b64), "<i2").astype(np.float32) / 32768.0
        if len(pcm) < 4800:
            continue
        hyp, last_t = asr.run(resample_48k_to_16k(pcm))
        extra, xw = trailing_words(refs[i], hyp)
        g, bl, s = sc.score(pcm)
        rows.append({"prompt": i, "wer": wer(refs[i], hyp), "extra_w": extra,
                     "tail_s": len(pcm) / 48000.0 - last_t,
                     "genuineness": g, "blend": bl, "spk_sim": s,
                     "hyp": hyp, "extra_words": " ".join(xw)[:100]})
    if not rows:
        return None
    m = lambda k: float(np.nanmean([x[k] for x in rows]))
    return {"condition": cond, "loras": loras, "n": len(rows),
            "gpu_ms": j.get("gpu_ms"),
            "wer": m("wer"), "extra_w": m("extra_w"), "tail_s": m("tail_s"),
            "genuineness": m("genuineness"), "blend": m("blend"),
            "spk_sim": m("spk_sim"),
            "pct_extra": float(np.mean([x["extra_w"] > 0 for x in rows])),
            "takes": rows}


def adapters_of(kind):
    import glob
    root = config.LORA_ROOTS.get(kind, "")
    if not root or not os.path.isdir(root):
        return []
    return sorted(os.path.basename(os.path.dirname(f))
                  for f in glob.glob(os.path.join(root, "*", "adapter_model.safetensors")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="quality",
                    help="quality | voice | voicenet | emotion | baseline")
    ap.add_argument("--scales", default="0.25,0.5,0.75,1.0,1.25,1.5")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    scales = [float(x) for x in a.scales.split(",") if x.strip()]
    out_p = a.out or f"/mnt/nvme/moss-15-v2-assets/sweep_{a.set}.json"

    items, refs = build_items(a.n)
    asr, sc = ASR(), Scorers()
    todo = []
    if a.set == "baseline":
        todo = [("baseline sft3+dpo", [])]
    elif a.set == "quality":
        for n in adapters_of("sft3_quality"):
            todo += [(f"{n} @{w}", [(f"sft3_quality:{n}", w)]) for w in scales]
    elif a.set == "voice":
        for w in scales:
            todo.append((f"voice emolia_c1699 @{w}", [("sft3_voice:emolia_c1699", w)]))
    elif a.set == "voicenet":
        for n in adapters_of("sft3_voicenet"):
            todo += [(f"{n} @{w}", [(f"sft3_voicenet:{n}", w)]) for w in scales]
    elif a.set == "emotion":
        for n in adapters_of("sft3_emotion"):
            todo += [(f"{n} @{w}", [(f"sft3_emotion:{n}", w)]) for w in scales]
    else:
        raise SystemExit("unknown --set")

    res = []
    if os.path.exists(out_p):
        try:
            res = json.load(open(out_p))
        except Exception:
            res = []
    done = {r["condition"] for r in res}
    t0 = time.time()
    for i, (cond, extra) in enumerate(todo, 1):
        if cond in done:
            continue
        try:
            rec = run(cond, [(DPO, 1.0)] + extra, items, refs, asr, sc)
        except Exception as e:
            print(f"  {cond}: {str(e)[:140]}", flush=True)
            continue
        if not rec:
            continue
        res.append(rec)
        json.dump(res, open(out_p, "w"), indent=1)
        el = time.time() - t0
        print(f'[{i}/{len(todo)}] {cond:28s} wer={rec["wer"]:.3f} '
              f'extra={rec["extra_w"]:4.1f}({rec["pct_extra"]:.0%}) '
              f'genuine={rec["genuineness"]:.2f} blend={rec["blend"]:.2f} '
              f'spk={rec["spk_sim"]:.3f}  [{el/60:.0f}m]', flush=True)
    print("SWEEP_DONE", flush=True)


if __name__ == "__main__":
    main()
