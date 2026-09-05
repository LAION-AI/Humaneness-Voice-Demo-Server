#!/usr/bin/env python3
"""Generate a turn N times and keep the best one.

The case for this is in the burst recipes themselves: they quote an `N` per
class — "at a hit rate of 0.27 it takes 8 candidates for 90 % confidence" — and
without best-of-N that column is advice nobody can act on.  The same holds for
the emotion adapters, whose own card says to generate several candidates and
rank them because the base model drifts under strong emotion.

All N candidates are one batched forward pass.  The streaming path is batch 1
because audio must start before the line ends; choosing between candidates is
the opposite situation, so it uses `generate_batch` and the whole set costs
little more than one take.

## The reward

    R = (norm(genuineness) + norm(blend) + 2 * norm(clap)) * gate(WER)

`clap` is the cosine between the take's VoiceCLAP-commercial *audio* embedding
and the *text* embedding of what the director asked for — GENERAL plus every
round bracket in the script.  It carries double weight because it is the only
term that measures whether the take is the performance that was requested; the
other two measure whether it is a good take of anything.

Normalisation is within the candidate set, not against an absolute scale.  Only
the ranking matters, the three scorers have unrelated ranges (0-6, 0-10, a
cosine), and their absolute values are not calibrated against human judgement
anyway.

`gate(WER)` is `1.0` when the inverse word error rate is above 0.85 and the
inverse rate itself below it.  Intelligibility is a threshold, not a
preference: a take everyone can understand should not beat another take everyone
can understand for being marginally more understandable, but a take that garbles
the line has to lose regardless of how good it sounds.
"""
import re

import numpy as np

import config


def direction_text(general, script):
    """What the director asked for: GENERAL plus every round bracket."""
    bits = []
    if general:
        bits.append(" ".join(str(general).split()))
    bits += [re.sub(r",?\s*[0-9]*\.?[0-9]+\s*(?:s|sec|seconds?)\b", "", c).strip()
             for c in re.findall(r"\(([^)]{2,160})\)", str(script or ""))]
    return " ".join(b for b in bits if b)[:600]


def _norm(v):
    """Min-max inside the candidate set; all-equal collapses to a constant."""
    a = np.asarray(v, dtype=np.float64)
    if not len(a):
        return a
    lo, hi = float(np.nanmin(a)), float(np.nanmax(a))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi - lo < 1e-9:
        return np.ones_like(a) * 0.5
    return (a - lo) / (hi - lo)


def gate(wer, knee=None):
    """The intelligibility factor: the inverse word error rate, straight.

    This was flattened to 1.0 above an inverse rate of 0.85, on the argument that
    intelligibility is a threshold rather than a preference.  Removed: the flat
    region covered most of a candidate set -- six of eight in one run -- so the
    factor stopped separating exactly where the candidates were closest, and the
    ranking there fell to the three perceptual terms alone.  Multiplying by the
    raw inverse rate keeps a small intelligibility difference as a small reward
    difference all the way up.

    `knee` is still honoured when passed, so the old behaviour is one argument
    away, but nothing sets it now.
    """
    inv = 1.0 - float(max(0.0, min(1.0, wer)))
    k = config.BON_WER_KNEE if knee is None else knee
    if k is not None and k > 0 and inv > k:
        return 1.0
    return inv


def rank(cands):
    """`cands`: dicts with genuineness, blend, clap, wer.  Adds reward + rank."""
    if not cands:
        return cands
    g = _norm([c.get("genuineness", 0.0) for c in cands])
    b = _norm([c.get("blend", 0.0) for c in cands])
    p = _norm([c.get("clap", 0.0) for c in cands])
    for i, c in enumerate(cands):
        c["n_genuineness"] = round(float(g[i]), 4)
        c["n_blend"] = round(float(b[i]), 4)
        c["n_clap"] = round(float(p[i]), 4)
        c["gate"] = round(gate(c.get("wer", 0.0)), 4)
        c["reward"] = round(
            float((g[i] + b[i] + config.BON_CLAP_WEIGHT * p[i]) * c["gate"]), 4)
    order = sorted(range(len(cands)), key=lambda i: -cands[i]["reward"])
    for pos, i in enumerate(order):
        cands[i]["rank"] = pos
    return cands


class Judge:
    """The three scorers plus transcription, loaded once."""

    def __init__(self, device=None, asr=None):
        self.ok = False
        self.asr = asr
        dev = device or config.BON_DEVICE
        try:
            import sys
            sys.path.insert(0, "/mnt/nvme/moss-15-v2-assets/vc_genuineness")
            sys.path.insert(0, "/mnt/nvme/moss-15-v2-assets/vc_blend")
            from blend_model import CommercialBlendScorer
            from genuineness_scorer import GenuinenessScorer
            self.gen = GenuinenessScorer(
                pkg_dir="/mnt/nvme/moss-15-v2-assets/vc_genuineness",
                model="full", device=dev)
            self.bl = CommercialBlendScorer(
                pkg_dir="/mnt/nvme/moss-15-v2-assets/vc_blend", device=dev)
            self.ok = True
        except Exception as e:
            print(f"[bestofn] scorers unavailable ({type(e).__name__}: {e})",
                  flush=True)
            return
        # the CLAP tower is already loaded for retrieval; reuse it rather than
        # holding a second copy of the same weights on the same card
        self.clap = None
        print(f"[bestofn] judge ready on {dev}", flush=True)

    def attach_clap(self, retriever):
        self.clap = retriever

    def _clap_sim(self, wav48, want_vec):
        if self.clap is None or want_vec is None:
            return 0.0
        try:
            import torch
            x = np.asarray(wav48, np.float32).reshape(-1)
            n = (len(x) // 3) * 3
            w16 = x[:n].reshape(-1, 3).mean(1)
            self.clap._load()
            with torch.no_grad():
                v = self.clap.model.encode_waveform(
                    torch.tensor(w16, dtype=torch.float32,
                                 device=self.clap.device)[None],
                    sample_rate=16000)[0].float().cpu().numpy()
            v = v - self.clap.qmu
            v /= max(np.linalg.norm(v), 1e-8)
            return float(np.dot(v, want_vec))
        except Exception as e:
            print(f"[bestofn] clap failed: {e}", flush=True)
            return 0.0

    def want_vector(self, general, script):
        """The centred text embedding of what was asked for."""
        if self.clap is None:
            return None
        txt = direction_text(general, script)
        if not txt:
            return None
        try:
            v = self.clap.embed(txt) - self.clap.qmu
            return v / max(np.linalg.norm(v), 1e-8)
        except Exception:
            return None

    def score(self, waves, sr, plain, general=None, script=None, want=None):
        """One dict per candidate, ready for `rank`."""
        import os
        import tempfile

        import soundfile as sf
        from eval_tail import trailing_words, wer as _wer
        if want is None:
            want = self.want_vector(general, script)
        out = []
        for w in waves:
            c = {"sec": round(len(w) / float(sr), 3), "genuineness": 0.0,
                 "blend": 0.0, "clap": 0.0, "wer": 1.0, "extra_w": 0, "hyp": ""}
            if w is None or len(w) < sr // 8:
                out.append(c)
                continue
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                sf.write(f.name, np.asarray(w, np.float32), sr)
                path = f.name
            try:
                c["genuineness"] = float(self.gen.score(path))
                c["blend"] = float(self.bl.score(path))
            except Exception as e:
                print(f"[bestofn] scorer: {e}", flush=True)
            finally:
                os.unlink(path)
            c["clap"] = self._clap_sim(w, want)
            if self.asr is not None and plain:
                try:
                    x = np.asarray(w, np.float32)
                    n = (len(x) // 3) * 3
                    hyp = self.asr.transcribe(x[:n].reshape(-1, 3).mean(1))
                    c["hyp"] = hyp
                    c["wer"] = float(_wer(plain, hyp))
                    c["extra_w"] = int(trailing_words(plain, hyp)[0])
                except Exception as e:
                    print(f"[bestofn] asr: {e}", flush=True)
            out.append(c)
        return out
