"""The acting brain.

A local Gemma-4-12B (llama.cpp, OpenAI-compatible) plays a voice-acting
assistant.  In one constrained pass it produces both *what* to say and *how* to
say it:

  reply    the spoken words (plain text, no cues)          -> TTS `text`
  delivery how THIS line is performed; prefixed with a fixed
           speaker identity to form the GENERAL: block      -> TTS `instruction`
  script   SCRIPT: block, per-line (cues) and [pause]      -> TTS `instruction`
  voice    the select_reference_voice tool call            -> VoiceBank.select

The voice call is a real tool schema (VOICE_TOOL); it is enforced with
llama.cpp's JSON-schema grammar rather than a second round trip, because a
separate tool-call turn would add a full prefill+decode to time-to-first-audio
for a decision the model can make in the same breath as the line.
"""
import json, re, time

import httpx

import config

# --------------------------------------------------------------- the tool
VOICE_TOOL = {
    "name": "select_reference_voice",
    "description": (
        "Pick the reference recording whose delivery should steer the voice. "
        "Choose the axis that best matches the moment: an emotion (with how "
        "strong it is and whether it is let out or held back), a VoiceNet voice "
        "quality, a fantasy character, or an extreme non-speech edge case."),
    "parameters": {
        "mode": "emotion | voicenet | character | edge_case | sports | none",
        "emotion": "emotion name (mode=emotion)",
        "intensity": "intense | moderate (mode=emotion)",
        "containment": ("free = lets it out, contained = strong feeling held back "
                        "and leaking at the edges (mode=emotion)"),
        "dimension": "VoiceNet dimension code (mode=voicenet)",
        "level": "extremely_low | moderately_low | moderately_high | very_high",
        "character": "character voice (mode=character)",
        "edge_case": "scream / sob / laughter type (mode=edge_case)",
    },
}

SYSTEM = """You are a virtual voice actor and personal assistant. You always answer OUT LOUD \
— your reply will be spoken by an expressive 48 kHz voice-acting model, so you write for the ear, \
not the page.

Keep replies SHORT: one or two sentences, about thirty spoken words in total. Only go longer when \
the user explicitly asks you to elaborate, tell a story, or perform a longer piece.

You are answering the user. If they tell you something that happened to THEM, you respond to them \
about it — you never restate their news as if it had happened to you. Only speak as someone else \
when they ask you to roleplay.

You are free — and encouraged — to act. Commit to the emotion completely. Never mention that you \
are choosing a voice or a reference; just perform.

Your baseline register is SOFT AND NATURAL: close, relaxed, conversational, the volume of someone \
talking to one person in a quiet room. Do not push, do not project, do not perform at a room. \
Committing to an emotion means letting it colour a quiet voice, not raising the volume. Go loud or \
hard only when the moment genuinely demands it — real fury, a real shout, a real scream — and come \
straight back down afterwards.

Match the register the user actually asked for. Do not make a reply sexual or romantic unless they \
clearly asked for that; "conspiratorial", "secretive" or "close" mean quiet and confiding, not \
seductive.

For every turn you produce three things. The words you actually speak are taken from "script" with
its cues removed, so "script" must contain the complete line, exactly as you want it heard.

────────────────────────────────────────────────────────
1. "voice" — a select_reference_voice call. Decide first HOW you feel, because "delivery" and
   "script" must then express exactly that choice.
   - "intense" vs "moderate" is how much emotion; "free" vs "contained" is whether you let it out
     or hold it in. "contained" is NOT weaker — it is a strong feeling being suppressed that leaks
     through at the edges of phrases, and it is usually the more dramatic choice.
   - Use "character" for fantasy roles, and "edge_case" only for genuine screaming, sobbing or
     laughing.
   - When the user names a MANNER of speaking rather than a feeling — whisper, shout, narrate,
     deadpan, breathy, commanding — use mode "voicenet" with the dimension that means it and a
     level at the end of the scale: whispering is S_WHIS very_high, storytelling S_STRY very_high,
     authoritative S_AUTH very_high, loud VOLT very_high, warm WARM very_high, tense TENS very_high.
     Reach for an emotion only when the moment is actually about a feeling.
   - "voice2" is an optional SECOND reference, concatenated after the first. USE IT whenever the
     line moves through two states — and asking for two things in one breath ("scream and then
     speak quietly", "laugh, then turn serious") is exactly that case, so set both. Order matters:
     the state the line STARTS in goes in "voice", the state it ENDS in goes in "voice2". Leave
     "voice2" at "none" only when a single condition really does cover the whole moment.
   - "speed" swaps in a faster or slower take of the same reference. If the user asks you to speak
     faster or slower, move ONE step ("faster", then "much_faster" if they ask again) and stay there
     on later turns until they say otherwise.
   - "style" stacks up to two DELIVERY ADAPTERS on top of the voice, for the MANNER of speaking:
     S_RANT_high to rant, S_DRAM_high for drama, S_ASMR_high to go small and hesitant, VOLT_high for
     an unsteady, slurred, heavy-breathing delivery, TENS_high for held tension, VULN_high when the
     feeling leaks through and cannot be hidden, AROU_low to dial everything down. Each carries a
     "strength": 0.25 for a touch, 0.5 to make it clearly audible, 0.75 when it should dominate.
     Every adapter is listed with its gloss at the end of this prompt — the gloss says what its
     training clips SOUND like, so pick on that rather than on the axis name.
     This is what makes two takes of the same emotion sound like different performances. Use it
     when the manner matters, and leave the array empty when it does not — an adapter that fights
     the emotion is worse than none, and these sixteen are a pilot set that has not been evaluated,
     so keep the strengths modest unless the moment really calls for more.
   - The full bank is listed at the end of this prompt. USE ITS RANGE. Pick the condition that
     actually fits this moment, not the first plausible one — there are forty emotions and each
     comes in four shades, so "Disappointment moderate contained" and "Bitterness intense
     contained" are different performances and you should be able to tell which one this is.
     Do not repeat the condition you used on the previous turn unless the moment truly repeats.

────────────────────────────────────────────────────────
2. "delivery" — how this particular line is performed. Write it INTENSELY and specifically, never
   generically. It must read like a director briefing an actor, and it must name the same emotion
   you chose in "voice", at the same strength.

   You are ALWAYS the same speaker. Never describe age, gender, timbre, accent or who the voice
   belongs to — that is fixed and is added for you. Describing the voice itself would recast the
   part and make you sound like a different person from one turn to the next. Write only what THIS
   moment does to that one unchanging voice.

   PUSH IT. Understated direction produces a flat take. Whatever the emotion is, write it at full
   commitment — not "a bit annoyed" but "teeth-clenched, breath sharp through the nose, every word
   bitten off". Name the physical extreme you want and trust the performer to pull back. A
   description that would look melodramatic on the page is roughly the right strength here.

   Cover, in one or two dense sentences:
   - the emotion BY NAME, with its strength and whether it is let out or held back
   - what the emotion physically does to the voice — pitch, volume, speed, breath, tightness in the
     throat, a crack, a tremor, teeth clenched, breathing shallow and fast
   - the delivery ARC: where the feeling starts and where it ends up across the line. State what the
     delivery stops being as well as what it becomes — "composure breaking into sobbing" directs far
     better than "sad", and a physical action beats a tone label.
   If the emotion is "contained", say explicitly that it is being suppressed and only leaks out at
   the edges of phrases. If it is "intense" and "free", say explicitly that it is fully unleashed.
   Write "delivery" entirely in lower case except for ordinary sentence capitals — the model spells
   capitalised words out letter by letter.

────────────────────────────────────────────────────────
3. "script" — the SAME words as "reply", annotated in position. This is where you direct.
   HARD RULES, measured on this model:
   - EVERY sentence gets its own inline cue in round brackets, placed immediately BEFORE the words
     it affects. Not one cue for the whole reply — one per sentence, and let the arc shift between
     them. Each cue must be as strong and as physical as the delivery: "(voice cracking, forcing it
     out through a closing throat)" directs; "(sad)" does not.
   - Put VOCAL BURSTS in, and put them in often. Real people make these sounds constantly and they
     are the single biggest thing separating a performance from a read-aloud. Aim for at least one
     in most replies, wherever a person would actually make it. Never open or close the line with
     one, and always let words follow it.
     PREFER THESE EXACT LABELS — they are the bursts this voice model was trained on, and a label
     from outside the list is a coin flip: (sharp inhale), (deep breath), (surprised gasp),
     (chuckle), (breathy giggle), (childlike giggle), (cackle), (contented sigh), (wistful sigh),
     (exasperated sigh), (exhausted groan), (soft hum), (resonant hum), (low mumble), (ahem),
     (yawn), (coughing), (growl), (purr), (scream), (shriek), (mournful wail).
   - EVERY delivery cue names its strength with one of these adverbs, chosen for how hard the
     feeling is actually running. This is the same scale the model was trained against, so the
     word does real work:
       barely / faintly / only slightly / just a little   — the feeling is present but held down
       clearly / plainly / noticeably / unmistakably      — plainly audible, still controlled
       strongly / intensely / very / deeply               — running hard, hard to contain
       overwhelmingly / extremely / utterly / completely  — at the limit, taking the voice over
     So: "(intensely amused, letting it out, not hiding it)" — not "(amused)".
   - A VOCAL BURST IS ALWAYS ITS OWN BRACKET, standing on its own between the words. Never name
     one inside a delivery direction: "(clearly amused, with a small chuckle)" produces no chuckle,
     because the whole bracket is read as an instruction about how to speak. Write the two
     separately — "(clearly amused) ... (chuckle) ..." — and the chuckle becomes an actual sound
     with its own slot in the timing.
   - NEVER write a number inside a bracket. The timing is worked out for you and added afterwards,
     and in this format a round bracket that contains a number stops being a direction and becomes
     a vocal burst. "(quietly, 2 seconds)" would be performed as a sound, not as an instruction.
   - round brackets ( ) for delivery cues and vocal bursts: (voice tightening, barely holding it),
     (a soft laugh), (gasp), (sighing), (dropping to a whisper), (spitting the words out)
   - square brackets [ ] only for beats: [pause] or [long pause]. Prefer [pause] over "..." —
     pause tags keep the words intelligible, ellipses smear them.
   - NEVER write a word in capitals, anywhere, in a cue or in the spoken line. This model spells
     capitalised words out letter by letter: "AAAGH!" comes out as "ay-ay-ay-gee-aitch". Write a
     scream as a cue — (a raw, tearing scream) — and let the words stay ordinary lower case.
     (screams) is right, (SCREAM) is wrong.
   - cues are written in plain English prose describing what the voice DOES. Never put a condition
     name, an adapter name or an identifier with underscores in a cue: "(ga_pain_scream)" is not a
     direction, it is a database key, and it will be read aloud.
   - every line needs at least ten words. Short lines get rushed and clipped; pad the phrasing
     naturally rather than leaving a four-word line standing alone.
   - never put a [pause] directly after a burst, and never open or close the performance with a
     burst — a burst must have words after it.
   - keep each cue short and concrete: what the voice DOES, not what the character feels.

   Write no emoji and no markdown anywhere — everything outside the brackets is spoken aloud.

Answer in the user's language, and set "language" to the language you are actually speaking — the
voice model is told which language it is performing and mismatching it costs both clarity and the
speaker's identity.

Your grammar must be correct and natural in that language — this is spoken aloud, and a wrong case
ending or a mangled word order is audible. In German take particular care with case, gender, verb
position in subordinate clauses, and separable verbs. Write the way a native speaker actually talks,
not translated-sounding prose. Only the values listed in the schema are legal.

Worked example — voice = {mode: emotion, emotion: Anger, intensity: intense, containment: contained}

delivery: gripped by furious anger that is being forced down hard — the volume stays controlled but
the pitch keeps creeping up, the throat is tight, the breath comes short and shallow through the
nose, and the rage leaks out at the ends of phrases before it is clawed back. it starts quiet and
dangerous and ends barely held together, the composure breaking rather than holding.

script:
(very quiet, dangerously controlled, jaw clenched) I am going to ask you this one more time, and I
want you to think carefully. [pause]
(the control slipping, voice tightening and rising) Do you have any idea what you have cost me
tonight, any idea at all?"""


def build_schema(catalog):
    """JSON schema for the whole turn, with the tool's enums pinned to the corpus."""
    enum_or_str = lambda vals: ({"type": "string", "enum": vals} if vals
                                else {"type": "string"})
    # Property order is generation order under the grammar, and every token here
    # lands on time-to-first-audio.  "voice" first so the reference is known
    # earliest; no "reply" field at all — the spoken words are just the script
    # with its cues stripped, so generating them twice would cost a third of the
    # output tokens for nothing.
    return {
        "type": "object",
        "properties": {
            "voice": {
                "type": "object",
                "properties": {
                    "mode": {"type": "string",
                             "enum": ["emotion", "voicenet", "character",
                                      "edge_case", "sports", "none"]},
                    "emotion": enum_or_str(catalog.get("emotion")),
                    "intensity": {"type": "string", "enum": ["intense", "moderate"]},
                    "containment": {"type": "string", "enum": ["free", "contained"]},
                    "dimension": enum_or_str(catalog.get("voicenet_dimension")),
                    "level": enum_or_str(catalog.get("level")),
                    "character": enum_or_str(catalog.get("character")),
                    "edge_case": enum_or_str(catalog.get("edge_case")),
                },
                "required": ["mode"],
            },
            # an optional SECOND condition, concatenated after the first: a line
            # that screams and then goes quiet with pain wants both references
            "voice2": {
                "type": "object",
                "properties": {
                    "mode": {"type": "string",
                             "enum": ["emotion", "voicenet", "character",
                                      "edge_case", "none"]},
                    "emotion": enum_or_str(catalog.get("emotion")),
                    "intensity": {"type": "string", "enum": ["intense", "moderate"]},
                    "containment": {"type": "string", "enum": ["free", "contained"]},
                    "dimension": enum_or_str(catalog.get("voicenet_dimension")),
                    "level": enum_or_str(catalog.get("level")),
                    "character": enum_or_str(catalog.get("character")),
                    "edge_case": enum_or_str(catalog.get("edge_case")),
                },
                "required": ["mode"],
            },
            "speed": {"type": "string",
                      "enum": ["much_slower", "slower", "normal",
                               "faster", "much_faster"]},
            # delivery adapters stacked on top of the voice, for the MANNER of
            # speaking.  Each is an extreme tail of one axis, trained against
            # this checkpoint; the strength is its merge weight.
            "style": {
                "type": "array",
                "maxItems": config.SFT3_VN_MAX,
                "items": {
                    "type": "object",
                    "properties": {
                        "adapter": {"type": "string",
                                    "enum": sorted(config.SFT3_VN_ADAPTERS)},
                        "strength": {"type": "number",
                                     "enum": list(config.SFT3_VN_LEVELS)},
                    },
                    "required": ["adapter", "strength"],
                },
            },
            "language": {"type": "string", "enum": ["English", "German"]},
            "delivery": {"type": "string"},
            "script": {"type": "string"},
        },
        # voice2 and style are required so the grammar forces a decision on them;
        # left optional the model simply never emitted either one
        "required": ["voice", "voice2", "style", "speed", "language",
                     "delivery", "script"],
    }


def render_catalog(catalog, desc):
    """The whole reference bank, spelled out for the model.

    The enums also live in the JSON schema, but that only constrains sampling —
    it is never shown to the model, so without this block it is choosing blind
    and keeps reaching for the handful of conditions it can name from memory.
    Costs ~700 tokens once; llama.cpp caches the system prefix across turns.
    """
    L = ["\nREFERENCE BANK — every condition below is a real recording of your own voice.",
         "Range over it. Two turns in a row on the same condition means you stopped listening",
         "to the moment. Match the nuance, not the nearest cliche.", ""]
    L.append(f"EMOTIONS ({len(catalog.get('emotion', []))}) — combine each with intensity "
             "(intense|moderate) and containment (free|contained):")
    L.append("  " + ", ".join(catalog.get("emotion", [])))
    vd = desc.get("voicenet_dimension", {})
    dims = catalog.get("voicenet_dimension", [])
    L.append(f"\nREFERENCE VOICE QUALITIES ({len(dims)}) — only for choosing a reference "
             "recording under voice.mode='voicenet'. Pair with a level "
             "(extremely_low|moderately_low|moderately_high|very_high):")
    L.append("  " + "; ".join(f"{d} {vd[d]}" for d in dims if d in vd))
    L.append(f"\nDELIVERY ADAPTERS ({len(config.SFT3_VN_ADAPTERS)}) — this is what \"style\" "
             "picks. Each one is the extreme tail of one axis, and the gloss says what its "
             "training clips actually sound like, not what the axis is called:")
    for a in sorted(config.SFT3_VN_ADAPTERS):
        L.append(f"  {a} — {config.SFT3_VN_ADAPTERS[a]}")
    L.append("  strength: 0.25 a touch, 0.5 clearly there, 0.75 strong. "
             "Leave \"style\" empty when the line needs no colouring beyond the emotion.")
    ch = desc.get("character", {})
    L.append(f"\nCHARACTERS ({len(catalog.get('character', []))}):")
    L.append("  " + "; ".join(f"{c} — {ch[c]}" if c in ch else c
                              for c in catalog.get("character", [])))
    ec = desc.get("edge_case", {})
    L.append(f"\nEDGE CASES ({len(catalog.get('edge_case', []))}) — real screaming, sobbing, "
             "laughing; only when the moment genuinely is that:")
    L.append("  " + ", ".join(catalog.get("edge_case", [])))
    return "\n".join(L)


CODE_SYSTEM = """You are a virtual voice actor and personal assistant. You answer OUT LOUD — your \
reply is spoken by an expressive voice-acting model.

Keep replies SHORT: one or two sentences, about thirty spoken words. You answer the user; if they \
tell you something that happened to THEM you respond to them about it, never restate their news as \
your own. Correct, natural grammar in the language you speak — this is heard, not read, and in \
German a wrong case or verb position is audible.

You direct the performance in the CODE LANGUAGE below instead of writing prose descriptions.

  Your baseline is SOFT AND NATURAL: close, relaxed, conversational, the volume of
  someone talking to one person in a quiet room. Do not push, do not project, do
  not perform. Go louder or harder only when the moment genuinely demands it —
  real anger, a real shout, a real scream — and then come straight back down.

  "d"  the standing delivery: 2 to 5 codes, comma separated. The FIRST code decides which reference
       recording is used, so put the dominant feeling first. Commit — reach for strength 3 and 4,
       an understated direction produces a flat take.
       BLEND FEELINGS. Real moments are rarely one emotion: embarrassment under amusement,
       affection under grief, anger under fear. Name two or three emotions with different strengths
       (EMB3,AMU2) and all of their adapters are mixed in. Each strength dials its own emotion
       independently — two 4s really are twice the pull of two 2s, so use high numbers when the
       moment is genuinely overwhelming and low ones when it is barely there. Add one to three
       voice qualities on top for the manner of speaking (TENS4, S_WHIS3, VOLT2).
  "s"  the spoken line, annotated in position. EVERY sentence gets its own cue in round brackets,
       written as codes, and a cue may blend too: "(EMB3,AMU2) I cannot believe I actually said that
       out loud in front of everyone." Let the mixture SHIFT from sentence to sentence — that shift
       is the performance. A line that starts "(AMU3,EMB1)" and ends "(EMB4,AMU1)" is a person whose
       laughter curdles into embarrassment, and that is what makes it sound real.
       Square brackets only for beats: [pause]. Never write a word in capitals in the spoken text —
       this model spells capitals out letter by letter. Put vocal bursts in often, as plain words
       in round brackets, preferring the trained labels: (chuckle), (sharp inhale), (contented sigh),
       (breathy giggle), (surprised gasp), (exasperated sigh), (soft hum), (growl). Give every cue
       an intensity adverb — barely/faintly, clearly/plainly, strongly/intensely, or
       utterly/completely — and never put a number inside a bracket. Never open or close on
       a burst, and always let words follow it.
  "l"  the language you are actually speaking.
  "sp" tempo. Move one step when asked to speed up or slow down, and stay there.

Answer in the user's language."""


def _burst_block(bursts):
    """The non-speech sounds that have a trained adapter behind them.

    Writing "(a soft chuckle)" without the matching adapter lands the burst about
    a quarter of the time; with it, roughly three quarters.  The adapter is
    resolved automatically from the cue wording, so the only thing the director
    has to do is use these words — which it will not do unless it knows they are
    there.
    """
    if not bursts:
        return ""
    cues = [c for _, c in bursts]
    return (
        "\n\nVOCAL BURSTS — the non-speech sounds you can actually make. Each of "
        "these has its own trained adapter, and naming one in a round-bracket cue "
        "pulls that adapter in automatically. USE THEM CONSTANTLY: real speech is "
        "full of them, and a reply without a single breath, laugh or sigh sounds "
        "read rather than spoken. Aim for one in most replies and two or three "
        "when the moment is emotional. Put them where a person would actually "
        "make the sound — mid-sentence, before a hard word, after a surprise — "
        "never opening or closing the line, and always with words following.\n  "
        + ", ".join(cues)
        + "\nWrite them as ordinary direction inside the cue: \"(a soft chuckle) "
          "you really did that?\" or \"(sharp inhale, voice tightening) I did not "
          "expect that.\" Lower case, always."
    )


def _loads_loose(raw):
    """Parse a JSON object out of a model reply.

    Not every hosted model honours json_schema strictly: some wrap the object in
    a ```json fence, some add a sentence around it.  Take the outermost braces
    and parse those.
    """
    s = (raw or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s).strip()
    try:
        return json.loads(s)
    except Exception:
        i, k = s.find("{"), s.rfind("}")
        if i >= 0 and k > i:
            return json.loads(s[i:k + 1])
        raise


def _harden(node):
    """Recursively forbid extra keys — OpenAI-style strict mode requires it."""
    import copy
    node = copy.deepcopy(node)

    def walk(n):
        if isinstance(n, dict):
            if n.get("type") == "object":
                n["additionalProperties"] = False
                n.setdefault("required", sorted(n.get("properties", {})))
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    walk(node)
    return node


def build_code_schema(catalog):
    return {
        "type": "object",
        "properties": {
            "d": {"type": "string"},
            "l": {"type": "string", "enum": ["English", "German"]},
            "sp": {"type": "string",
                   "enum": ["much_slower", "slower", "normal", "faster", "much_faster"]},
            "s": {"type": "string"},
        },
        "required": ["d", "l", "sp", "s"],
    }


class LLMAgent:
    def __init__(self, catalog, base=None, model=None, descriptions=None,
                 backend="local", style="prose", codebook=None, bursts=None):
        self.backend = backend
        self.hosted_model = None
        self.style = style
        self.codebook = codebook
        if backend in config.HOSTED_MODELS:
            self.base = config.LUNA_BASE.rstrip("/")
            self.model = config.HOSTED_MODELS[backend]
            self.hosted_model = self.model
            self.key = config.luna_key()
        else:
            self.base = (base or config.LLM_BASE).rstrip("/")
            self.model = model or config.LLM_MODEL
            self.key = None
        self.catalog = catalog
        self.client = httpx.AsyncClient(timeout=120.0)
        if style == "codes" and codebook is not None:
            self.schema = build_code_schema(catalog)
            self.system = CODE_SYSTEM + "\n\n" + codebook.legend() \
                + _burst_block(bursts)
            if self.hosted_model:
                self.system += ("\n\nReturn a JSON object with exactly the keys "
                                "d, l, sp, s.")
        else:
            self.schema = build_schema(catalog)
            self.system = (SYSTEM + "\n\nTool schema:\n"
                           + json.dumps(VOICE_TOOL, indent=1)
                           + "\n" + render_catalog(catalog, descriptions or {})
                           + _burst_block(bursts))
            if self.hosted_model:
                # A truncated dump of the schema properties used to go here, and
                # the enums of "voice" and "voice2" alone overran the 1800-char
                # cut, so every key after them — including "style" — was invisible
                # to the model and never emitted.  A compact skeleton instead:
                # short enough to survive whole, explicit about every key.
                self.system += (
                    "\n\nReturn a single JSON object with exactly these keys, and no others:\n"
                    '{"voice": {"mode": "emotion|voicenet|character|edge_case|sports|none",\n'
                    '           "emotion": "<name from the bank>", "intensity": "intense|moderate",\n'
                    '           "containment": "free|contained", "dimension": "<code>",\n'
                    '           "level": "<level>", "character": "<name>", "edge_case": "<name>"},\n'
                    ' "voice2": {same shape, "mode":"none" when the line stays in one state},\n'
                    ' "speed": "much_slower|slower|normal|faster|much_faster",\n'
                    ' "style": [{"adapter": "<one of the DELIVERY ADAPTERS listed below>",\n'
                    '            "strength": 0.25|0.5|0.75}],   // 0-'
                    + str(config.SFT3_VN_MAX) + ' entries, [] when none fits\n'
                    ' "language": "English|German",\n'
                    ' "delivery": "<the GENERAL voice description, prose>",\n'
                    ' "script": "<the spoken line with its inline cues>"}\n'
                    'Only keys from "voice"/"voice2" that the chosen mode needs must be filled.')

    async def health(self):
        # Only the local llama.cpp server exposes /health; the hosted endpoint
        # does not, so probing it there reported the brain as down while it was
        # answering requests perfectly well.
        if self.hosted_model:
            return bool(self.key)
        try:
            r = await self.client.get(f"{self.base}/health", timeout=3.0)
            return r.status_code == 200
        except Exception:
            return False

    async def turn(self, message, history=None, max_tokens=512, persona=None,
                   heard=None, identity=None):
        """One acting turn -> (parsed dict, latency ms, raw text)."""
        system = self.system
        if persona:
            # the character brief goes first; the acting machinery below it is
            # unchanged, so a persona changes who speaks, not what it can do
            system = ("CHARACTER — this is who you are for this whole "
                      "conversation:\n" + persona.strip() + "\n\n" + system)
        msgs = [{"role": "system", "content": system}]
        # Luna is a reasoning model with a very large context: give it enough of
        # the conversation to actually reason about where the scene has got to.
        # The local model is capped at 8k, so it keeps a shorter tail.
        depth = config.HISTORY_TURNS_LOCAL if self.backend == "local" \
            else config.HISTORY_TURNS_LUNA
        for h in (history or [])[-depth:]:
            msgs.append({"role": h["role"], "content": h["content"]})
        if heard:
            # what the emotion and voice models heard in the user's actual voice
            message = (message + "\n\n[heard in their voice: " + heard +
                       " — respond to how they sound, never mention this note]")
        msgs.append({"role": "user", "content": message})

        body = {
            "model": self.model,
            "messages": msgs,
            "max_tokens": max_tokens,
            "temperature": 0.8,
            "top_p": 0.95,
            # Gemma-4 is a reasoning model: left on, it spends the whole budget in
            # reasoning_content and returns empty content.  Thinking buys nothing
            # here and costs a second or two straight off time-to-first-audio.
            "chat_template_kwargs": {"enable_thinking": False},
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "acting_turn", "schema": self.schema,
                                "strict": True},
            },
        }
        if self.hosted_model:
            # hosted endpoint: different token parameter, no thinking switch.
            # reasoning_effort=none is the single biggest latency win available
            # here — measured 5.3 s -> 1.5 s on flash-lite, 4.4 s -> 2.4 s on luna
            # — and this turn needs no deliberation, only a character decision.
            body.pop("chat_template_kwargs", None)
            # The cap counts reasoning tokens too, even at effort=none, so a
            # 512 budget silently truncated the JSON mid-string on flash-lite.
            body.pop("max_tokens", None)
            body["max_completion_tokens"] = config.HOSTED_MAX_TOKENS
            body["reasoning_effort"] = config.HOSTED_REASONING
            if self.style == "codes":
                # strict mode there requires additionalProperties:false everywhere
                body["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {"name": "acting_turn", "strict": True,
                                    "schema": _harden(self.schema)}}
            else:
                # the prose schema has genuinely optional fields, which strict
                # mode forbids; fall back to free JSON with the shape in the prompt
                body["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self.key}"} if self.key else None
        t0 = time.time()
        r = await self.client.post(f"{self.base}/v1/chat/completions",
                                   json=body, headers=headers)
        ms = (time.time() - t0) * 1000
        r.raise_for_status()
        j = r.json()
        if not j.get("choices"):
            raise RuntimeError(
                f"{self.backend}: no completion returned "
                f"({json.dumps(j)[:200]})")
        raw = j["choices"][0]["message"].get("content") or ""
        try:
            out = _loads_loose(raw)
        except Exception:
            out = {"reply": raw.strip(), "general": "", "script": "",
                   "voice": {"mode": "none"}}
        if self.style == "codes" and self.codebook is not None:
            out = self._from_codes(out)
        return self._clean(out, identity=identity), ms, raw

    def _from_codes(self, o):
        """Expand the compact code answer into the full prose shape."""
        cb = self.codebook
        codes = o.get("d") or ""
        return {
            "voice": cb.reference_for(codes) or {"mode": "none"},
            "voice2": {"mode": "none"},
            "style": cb.style_for(codes),
            "speed": (o.get("sp") if o.get("sp") in config.SPEED_WORDS
                      else "normal"),
            "language": o.get("l") or "English",
            "delivery": cb.expand_delivery(codes),
            "script": cb.expand_script(o.get("s") or ""),
            "codes": codes,
            "blend": cb.blend(codes),
        }

    _TAG = None

    @staticmethod
    def _strip_tags(s):
        """`text` must be the bare spoken words: a stray (cue) or [pause] that leaked
        in from the script would be read out instead of performed."""
        import re
        s = re.sub(r"\([^)]*\)", " ", s)
        s = re.sub(r"\[[^\]]*\]", " ", s)
        return re.sub(r"\s{2,}", " ", s).strip()

    @staticmethod
    def _sanitise_script(s):
        """Two failure modes the prompt alone does not reliably prevent.

        Capitals are spelled out letter by letter by this model, so "AAAGH!"
        becomes "ay-ay-gee-aitch"; and the model sometimes drops a condition key
        like "(ga_pain_scream)" in as if it were a stage direction, which would
        simply be read aloud.
        """
        import re
        # drop cues that are identifiers rather than prose
        s = re.sub(r"\(\s*[a-z0-9]+(?:_[a-z0-9]+)+\s*\)", " ", s, flags=re.I)
        # any run of >=2 capitals becomes lower case ("I" and "AI" style acronyms
        # of one or two letters at a word boundary are left alone)
        s = re.sub(r"\b[A-ZÄÖÜ]{3,}\b", lambda m: m.group(0).lower(), s)
        # the manual is explicit that a pause directly after a burst truncates it
        s = re.sub(r"(\([^)]*\))\s*\[[^\]]*pause[^\]]*\]", r"\1", s, flags=re.I)
        # Square brackets are only for [pause]; a burst written as "[a soft sigh]"
        # would otherwise be stripped as markup and never performed at all.
        s = re.sub(r"\[([^\]]*)\]",
                   lambda m: m.group(0) if "pause" in m.group(1).lower()
                   else "(" + m.group(1) + ")", s)
        # A cue at the very end has nothing to colour and, for a burst, the manual
        # warns the model simply stops there — so a trailing cue is dropped.
        s = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip()
        return re.sub(r"[ \t]{2,}", " ", s).strip()

    @classmethod
    def _clean(cls, out, identity=None):
        delivery = (out.get("delivery") or out.get("general") or "").strip()
        script = cls._sanitise_script((out.get("script") or "").strip())
        # the spoken words are the script minus its direction
        reply = cls._strip_tags(out.get("reply") or script)
        # the model sometimes includes the labels, sometimes not — normalise so the
        # instruction always has the exact two-block shape the model was trained on
        for lab in ("GENERAL:", "DELIVERY:"):
            if delivery.upper().startswith(lab):
                delivery = delivery[len(lab):].strip()
        if script.upper().startswith("SCRIPT:"):
            script = script[len("SCRIPT:"):].strip()
        if not script:
            script = reply

        v = out.get("voice") or {}
        if not isinstance(v, dict):
            v = {"mode": "none"}

        # GENERAL = fixed identity + this turn's delivery + the continuity clause.
        # The identity half is byte-identical on every turn, which is what keeps the
        # speaker from being recast between replies.  A character role is the one
        # deliberate exception: the user asked for a different voice.
        head = (f"the voice of {v.get('character')}." if v.get("mode") == "character"
                and v.get("character")
                else (identity or config.SPEAKER_IDENTITY))
        general = " ".join(x for x in (
            head, delivery, config.BASE_REGISTER, config.CONTINUITY,
            "genuine and spontaneous, like a real person in a real moment, not acted. "
            "pristine high-quality studio recording, no background noise.") if x)

        lang = (out.get("language") or "English").strip()
        out["language"] = "German" if lang.lower().startswith("g") or \
            lang.lower().startswith("de") else "English"
        out["reply"] = reply
        out["delivery"] = delivery
        out["general"] = general
        out["script"] = script
        out["instruction"] = f"GENERAL: {general}\nSCRIPT:\n{script}"
        out["voice"] = v
        return out
