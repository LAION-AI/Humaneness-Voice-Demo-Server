"""MOSS voice-acting web demo — FastAPI orchestrator.

One turn:
  user text -> Gemma (GPU LLM_GPU) picks the line + the GENERAL/SCRIPT direction
            -> select_reference_voice resolves to pre-tokenised codes in RAM
            -> MOSS 4.55B (GPU TTS_GPU) streams 48 kHz PCM as it is generated
            -> browser plays the first chunk while the rest is still decoding

Wire format (so the browser can start playing before the reply is finished):
    [1 byte tag][4 byte big-endian length][payload]
    tag 0 = UTF-8 JSON event, tag 1 = raw PCM int16 LE mono @ 48 kHz
"""
import asyncio, json, os, struct, threading, time

import numpy as np
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

import config
import lora_bank
from llm_agent import VOICE_TOOL, LLMAgent
from lora_bank import LoraBank
from tts_engine import TTSEngine
from voice_bank import VoiceBank
import personas
import retrieval
import voice_profiles
from voice_codes import CodeBook

HERE = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="MOSS Voice Acting")
STATE = {"tts": None, "bank": None, "agent": None, "lora": None, "asr": None,
         "agents": {}, "codebook": None, "vc": None, "sim": None,
         "score": None, "profiles": {}, "error": None}


def _frame(tag: int, payload: bytes) -> bytes:
    return struct.pack(">BI", tag, len(payload)) + payload


def _ev(obj) -> bytes:
    return _frame(0, json.dumps(obj).encode())


def _pcm(seg: np.ndarray) -> bytes:
    return _frame(1, np.clip(seg * 32767, -32768, 32767).astype("<i2").tobytes())


# Voice context per conversation.  The manual is explicit that chaining whole
# previous clips is harmful — measured similarity collapsed 0.777 -> 0.280 by the
# fourth clip, because drift compounds and a long prefix drags the previous
# emotion into the new line.  What works is the anchor plus a short tail, so this
# keeps only the last few seconds of each of the last few replies.
SESSIONS = {}


def _session(sid):
    if not sid:
        return None
    s = SESSIONS.get(sid)
    if s is None:
        if len(SESSIONS) > config.MAX_SESSIONS:      # crude cap, oldest first
            for k in list(SESSIONS)[:len(SESSIONS) // 2]:
                SESSIONS.pop(k, None)
        s = SESSIONS[sid] = {"tails": []}
    return s


def _handoff(q, loop, item, gone, timeout=60.0):
    """Hand one item to the streaming consumer, giving up if it has gone away.

    Without the timeout a dropped client leaves this thread parked on a queue
    forever while it still holds the generation lock, and every later request
    queues behind it.
    """
    try:
        asyncio.run_coroutine_threadsafe(q.put(item), loop).result(timeout=timeout)
        return True
    except Exception:
        gone.set()
        return False


# ------------------------------------------------------------------ startup
def _boot():
    try:
        tts = TTSEngine(device="cuda:0")     # CUDA_VISIBLE_DEVICES pins the card
        STATE["tts"] = tts
        bank = VoiceBank(tts.proc, tts.device, gpu_lock=tts.lock)
        STATE["bank"] = bank
        cat, desc = bank.catalog(), bank.descriptions()
        cb = CodeBook(cat, desc)
        # what the director may reach for is what is installed, nothing else
        import glob as _glob
        _broot = config.LORA_ROOTS.get("burst") or ""
        _have = [os.path.basename(d) for d in _glob.glob(os.path.join(_broot, "*"))
                 if os.path.isdir(d)]
        burst_cues = lora_bank.burst_catalog(_have)
        print(f"[bursts] {len(burst_cues)} burst adapters offered to the director",
              flush=True)
        STATE["codebook"] = cb
        # one agent per (brain, prompt style); they share the http client cost
        # only at construction, so building all four up front keeps switching free
        for be in ("local",) + tuple(config.HOSTED_MODELS):
            for st in ("prose", "codes"):
                try:
                    STATE["agents"][(be, st)] = LLMAgent(
                        cat, descriptions=desc, backend=be, style=st,
                        codebook=cb, bursts=burst_cues)
                except Exception as e:
                    print(f"[app] agent {be}/{st} unavailable: {e}", flush=True)
        STATE["agent"] = STATE["agents"].get((config.DEFAULT_BRAIN, "codes")) \
            or STATE["agents"][("local", "prose")]
        STATE["profiles"] = voice_profiles.discover()
        for _v, _p in STATE["profiles"].items():      # own matrix beats borrowing
            _p["has_conditions"] = _p["has_conditions"] or bank.has_matrix(_v)
        print(f"[profiles] {len(STATE['profiles'])} voice profiles available",
              flush=True)
        try:
            STATE["retriever"] = retrieval.Retriever(device=str(tts.device))
        except Exception as e:
            print(f"[retrieval] unavailable: {e}", flush=True)
        if config.USE_LORA:
            lb = LoraBank(tts.model, tts.device)
            lb.discover(config.LORA_ROOTS)
            tts.lora = lb
            STATE["lora"] = lb
        tts.warmup()
        # speech recognition lives on the other card, next to the language model
        # Both of these load on the second card.  They must load one after the
        # other, not in parallel: transformers flips torch's global default dtype
        # while building a bfloat16 model, and a model being constructed in
        # another thread at that moment comes out bf16 too — which is how WavLM
        # ended up dying with "mixed dtype (CPU)".
        def _side_models():
            try:
                from asr_engine import ParakeetASR
                STATE["asr"] = ParakeetASR()
            except Exception as e:
                print(f"[asr] unavailable: {e}", flush=True)
            try:
                from vc_engine import VoiceConverter
                v = VoiceConverter()
                ref = os.path.join(config.REF_DIR, "reference",
                                   "reference_target.mp3")
                if v.set_target(ref):
                    STATE["vc"] = v
                    print("[vc] target set to the corpus anchor", flush=True)
            except Exception as e:
                import traceback
                print(f"[vc] unavailable: {e}", flush=True)
                traceback.print_exc()
            try:
                from score_engine import VoiceScorer
                STATE["score"] = VoiceScorer()
            except Exception as e:
                print(f"[score] unavailable: {e}", flush=True)
            try:
                from sim_engine import SpeakerSim
                STATE["sim"] = SpeakerSim(os.path.join(
                    config.REF_DIR, "reference", "reference_target.mp3"))
            except Exception as e:
                print(f"[sim] unavailable: {e}", flush=True)
        threading.Thread(target=_side_models, daemon=True).start()
        bank.preload()                       # pre-tokenise the corpus in the background
        if STATE.get("lora"):
            lb = STATE["lora"]
            names = [n for k in config.PRELOAD_LORA_KINDS
                     for n in lb.repos if n.startswith(k + ":")]
            threading.Thread(target=lb.preload, args=(names,), daemon=True).start()
        print("[app] ready", flush=True)
    except Exception as e:
        import traceback; traceback.print_exc()
        STATE["error"] = str(e)


@app.on_event("startup")
async def startup():
    threading.Thread(target=_boot, daemon=True).start()


# -------------------------------------------------------------------- routes
@app.get("/", response_class=HTMLResponse)
def index():
    return open(os.path.join(HERE, "index.html")).read()


@app.get("/studio", response_class=HTMLResponse)
def studio():
    return open(os.path.join(HERE, "studio.html"), encoding="utf-8").read()


@app.get("/api/personas")
def api_personas():
    return {"personas": personas.listing(), "default": personas.DEFAULT}


@app.post("/api/listen")
async def listen(req: Request):
    """Transcribe and, in parallel, score what the voice sounds like."""
    raw = await req.body()
    if not raw:
        return JSONResponse({"error": "empty audio"}, status_code=400)
    asr, sc = STATE["asr"], STATE["score"]
    if asr is None:
        return JSONResponse({"error": "speech recognition not ready"},
                            status_code=503)
    loop = asyncio.get_running_loop()
    t0 = time.time()
    try:
        wav = await loop.run_in_executor(None, asr._to_wav16k, raw)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    # both read the same 16 kHz array; they sit on different models so the two
    # calls overlap instead of queueing
    tasks = [loop.run_in_executor(None, asr.transcribe, wav)]
    if sc is not None:
        tasks.append(loop.run_in_executor(None, sc.score, wav))
    done = await asyncio.gather(*tasks, return_exceptions=True)
    text = done[0] if not isinstance(done[0], Exception) else ""
    heard = None
    if len(done) > 1 and not isinstance(done[1], Exception):
        heard = done[1]
    return {"text": text, "heard": heard,
            "listen_ms": round((time.time() - t0) * 1000, 1)}


@app.get("/report", response_class=HTMLResponse)
def report():
    return open(os.path.join(HERE, "report.html")).read()


@app.get("/api/state")
async def state():
    agent = STATE["agent"]
    return {
        "ready": STATE["tts"] is not None and agent is not None,
        "error": STATE["error"],
        "bank": STATE["bank"].stats() if STATE["bank"] else None,
        "lora": STATE["lora"].stats() if STATE["lora"] else None,
        "asr": bool(STATE["asr"]), "vc": bool(STATE["vc"]),
        "sim": bool(STATE["sim"]), "score": bool(STATE["score"]),
        "tts_model": config.TTS_REPO.split("/")[-1],
        "brains": ["local"] + list(config.HOSTED_MODELS),
        "profiles": voice_profiles.listing(STATE["profiles"]),
        "default_profile": config.DEFAULT_PROFILE,
        "personas": personas.listing(), "speaker_lora": config.SPEAKER_LORA in (
            STATE["lora"].repos if STATE["lora"] else {}),
        "llm": await agent.health() if agent else False,
        "sr": STATE["tts"].sr if STATE["tts"] else None,
    }


@app.get("/api/adapters")
def adapters():
    """Every adapter the overlay can dial, grouped, with its default weight.

    A default of 0 does not mean "off": it means nothing is forced and the
    director decides.  Only the three quality axes are on by default.
    """
    lb = STATE.get("lora")
    if lb is None:
        return JSONResponse({"error": "adapters disabled"}, status_code=503)
    def group(kind):
        return sorted(n.split(":", 1)[1] for n in lb.repos if n.startswith(kind + ":"))
    out = []
    out.append({"kind": "sft3_quality", "title": "Quality axes",
                "note": "On by default at the trained value of 1.0.",
                "items": [{"name": n, "label": config.QUALITY_LABELS.get(n, n),
                           "default": config.QUALITY_LORAS.get(n, 0.0), "max": 2.0}
                          for n in sorted(config.QUALITY_LORAS)
                          if n in lb.repos]})
    out.append({"kind": "sft3_voicenet", "title": "Delivery axes",
                "note": "The director picks up to two of these itself. A slider "
                        "forces one on regardless.",
                "items": [{"name": f"sft3_voicenet:{n}", "label": n,
                           "hint": config.SFT3_VN_ADAPTERS.get(n, ""),
                           "default": 0.0, "max": 2.0} for n in group("sft3_voicenet")]})
    out.append({"kind": "sft3_emotion", "title": "Emotions",
                "note": "The retrieval picks one per turn at 1.5. A slider adds "
                        "or replaces it.",
                "items": [{"name": f"sft3_emotion:{n}", "label": n.replace("_", " "),
                           "default": 0.0, "max": 2.0} for n in group("sft3_emotion")]})
    out.append({"kind": "burst", "title": "Vocal bursts",
                "note": f"Added automatically when the script contains one, at "
                        f"{config.BURST_LAM} ({config.BURST_LAM_INTENSE} standing alone).",
                "items": [{"name": f"burst:{n}", "label": n.replace("_", " "),
                           "default": 0.0, "max": 1.5} for n in group("burst")]})
    return {"groups": out,
            "always": [{"name": config.SFT3_DPO_LORA, "label": "Quality (DPO p2)",
                        "default": config.SFT3_DPO_LAM},
                       {"name": "sft3_voice:<profile>", "label": "Voice identity",
                        "default": config.PROFILE_LORA_LAM}]}


@app.get("/api/voices")
def voices():
    if not STATE["bank"]:
        return JSONResponse({"error": "not ready"}, status_code=503)
    return {"catalog": STATE["bank"].catalog(), "tool": VOICE_TOOL,
            "stats": STATE["bank"].stats()}


@app.post("/api/say")
async def say(req: Request):
    """Speak an exact text with an exact instruction — no language model in the
    loop.  This is the harness for measuring the voice model on its own."""
    import base64
    b = await req.json()
    tts, bank = STATE["tts"], STATE["bank"]
    if not tts:
        return JSONResponse({"error": "not ready"}, status_code=503)
    ref = []
    if b.get("anchor", True) and bank:
        a = bank.anchor()
        if a is not None:
            ref.append(a)
    if b.get("reference") and bank:
        hit = bank.select(b["reference"], language=b.get("ref_lang", "en"),
                          speed=float(b.get("speed", 1.0)))
        if hit:
            ref.append(hit["codes"])

    chunks, meta = [], {}
    def run():
        for kind, payload in tts.stream_pcm(
                text=b["text"], instruction=b.get("instruction", ""),
                language=b.get("language", "English"), ref_codes=ref or None,
                lora_specs=b.get("loras"), tokens=b.get("tokens"),
                seed=b.get("seed"), audio_temperature=b.get("audio_temperature"),
                max_new_tokens=b.get("max_new_tokens"),
                chunk_frames=b.get("chunk_frames"),
                stop_bias=b.get("stop_bias")):
            if kind == "pcm":
                chunks.append(payload)
            elif kind == "end":
                meta.update(payload)
    await asyncio.get_running_loop().run_in_executor(None, run)
    w = np.concatenate(chunks) if chunks else np.zeros(1, np.float32)
    pcm = np.clip(w * 32767, -32768, 32767).astype("<i2").tobytes()
    return {"sr": tts.sr, "pcm": base64.b64encode(pcm).decode(), **meta}


@app.post("/api/asr")
async def asr(req: Request):
    """Transcribe a browser recording with Parakeet TDT 0.6B v3."""
    asr = STATE["asr"]
    if asr is None:
        return JSONResponse({"error": "speech recognition not ready"},
                            status_code=503)
    raw = await req.body()
    if not raw:
        return JSONResponse({"error": "empty audio"}, status_code=400)
    t0 = time.time()
    try:
        text = await asyncio.get_running_loop().run_in_executor(
            None, asr.transcribe, raw)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    return {"text": text, "asr_ms": round((time.time() - t0) * 1000, 1)}


@app.post("/api/turn")
async def turn(req: Request):
    body = await req.json()
    message = (body.get("message") or "").strip()
    history = body.get("history") or []
    language = body.get("language") or "English"
    if not message:
        return JSONResponse({"error": "empty message"}, status_code=400)
    if STATE["error"]:
        return JSONResponse({"error": STATE["error"]}, status_code=500)
    if not (STATE["tts"] and STATE["agent"]):
        return JSONResponse({"error": "model still loading"}, status_code=503)

    tts, bank = STATE["tts"], STATE["bank"]
    # the browser sends only the choice, never a key
    be = str(body.get("brain") or config.DEFAULT_BRAIN)
    if be != "local" and be not in config.HOSTED_MODELS:
        be = config.DEFAULT_BRAIN
    # Default is the language model's own prose: it writes the GENERAL delivery
    # line and the inline cues itself, instead of emitting codes that get
    # expanded procedurally.  Costs output tokens, buys direction that is written
    # for this moment rather than assembled from a table.
    st = "codes" if str(body.get("prompt_style")) == "codes" else "prose"
    agent = STATE["agents"].get((be, st)) or STATE["agent"]
    persona = personas.brief_for(body.get("persona"), body.get("persona_custom"))
    persona_loras = personas.loras_for(body.get("persona"),
                                       body.get("persona_custom"))
    profs = STATE["profiles"] or {}
    prof = profs.get(str(body.get("profile") or config.DEFAULT_PROFILE)) \
        or profs.get(config.DEFAULT_PROFILE)
    heard = body.get("heard_summary")
    t_req = time.time()

    async def gen():
        # ---- 1. the brain -------------------------------------------------
        try:
            out, llm_ms, _ = await agent.turn(
                message, history, persona=persona, heard=heard,
                identity=(prof or {}).get("identity"))
        except Exception as e:
            yield _ev({"type": "error", "where": "llm", "message": str(e)})
            return

        # ---- 2. reference retrieval (already in RAM, pre-tokenised) --------
        # the model decides which language it is speaking; the reference must be
        # drawn from that language and the voice model told the same thing
        spoken = out.get("language") or language
        t_sel = time.time()
        lang2 = "de" if str(spoken).lower().startswith(("ger", "de")) else "en"
        # The declared language is not reliable — a turn written wholly in German
        # came back declared as English, which then drew an English reference
        # clip for it.  The words themselves settle it.
        if lang2 == "en" and retrieval.looks_german(out.get("reply") or ""):
            lang2 = "de"
            spoken = "German"
        speed = config.SPEED_WORDS.get(out.get("speed") or "normal", 1.0)
        try:
            pv = prof["id"] if prof else None
            hit = bank.select(out.get("voice"), language=lang2, speed=speed,
                              voice=pv)
            # an optional second condition, concatenated after the first, for a
            # line that genuinely moves through two states
            v2 = out.get("voice2") or {}
            hit2 = (bank.select(v2, language=lang2, speed=speed, voice=pv)
                    if v2.get("mode") not in (None, "none", "") else None)
        except Exception as e:
            print("[app] voice select failed:", e, flush=True)
            hit = hit2 = None

        # Retrieval: the director's own prose decides the reference clip.
        # Everything it wrote about sound — the standing GENERAL description and
        # every bracketed cue — is concatenated, embedded with the
        # VoiceCLAP-commercial text tower and matched against the corpus.  This
        # replaces the clip the code path picked, because it is chosen from what
        # the director actually asked for rather than from a decoded label.
        retr = None
        want_emo = body.get("emotion_nuance", config.EMOTION_NUANCE_ON) is not False
        R = STATE.get("retriever")
        if R is not None and R.ok and body.get("retrieval", config.RETRIEVAL_ON) is not False:
            try:
                _gen, _cues = retrieval.split_direction(
                    out.get("general") or (prof or {}).get("identity"),
                    out.get("script"), out.get("text"))
                direction = " ".join(b for b in (_gen, _cues) if b)[:800]
                lvl = {"intense": "A", "contained": "B"}.get(
                    (out.get("voice") or {}).get("intensity"))
                # The emotion is read off the cues, but only when they are in
                # the language the text tower actually speaks.  Otherwise fall
                # back to the emotion the director named, which is always an
                # English label from a fixed vocabulary.
                _eq = _cues
                _named = (out.get("voice") or {}).get("emotion")
                if _named and (not _cues or retrieval.looks_german(_cues)):
                    _eq = f"a person speaking with {_named.replace('_', ' ').lower()} in their voice"
                retr = R.query(direction, voice=pv, lang=lang2, level=lvl,
                               emotion_nuance=want_emo, cues=_eq)
                for h in (retr or {}).get("hits", []):
                    got = bank.select_gid(h["gid"], speed)
                    if got is not None:
                        hit = got
                        retr["used"] = h
                        break
            except Exception as e:
                print("[app] retrieval failed:", e, flush=True)
                retr = None
        sel_ms = (time.time() - t_sel) * 1000
        # identity anchor first, then the delivery clip(s) in order
        ref_codes = []
        if config.USE_ANCHOR and out.get("voice", {}).get("mode") != "character":
            a = bank.anchor(prof["anchor"]) if prof else bank.anchor()
            if a is not None:
                ref_codes.append(a)
        # The 832 conditioned clips are renderings of one specific speaker, so
        # they only belong in the prompt when that is the speaker being asked
        # for.  For any other profile the delivery comes from the emotion and
        # VoiceNet adapters instead, and the reference stays purely its anchor.
        if hit and (prof is None or prof.get("has_conditions")
                    or bank.has_matrix(prof["id"])):
            ref_codes.append(hit["codes"])
        if hit2 and hit2["entry"]["id"] != (hit or {}).get("entry", {}).get("id"):
            ref_codes.append(hit2["codes"])
        # anchor (who) -> tails of the last turns (how they were just speaking)
        # -> this moment's condition clip (what to do now)
        sess = _session(body.get("session"))
        if sess and config.USE_TAIL_CONTEXT and ref_codes:
            ref_codes = ref_codes[:1] + sess["tails"] + ref_codes[1:]
        ref_codes = ref_codes or None
        chosen = None
        if hit:
            e = hit["entry"]
            chosen = {k: e.get(k) for k in
                      ("id", "block", "emotion", "intensity", "containment",
                       "dimension", "level", "character", "edge_case", "language")}
            chosen["frames"] = int(hit["codes"].shape[0])
            chosen["anchored"] = config.USE_ANCHOR
            chosen["speed"] = hit.get("speed", 1.0)
            if hit2:
                e2 = hit2["entry"]
                chosen["then"] = (e2.get("emotion") or e2.get("character")
                                  or e2.get("dimension") or e2.get("edge_case"))

        # ---- 2b. which adapters this turn gets (doses from the manual) -----
        # "Pure" mode: the v2 base model, the retrieved reference clips, and the
        # voice's own character adapter — nothing else.  Every expressive adapter
        # (emotion, VoiceNet, burst, aesthetics, base style) is left off, so the
        # performance comes from the reference audio and the prompt alone, the
        # way the base model was meant to be driven.
        # Pure is the default: base model + this voice's own reference clips +
        # its character adapter.  Every profile now has its own 842-condition
        # matrix, so the delivery can come from real recordings of that speaker
        # rather than from expressive adapters stacked on a borrowed voice.
        # Pure: the tuned base model plus this voice's own reference clips, and
        # nothing else.  The character adapter is a separate switch because it
        # was trained against the untuned weights.
        pure = body.get("pure_mode", False) is True
        want_char = body.get("char_lora", True) is not False
        specs = []
        lb = STATE.get("lora")
        # perceptual-quality adapters: on by default, each with its own slider
        q_spec = []
        if lb:
            ql = body.get("quality_lams") or {}
            for nm, dflt in config.QUALITY_LORAS.items():
                lam = ql.get(nm, ql.get(nm.split(":")[-1], dflt))
                try:
                    lam = float(lam)
                except (TypeError, ValueError):
                    lam = dflt
                if lam > 0.001 and nm in lb.repos:
                    q_spec.append((nm, lam))
        vn_spec = []
        if lb and body.get("delivery_loras", True) is not False:
            seen_vn = set()
            for it in (out.get("style") or []):
                if not isinstance(it, dict):
                    continue
                a = it.get("adapter")
                if a not in config.SFT3_VN_ADAPTERS or a in seen_vn:
                    continue
                try:
                    lam = float(it.get("strength") or 0)
                except (TypeError, ValueError):
                    continue
                # the set is a pilot and unevaluated; keep it inside the dial
                lam = max(0.0, min(lam, max(config.SFT3_VN_LEVELS)))
                nm = f"sft3_voicenet:{a}"
                if lam > 0.001 and nm in lb.repos:
                    seen_vn.add(a)
                    vn_spec.append((nm, lam))
                if len(vn_spec) >= config.SFT3_VN_MAX:
                    break
        dpo_spec = []
        if lb and body.get("dpo_lora", True) is not False \
                and config.SFT3_DPO_LORA in lb.repos and config.SFT3_DPO_LAM > 0.001:
            dpo_spec = [(config.SFT3_DPO_LORA, config.SFT3_DPO_LAM)]
        emo_spec = []
        if (lb and want_emo and retr and retr.get("emotion")
                and f"sft3_emotion:{retr['emotion']}" in lb.repos):
            # 1.5 is the published operating point: emotion 0.408 -> 0.471 with
            # genuineness and burst blend rising alongside it, and median word
            # error still 0.000.  Off when the emotion nuances are switched off,
            # which leaves the base checkpoint and the retrieved clip alone.
            emo_spec = [(f"sft3_emotion:{retr['emotion']}", config.SFT3_EMOTION_LAM)]
        if lb and pure:
            if want_char:
                lam = body.get("profile_lora_lam")
                lam = config.PURE_PROFILE_LAM if lam is None else float(lam)
                if prof and prof["lora"] in lb.repos and lam > 0.001:
                    specs = [(prof["lora"], lam)]
            specs = dpo_spec + q_spec + specs + vn_spec + emo_spec
        elif lb:
            try:
                mix = out.get("blend")
                if mix:
                    # code mode gave us the whole mixture: merge every emotion in
                    # it, weighted by its level, plus the voice qualities
                    specs = lora_bank.plan_blend(
                        mix, out.get("script"),
                        have_emotion=set(lb.names("emotion")),
                        have_voicenet=set(lb.names("voicenet")),
                        have_burst=lb.names("burst"))
                else:
                    specs = lora_bank.plan(
                        out.get("voice"), out.get("script"),
                        have_emotion=set(lb.names("emotion")),
                        have_character=set(lb.names("character")),
                        have_burst=lb.names("burst"),
                        have_voicenet=set(lb.names("voicenet")),
                        style=None)
            except Exception as e:
                print("[app] lora plan failed:", e, flush=True)
            # The speaker adapter goes on top of everything else: it is what makes
            # the voice the same person from turn to turn, so it is not one of the
            # per-moment choices the director gets to make.
            # Both of these are dials on the voice itself rather than choices
            # about this moment, so they are prepended, and a dose of 0 simply
            # means the adapter is not merged at all.
            def _dial(flag, dose, name, default_lam):
                if flag is False or name not in lb.repos:
                    return None
                lam = default_lam if dose is None else float(dose)
                return (name, lam) if lam > 0.001 else None

            # The base style is a floor, not a ceiling: if the director asked for
            # one of these dimensions itself — WARM low for something cold, or
            # S_CASU low for something formal — that choice wins, because it was
            # made for this moment and the default was not.
            chosen_dims = {n.rsplit("__", 1)[0] for n, _ in specs
                           if n.startswith("voicenet:")}
            base_style = [] if body.get("base_style") is False else [
                (n, l) for n, l in config.BASE_STYLE_LORAS
                if n in lb.repos and n.rsplit("__", 1)[0] not in chosen_dims]
            fixed = base_style + [(n, l) for n, l in persona_loras
                                  if n in lb.repos and
                                  n not in {x for x, _ in base_style}]
            have_profile = False
            if prof and prof["lora"] in lb.repos:
                lam = body.get("profile_lora_lam")
                lam = config.PROFILE_LORA_LAM if lam is None else float(lam)
                if lam > 0.001:
                    fixed = [(prof["lora"], lam)] + fixed
                    have_profile = True
            head = fixed + [x for x in (
                _dial(body.get("speaker_lora", not have_profile)
                      and not have_profile,
                      body.get("speaker_lora_lam"),
                      config.SPEAKER_LORA, config.SPEAKER_LORA_LAM),
                _dial(body.get("aesth_lora", True), body.get("aesth_lora_lam"),
                      config.AESTH_LORA, config.AESTH_LORA_LAM),
            ) if x]
            # a fixed or dialled adapter wins over the same one picked as a
            # per-moment style, so it keeps its intended dose
            picked = {n for n, _ in head}
            specs = head + [s for s in specs if s[0] not in picked]
            if dpo_spec:
                specs = dpo_spec + [x for x in specs if x[0] != config.SFT3_DPO_LORA]
            if q_spec:
                picked_q = {n for n, _ in q_spec}
                specs = [x for x in specs if x[0] not in picked_q] + q_spec
            if vn_spec:
                picked_vn = {n for n, _ in vn_spec}
                specs = [x for x in specs if x[0] not in picked_vn] + vn_spec
            if emo_spec:
                # the v3 emotion adapters were trained against the untuned v2
                # weights; on sft3 the matching set is the one trained with it
                specs = [s for s in specs if not s[0].startswith("emotion:")] + emo_spec

        # The overlay's sliders: a full adapter name mapped to a weight.  0 means
        # "leave it to the director", which is not the same as forcing it off —
        # the director's own picks stay unless a slider names them.
        ov = body.get("adapter_overrides") or {}
        if lb and isinstance(ov, dict) and ov:
            forced = []
            for nm, lam in ov.items():
                try:
                    lam = float(lam)
                except (TypeError, ValueError):
                    continue
                if lam > 0.001 and nm in lb.repos:
                    forced.append((nm, lam))
            if forced:
                names = {n for n, _ in forced}
                specs = [x for x in specs if x[0] not in names] + forced

        yield _ev({"type": "llm", "reply": out["reply"], "general": out["general"],
                   "script": out["script"], "voice": out.get("voice"),
                   "chosen": chosen, "llm_ms": round(llm_ms, 1),
                   "select_ms": round(sel_ms, 1), "language": out.get("language"),
                   "speed": out.get("speed"), "style": out.get("style"),
                   "brain": be, "prompt_style": st, "codes": out.get("codes"),
                   "profile": prof["id"] if prof else None,
                   "pure": pure, "char_lora": want_char,
                   "retrieval": ({"direction": retr.get("direction"),
                                  "emotion": retr.get("emotion"),
                                  "emotions": retr.get("emotions", [])[:3],
                                  "used": {k: retr["used"].get(k) for k in
                                           ("gid", "emotion", "dim", "level",
                                            "lang", "score", "genuineness",
                                            "blend")}
                                  if retr.get("used") else None}
                                 if retr else None),
                   "emotion_nuance": want_emo,
                   "ref_clips": len(ref_codes or []),
                   # only the corpus voice has the 832 conditioned clips, so for
                   # any other profile the reference is its anchor alone
                   "ref_conditioned": bool(hit and (prof is None
                                                    or prof.get("has_conditions")
                                                    or bank.has_matrix(prof["id"]))),
                   "loras": [{"name": n, "lam": l} for n, l in specs],
                   "cached": bool(hit and hit["entry"]["id"] in bank.codes)})

        # ---- 3. stream the performance ------------------------------------
        q: asyncio.Queue = asyncio.Queue(maxsize=64)
        loop = asyncio.get_running_loop()
        want_vc = bool(body.get("voice_conversion")) and STATE["vc"] is not None
        vc = STATE["vc"] if want_vc else None
        if vc is not None and prof:
            # otherwise every profile is converted onto the corpus anchor, which
            # is exactly how every voice ended up sounding like Velvet Sage
            try:
                await loop.run_in_executor(None, vc.use_target, prof["anchor"])
            except Exception as e:
                print("[vc] target switch failed:", e, flush=True)
        vc_st = vc.new_stream(tts.sr or 48000) if vc is not None else None
        take = []          # kept only to score speaker similarity at the end

        # If the client goes away mid-reply — tab closed, connection dropped — the
        # producer thread would otherwise block forever handing the next chunk to
        # a queue nobody drains, and it holds the generation lock while it does,
        # which wedges every later request.  The flag lets it notice and unwind.
        gone = threading.Event()

        def produce():
            try:
                from llm_agent import LLMAgent as _A
                for kind, payload in tts.stream_utterance(
                        script=out["script"], general=out["general"],
                        strip=_A._strip_tags,
                        language=spoken, ref_codes=ref_codes, lora_specs=specs,
                        speed=speed,
                        reads_as=((retr or {}).get("emotion")
                                  or (out.get("voice") or {}).get("emotion")),
                        max_new_tokens=body.get("max_new_tokens"),
                        chunk_frames=body.get("chunk_frames"),
                        seed=body.get("seed"),
                        audio_temperature=body.get("audio_temperature"),
                        stop_bias=body.get("stop_bias")):
                    if gone.is_set():
                        break
                    if not _handoff(q, loop, (kind, payload), gone):
                        break
            except Exception as e:
                import traceback; traceback.print_exc()
                _handoff(q, loop, ("error", {"message": str(e)}), gone)
            finally:
                _handoff(q, loop, (None, None), gone)

        threading.Thread(target=produce, daemon=True).start()

        try:
          while True:
            kind, payload = await q.get()
            if kind is None:
                break
            if kind == "pcm":
                if vc is not None:
                    payload = await loop.run_in_executor(
                        None, vc.convert_chunk, payload, vc_st)
                    if payload is None or not payload.size:
                        continue
                take.append(payload)
                yield _pcm(payload)
            elif kind == "start":
                payload = dict(payload)
                # wall-clock from request arrival to the first audio leaving the server
                payload["ttfa_server_ms"] = round((time.time() - t_req) * 1000, 1)
                payload["type"] = "start"
                yield _ev(payload)
            elif kind == "end":
                if vc is not None:                 # emit the held-back seam
                    tailp = vc.flush(vc_st)
                    if tailp.size:
                        yield _pcm(tailp)
                payload = dict(payload)
                payload["type"] = "end"
                payload["server_total_ms"] = round((time.time() - t_req) * 1000, 1)
                payload["llm_ms"] = round(llm_ms, 1)
                payload["speaker_lora"] = next(
                    (l for n, l in specs if n == config.SPEAKER_LORA), 0.0)
                payload["aesth_lora"] = next(
                    (l for n, l in specs if n == config.AESTH_LORA), 0.0)
                payload["vc"] = vc is not None
                tail = payload.pop("tail_codes", None)
                if sess is not None and tail is not None and len(tail):
                    sess["tails"].append(tail)
                    del sess["tails"][:-config.TAIL_TURNS]
                payload["tail_turns"] = len(sess["tails"]) if sess else 0
                if STATE["sim"] and take:
                    t_s = time.time()
                    w = np.concatenate(take)
                    payload["speaker_sim"] = await loop.run_in_executor(
                        None, STATE["sim"].score, w, tts.sr,
                        (prof or {}).get("anchor"))
                    payload["sim_ms"] = round((time.time() - t_s) * 1000, 1)
                yield _ev(payload)
            elif kind == "error":
                yield _ev({"type": "error", "where": "tts", **payload})
        finally:
            # the client may have disconnected; tell the producer to stop so it
            # releases the generation lock instead of parking on the queue
            gone.set()
            try:
                while True:
                    q.get_nowait()
            except Exception:
                pass

    return StreamingResponse(gen(), media_type="application/octet-stream",
                             headers={"Cache-Control": "no-store",
                                      "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.APP_PORT)
