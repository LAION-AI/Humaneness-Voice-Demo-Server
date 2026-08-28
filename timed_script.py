"""Turn the director's script into the timed script SFT3 was trained on.

SFT3's format carries its own arithmetic: every speech segment is preceded by
`[N.N seconds duration]`, every gap of 0.2 s or more by `[N.N seconds pause]`,
and every vocal burst is `(label, N.N seconds)`.  The Tokens field is the sum of
all of it at 12.5 frames per second, and when the numbers disagree with the
budget the model has to choose which to honour.

So the numbers are not left to the language model.  It writes the performance —
directions, bursts, where the silences fall — and this module does the
arithmetic, then makes the total match the budget exactly.  Getting a language
model to produce a set of decimals that sums to a given figure is a bad bet, and
length control is the one thing this checkpoint honours best.

Brackets are what tell the three tag kinds apart, and the rule is unforgiving:
square bracket = seconds; round bracket *with* a number = a burst; round bracket
*without* a number = a delivery direction.  A direction that picks up a number
becomes a burst, so directions here never carry one.
"""
import re

import config

# Median burst in the training data is 0.28 s; the 10th and 90th percentiles are
# 0.14 and 0.48.  A burst asked for at 3 s is outside anything the model saw.
BURST_DEFAULT = 0.28
BURST_MIN, BURST_MAX = 0.14, 1.2
PAUSE_DEFAULT = 0.30
PAUSE_MIN = 0.20
LEAD_PAUSE = 0.30
TAIL_PAUSE = 0.30
# Segments over 12 s were split again in training, so nothing longer is emitted.
SEG_MAX = 12.0

# labels that actually occur in the training data
BURST_LABELS = [
    "low mumble", "ahem", "contented sigh", "surprised gasp", "chuckle",
    "breathy giggle", "childlike giggle", "wistful sigh", "exhausted groan",
    "sharp inhale", "resonant hum", "scream", "yawn", "deep breath", "soft hum",
    "exasperated sigh", "cackle", "shriek", "coughing", "mournful wail",
    "growl", "purr",
]
_BURST_RE = re.compile(r"\(([^)]*?),\s*([0-9]*\.?[0-9]+)\s*(?:s|sec|seconds?)\)",
                       re.I)
_PAUSE_RE = re.compile(r"\[\s*(?:([0-9]*\.?[0-9]+)\s*(?:s|sec|seconds?)?\s*)?"
                       r"(?:pause|beat)\s*\]", re.I)
_DUR_RE = re.compile(r"\[\s*[0-9]*\.?[0-9]+\s*(?:s|sec|seconds?)?\s*duration\s*\]", re.I)
_CUE_RE = re.compile(r"\(([^)]*)\)")


def _is_burst_label(txt):
    t = txt.strip().lower().rstrip(".")
    if t in BURST_LABELS:
        return True
    # a short fragment naming a known burst word counts too ("a soft chuckle")
    return len(t.split()) <= 4 and any(b.split()[-1] in t for b in BURST_LABELS)


def _seconds_for(words, speed=1.0):
    """How long this many words should take, in the model's own units."""
    per = config.TIMED_FRAMES_PER_WORD / config.FRAME_RATE   # seconds per word
    return max(0.4, words * per / max(speed, 0.1))


def parse(script):
    """Split the director's script into ordered items.

    Returns a list of ('pause', secs) | ('burst', label, secs) |
    ('direction', text) | ('speech', text).
    """
    s = _DUR_RE.sub(" ", str(script or ""))
    items, pos = [], 0
    marks = []
    for m in _PAUSE_RE.finditer(s):
        marks.append((m.start(), m.end(), ("pause", float(m.group(1) or PAUSE_DEFAULT))))
    for m in _BURST_RE.finditer(s):
        secs = min(max(float(m.group(2)), BURST_MIN), BURST_MAX)
        marks.append((m.start(), m.end(), ("burst", m.group(1).strip(), secs)))
    taken = [(a, b) for a, b, _ in marks]
    for m in _CUE_RE.finditer(s):
        if any(a <= m.start() < b for a, b in taken):
            continue
        body = m.group(1).strip()
        kind = ("burst", body, BURST_DEFAULT) if _is_burst_label(body) \
            else ("direction", body)
        marks.append((m.start(), m.end(), kind))
    marks.sort()
    for a, b, kind in marks:
        chunk = s[pos:a]
        if chunk.strip():
            items.append(("speech", chunk.strip()))
        items.append(kind)
        pos = b
    if s[pos:].strip():
        items.append(("speech", s[pos:].strip()))
    return items


def _split_sentences(text):
    out = [p.strip() for p in re.split(r"(?<=[.!?…])\s+", text) if p.strip()]
    return out or ([text.strip()] if text.strip() else [])


def render(script, speed=1.0, budget_frames=None):
    """Return (tagged_script, frames, plain_text).

    `tagged_script` goes into both SCRIPT: and Text:, byte-identical, and
    `frames` into Tokens: — the sum of every number in the script.
    """
    items = parse(script)
    seq = []          # (kind, payload, seconds)
    pending_dir = None
    for it in items:
        if it[0] == "pause":
            seq.append(("pause", None, max(it[1], PAUSE_MIN)))
        elif it[0] == "burst":
            if pending_dir:
                seq.append(("direction", pending_dir, 0.0))
                pending_dir = None
            seq.append(("burst", it[1], it[2]))
        elif it[0] == "direction":
            pending_dir = it[1]
        else:
            for sent in _split_sentences(it[1]):
                words = len([w for w in sent.split() if w.strip()])
                if not words:
                    continue
                secs = _seconds_for(words, speed)
                if pending_dir:
                    seq.append(("direction", pending_dir, 0.0))
                    pending_dir = None
                # anything past 12 s was split again in training
                while secs > SEG_MAX:
                    seq.append(("speech", sent, SEG_MAX))
                    secs -= SEG_MAX
                    sent = ""
                seq.append(("speech", sent, round(secs, 1)))
    if pending_dir:                       # a direction with nothing after it
        seq.append(("direction", pending_dir, 0.0))
    if not any(k == "speech" for k, _, _ in seq):
        return "", 0, ""

    # a gap before the first word and after the last, as the format expects
    if seq and seq[0][0] != "pause":
        seq.insert(0, ("pause", None, LEAD_PAUSE))
    if seq and seq[-1][0] != "pause":
        seq.append(("pause", None, TAIL_PAUSE))

    total = round(sum(s for _, _, s in seq), 1)
    frames = int(round(total * config.FRAME_RATE))
    if budget_frames:
        # scale the speech to the requested budget, leaving pauses and bursts
        # alone — they are performance, not padding
        fixed = sum(s for k, _, s in seq if k != "speech")
        spoken = total - fixed
        want = budget_frames / config.FRAME_RATE - fixed
        if spoken > 0.1 and want > 0.1:
            f = want / spoken
            seq = [(k, p, round(s * f, 1) if k == "speech" else s) for k, p, s in seq]
            total = round(sum(s for _, _, s in seq), 1)
            frames = int(round(total * config.FRAME_RATE))

    out, plain = [], []
    for kind, payload, secs in seq:
        if kind == "pause":
            out.append(f"[{secs:.1f} seconds pause]")
        elif kind == "burst":
            out.append(f"({payload}, {secs:.1f} seconds)")
        elif kind == "direction":
            out.append(f"({payload})")
        else:
            out.append(f"[{secs:.1f} seconds duration] {payload}")
            plain.append(payload)
    return " ".join(out), frames, " ".join(plain).strip()


def check(tagged, frames):
    """Do the printed numbers add up to the stated budget?"""
    tot = 0.0
    for m in re.finditer(r"\[([0-9]*\.?[0-9]+) seconds (?:duration|pause)\]", tagged):
        tot += float(m.group(1))
    for m in _BURST_RE.finditer(tagged):
        tot += float(m.group(2))
    return round(tot, 2), frames, abs(tot * config.FRAME_RATE - frames) <= 1.0


def general_line(general, seconds, lang_code, reads_as=None):
    """Fold GENERAL into the one-line shape the format's own example uses.

    The guide's GENERAL is a single compact line that ends with the emotions and
    then the clip's length and language — "…; reads as bitterness, contempt;
    9.5s, EN."  Ours had grown into several standing sentences about register,
    continuity and recording quality, which is prose the model has to wade
    through before it reaches the part that changes between turns.
    """
    g = " ".join(str(general or "").split())
    # The standing sentences this demo had accumulated — register, continuity,
    # genuineness, room — are four clauses of prose that never change between
    # turns.  The format's own example is one line, so they are compressed to
    # the short equivalents rather than carried in full.
    keep_short = []
    for sent in re.split(r"(?<=[.;])\s+", g):
        low = sent.lower()
        if "the way someone actually talks" in low or "close conversational volume" in low:
            keep_short.append("close conversational volume, unforced")
        elif "the same speaker continues" in low:
            keep_short.append("same speaker throughout")
        elif "genuine and spontaneous" in low:
            keep_short.append("genuine, not acted")
        elif "studio recording" in low:
            keep_short.append("clean studio recording")
        elif sent.strip(" .;"):
            keep_short.append(sent.strip(" .;"))
    seen, g2 = set(), []
    for k in keep_short:
        if k.lower() not in seen:
            seen.add(k.lower())
            g2.append(k)
    g = "; ".join(g2).rstrip(" .;")
    if reads_as and "reads as" not in g.lower():
        names = reads_as if isinstance(reads_as, str) else ", ".join(reads_as)
        names = names.replace("_", " ").lower()
        g += f"; reads as {names}"
    return f"{g}; {seconds:.1f}s, {lang_code}."
