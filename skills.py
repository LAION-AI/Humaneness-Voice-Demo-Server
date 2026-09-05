#!/usr/bin/env python3
"""The measured knowledge layer, rendered into something the director can read.

`wikiskills/` is a generated corpus: sixty attribute pages, a machine-readable
`coefficients.json` the lever planner already reads, and `VOCAL_BURSTS.md`, which
is the part that changes what the director should write.  This module turns the
burst tables into two things the server can act on — a per-class merge weight and
a prompt block naming the sounds that actually exist.

Why it matters more than a documentation update: the instructions this server was
shipping contradict the measurements in two places.

  * It told the director to place bursts **mid-sentence**.  Measured, mid-clause
    placement is worse on 15 of 15 classes (-0.07..-0.12 hit rate, miss rate
    +0.31..+0.37, t 8-10).  One inversion: `clears_throat` goes 0.250 -> 0.483.
  * It offered every burst that has an adapter.  Nineteen classes never realise
    at any dose under either prompt form, and seventeen more sit below the 0.15
    bar.  Every mouth class and every whistle class in the bank is on one of
    those lists.  Offering them produces a silent take and no warning.

And one thing it did not know: the useful merge weight is **per class** and runs
0.25 to 2.3, against the flat 0.25 / 0.5 shipped here.

The tables are parsed rather than transcribed, for the same reason the wiki is
generated rather than typed: a copy stops agreeing with its source the moment
either moves.
"""
import os
import re

import config

_NUM = re.compile(r"^-?[0-9]+(?:[.,][0-9]+)?$")


def _f(x):
    x = str(x).strip().replace("**", "").replace(",", ".")
    return float(x) if _NUM.match(x.replace(",", ".")) else None


def _rows(md, header_must):
    """Every pipe-table row under a header containing all of `header_must`."""
    out, cols = [], None
    for line in md.splitlines():
        if not line.strip().startswith("|"):
            cols = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        low = [c.lower() for c in cells]
        if cols is None:
            if all(any(m in c for c in low) for m in header_must):
                cols = cells
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        out.append(dict(zip(cols, cells)))
    return out


def _cls(cell):
    """`[`vb/chuckle`](patterns/vb-chuckle.md)` -> `chuckle`."""
    m = re.search(r"`([a-z]+)/([a-z0-9_]+)`", cell)
    if m:
        return m.group(2)
    m = re.search(r"`([a-z0-9_]+)`", cell)
    return m.group(1) if m else None


class Skills:
    def __init__(self, root=None):
        self.root = root or config.SKILLS_DIR
        self.ok = False
        self.recipes = {}          # class -> {w, form, hit, n, source}
        self.never = set()         # never realises at any dose
        self.weak = {}             # class -> hit rate, below the shipping bar
        p = os.path.join(self.root, "VOCAL_BURSTS.md")
        if not os.path.exists(p):
            print(f"[skills] no wikiskills at {self.root}", flush=True)
            return
        md = open(p, encoding="utf-8").read()
        self._parse_main(md)
        self._parse_merge(md)
        self._parse_lists(md)
        self.ok = bool(self.recipes)
        print(f"[skills] {len(self.recipes)} burst recipes, "
              f"{len(self.never)} classes that never realise, "
              f"{len(self.weak)} below the bar", flush=True)

    # ------------------------------------------------------------------ parse
    def _parse_main(self, md):
        for r in _rows(md, ["class", "weight", "hit"]):
            c = _cls(r.get("class", ""))
            w = _f(r.get("weight"))
            hit = _f(next((v for k, v in r.items() if "hit" in k.lower()), None))
            if not c or w is None:
                continue
            self.recipes[c] = {"w": w, "form": r.get("prompt form", "").strip(),
                               "hit": hit, "n": _f(r.get("N")) or 1,
                               "source": "§51/52"}

    def _parse_merge(self, md):
        """The §64 addendum: some recipes are superseded, most are not."""
        for r in _rows(md, ["klasse", "steht"]):
            c = _cls(r.get("Klasse", "") or r.get("klasse", ""))
            if not c:
                continue
            steht = (r.get("steht") or "").replace("*", "").strip().lower()
            newcell = next((v for k, v in r.items() if k.startswith("neu:")), "")
            parts = [p.strip() for p in newcell.split("/")]
            w = next((_f(p) for p in parts if _f(p) is not None), None)
            hit = _f(parts[-1]) if parts else None
            if steht.startswith("neu") and w is not None:
                cur = self.recipes.get(c, {})
                self.recipes[c] = {"w": w, "form": cur.get("form", ""),
                                   "hit": hit if hit is not None else cur.get("hit"),
                                   "n": _f(r.get("N")) or cur.get("n", 1),
                                   "source": "§64"}
            elif c not in self.recipes and w is not None:
                self.recipes[c] = {"w": w, "form": "", "hit": hit,
                                   "n": _f(r.get("N")) or 1, "source": "§64"}

    def _parse_lists(self, md):
        m = re.search(r"\*\*Never realised, at any dose:\*\*\s*\n\n?(.+?)\n\n", md, re.S)
        if m:
            self.never = set(re.findall(r"`([a-z0-9_]+)`", m.group(1)))
        m = re.search(r"\*\*Below the bar[^\n]*\*\*\s*\n\n?(.+?)\n\n", md, re.S)
        if m:
            for cls, val in re.findall(r"`([a-z0-9_]+)`\s*\(([0-9.]+)\)", m.group(1)):
                self.weak[cls] = float(val)

    # ------------------------------------------------------------------ use
    def weight_for(self, burst_class, default=None):
        """The measured merge weight for this class, or the flat default."""
        r = self.recipes.get(str(burst_class or "").lower())
        return r["w"] if r else default

    def offerable(self, available):
        """Of the adapters on disk, the ones actually worth offering.

        Ordered by measured hit rate, because the director should reach for the
        reliable sounds first and the tail of the list is where the misses live.
        """
        av = {a.lower() for a in available}
        got = [(c, r) for c, r in self.recipes.items()
               if c in av and c not in self.never
               and (r.get("hit") or 0) >= config.SKILLS_MIN_HIT]
        got.sort(key=lambda kv: -(kv[1].get("hit") or 0))
        return got

    def prompt_block(self, available):
        """What the director is told about bursts, from the measurements."""
        got = self.offerable(available)
        if not got:
            return ""
        strong = [c for c, r in got if (r.get("hit") or 0) >= 0.40]
        rest = [c for c, r in got if (r.get("hit") or 0) < 0.40]
        gone = sorted(self.never | set(self.weak))
        L = ["\n\nVOCAL BURSTS — measured, not guessed. Every sound below has a "
             "trained adapter AND a measured hit rate; naming one in a "
             "round-bracket cue pulls its adapter in at the weight that was "
             "measured best for that class.",
             "",
             "USE THEM CONSTANTLY. Real speech is full of them and a reply "
             "without a breath, a laugh or a sigh sounds read rather than "
             "spoken. One in most replies, two or three when the moment is "
             "emotional.",
             "",
             "MOST RELIABLE — reach for these first (they land 40-75% of the time):",
             "  " + ", ".join(strong)]
        if rest:
            L += ["", "ALSO AVAILABLE, less reliable (15-40%):", "  " + ", ".join(rest)]
        if gone:
            L += ["",
                  "NEVER ASK FOR THESE. They do not exist in this voice: measured "
                  "across every dose and both prompt forms, they produce nothing "
                  "or something else. Asking yields a silent gap, not a sound. "
                  "Every mouth sound and every whistle is in this group:",
                  "  " + ", ".join(gone)]
        L += ["",
              "HOW TO WRITE THEM — each of these was measured on this model:",
              "  * Put the burst BETWEEN sentences, not inside one. Mid-clause "
              "placement is worse on 15 of 15 classes tested (hit rate -0.07 to "
              "-0.12, miss rate +0.31 to +0.37). The single exception is "
              "clears_throat, which is better mid-sentence.",
              "  * Name the CAUSE of the sound in your GENERAL line — what makes "
              "the character breathe in, laugh, sigh. Worth +0.026 hit rate on "
              "its own, and it composes with the next one.",
              "  * A burst that matters gets a longer stated duration. Worth "
              "+0.022, and together with the cause sentence +0.044.",
              "  * Write the sound, never the action that makes it. "
              "\"(chuckle)\" works; \"(he chuckles)\" degrades to silence "
              "(-0.08 to -0.11 hit rate, misses +0.12).",
              "  * Do not substitute a neighbour. Asking for a tired groan to "
              "get a frustrated one is measured as a harm, not a fallback.",
              "  * Never open or close the line on a burst; words must follow."]
        return "\n".join(L)


_CACHE = {}


def load():
    if "s" not in _CACHE:
        try:
            _CACHE["s"] = Skills()
        except Exception as e:
            print(f"[skills] unavailable: {e}", flush=True)
            _CACHE["s"] = None
    return _CACHE["s"]
