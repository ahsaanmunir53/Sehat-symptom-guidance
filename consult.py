"""
SEHAT consultation engine.

Flow per session:
  intake -> deterministic emergency/crisis screen
         -> history taking (one doctor question per turn)
         -> structured assessment
         -> free follow-up questions

Every incoming patient message is re-screened deterministically, so an
emergency typed mid-consultation is caught even if the model misses it.
"""

import json
import os
import re
import time
import uuid

import firstaid
import otc
import prompts
import safety
from llm import LLMError, call_llm, config

MAX_QUESTIONS = int(os.environ.get("SEHAT_MAX_QUESTIONS", "8"))
SESSION_TTL = 60 * 60 * 6  # 6 hours

DISCLAIMER = ("SEHAT helps you understand symptoms and prepare for a doctor's "
              "visit. It is not a medical diagnosis and not a substitute for a "
              "qualified doctor. For treatment, always consult your doctor.")

_SESSIONS: dict[str, dict] = {}


# ------------------------------------------------------------------ helpers

def _prune():
    now = time.time()
    dead = [k for k, s in _SESSIONS.items() if now - s["touched"] > SESSION_TTL]
    for k in dead:
        _SESSIONS.pop(k, None)


def _emergency_payload(rule: dict) -> dict:
    proto = firstaid.get_protocol(rule["protocol"]) or firstaid.get_protocol("unconscious")
    return {
        "type": "emergency",
        "label": rule["label"],
        "reason": rule.get("reason", ""),
        "call": firstaid.CALL,
        "ambulance_alt": "Edhi 115",
        "protocol": proto,
    }


def _crisis_payload() -> dict:
    return {
        "type": "crisis",
        "message": ("What you're carrying right now sounds really heavy, and you "
                    "don't have to carry it alone. Please talk to someone who can "
                    "actually be with you in this - a person you trust, or the "
                    "trained counsellors below. They listen for free, any time, "
                    "and you can stay anonymous."),
        "helplines": [
            {"name": "Umang - 24/7 mental health helpline (free)", "number": "0311-7786264"},
            {"name": "Rescue (if someone is in immediate danger)", "number": "1122"},
        ],
        "note": "If you have already taken something or hurt yourself, go to the nearest hospital emergency now.",
    }


def _parse_llm_json(raw: str):
    s = (raw or "").strip()
    s = re.sub(r"^```(?:json)?", "", s).strip()
    s = re.sub(r"```$", "", s).strip()
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no json object")
    return json.loads(s[start:end + 1])


def _profile_line(p: dict) -> str:
    parts = [f"{p['sex'].capitalize()}, {p['age']}"]
    if p.get("pregnant"):
        w = int(p.get("pregnancy_weeks") or 0)
        parts.append(f"Pregnant - {w} weeks ({prompts.trimester(w)})")
    return " · ".join(parts)


# ---------------------------------------------------------------- demo mode

_DEMO_QUESTIONS = [
    {"question": "When exactly did this start, and did it come on suddenly or slowly?",
     "why_asking": "Onset separates urgent causes from gradual ones.",
     "quick_options": ["Today, suddenly", "Today, gradually", "A few days ago", "More than a week"]},
    {"question": "How severe is it right now, from 1 (barely there) to 10 (worst ever)?",
     "why_asking": "Severity guides how urgently you need care.",
     "quick_options": ["1-3 mild", "4-6 moderate", "7-8 severe", "9-10 worst ever"]},
    {"question": "Is anything else happening along with it - fever, vomiting, dizziness, rash, or anything unusual?",
     "why_asking": "Associated symptoms often point to the cause.",
     "quick_options": ["Fever", "Vomiting/nausea", "Dizziness", "None of these"]},
    {"question": "Does anything make it better or worse - food, rest, movement, a particular position?",
     "why_asking": "Triggers and relievers narrow the possibilities.",
     "quick_options": []},
    {"question": "Any ongoing conditions (sugar, BP, asthma) or medicines you take regularly?",
     "why_asking": "Existing conditions change what this could be.",
     "quick_options": ["None", "Diabetes", "Blood pressure", "Other"]},
    {"question": "Has this ever happened before? If yes, what helped last time?",
     "why_asking": "A repeating pattern is itself a clue.",
     "quick_options": ["First time", "Happened before"]},
]

_SPECIALTY_MAP = [
    (["chest", "heart", "palpitation", "seenay"], "Cardiologist"),
    (["headache", "migraine", "dizzy", "numb", "tingling", "sir dard", "chakkar"], "Neurologist"),
    (["stomach", "abdominal", "vomit", "diarrhoea", "diarrhea", "constipation", "pait", "acidity", "ulcer"], "Gastroenterologist"),
    (["cough", "breath", "wheez", "asthma", "khansi", "saans"], "Pulmonologist"),
    (["urine", "urinat", "kidney", "peshab"], "Urologist"),
    (["pregnan", "period", "mahwari", "hamal", "discharge"], "Gynaecologist"),
    (["skin", "rash", "itch", "kharish", "acne", "daane"], "Dermatologist"),
    (["joint", "knee", "back pain", "bone", "haddi", "kamar"], "Orthopaedic specialist"),
    (["ear", "throat", "nose", "gala", "kaan", "sinus"], "ENT specialist"),
    (["eye", "vision", "aankh", "nazar"], "Eye specialist (Ophthalmologist)"),
    (["anxiety", "depress", "sad", "sleep", "stress", "pareshan", "udaas"], "Psychiatrist"),
]


def _demo_specialist(complaint: str) -> str:
    low = complaint.lower()
    for keys, spec in _SPECIALTY_MAP:
        if any(k in low for k in keys):
            return spec
    return "General Physician"


def _demo_assessment(profile: dict, answers: list) -> dict:
    spec = _demo_specialist(profile["complaint"])
    pregnant = bool(profile.get("pregnant"))
    a = {
        "case_summary": (f"{_profile_line(profile)} presenting with: {profile['complaint']}. "
                         f"History taken over {len(answers)} answers (demo mode - recorded but "
                         "not analysed by AI)."),
        "possible_conditions": [],
        "demo_note": ("Demo mode: the AI engine is not connected, so SEHAT cannot analyse "
                      "possible conditions. Add your Anthropic API key (Claude Fable 5) to "
                      "unlock the full doctor-style assessment. Everything below is safe, "
                      "general guidance."),
        "red_flags": [
            "Symptoms suddenly become severe or rapidly worse",
            "Difficulty breathing, chest pressure, fainting, or confusion",
            "High fever that does not settle with paracetamol",
            "Severe pain, repeated vomiting, or blood anywhere it shouldn't be",
        ],
        "precautions": [
            "Don't self-prescribe antibiotics or someone else's medicines",
            "Keep a simple note of when symptoms happen and what makes them better or worse",
        ],
        "self_care": [
            "Rest, fluids, and light regular meals unless a doctor has said otherwise",
        ],
        "otc": [],
        "see_doctor": {
            "urgency": "within_3_days",
            "who": spec,
            "why": "A physical examination is what turns possibilities into an answer.",
        },
        "questions_for_your_doctor": [
            "What examinations or tests do I need to confirm the cause?",
            "What warning signs mean I should come back immediately?",
            "Is there anything I should stop or avoid until we know more?",
        ],
    }
    if pregnant:
        w = int(profile.get("pregnancy_weeks") or 0)
        a["pregnancy_note"] = (f"At {w} weeks ({prompts.trimester(w)}), check every medicine "
                               "with your gynaecologist first. Paracetamol is the usual safe "
                               "choice for pain or fever; avoid ibuprofen.")
        a["see_doctor"]["who"] = "Gynaecologist (you are pregnant - she coordinates everything)"
    return a


# ------------------------------------------------------------ postprocessing

_URGENCIES = {"within_24_hours", "within_3_days", "this_week", "routine"}


def _clean_assessment(a: dict, profile: dict) -> dict:
    a = dict(a or {})
    pregnant = bool(profile.get("pregnant"))

    # OTC allow-list: keep only curated medicines, attach curated notes,
    # drop anything pregnancy-unsafe for a pregnant patient
    cleaned = []
    for item in a.get("otc") or []:
        entry = otc.match(item.get("name", "") if isinstance(item, dict) else str(item))
        if not entry:
            continue
        if pregnant and not entry["pregnancy_safe"]:
            continue
        cleaned.append({
            "name": entry["name"],
            "adult": entry["adult"],
            "note": (item.get("note", "") if isinstance(item, dict) else ""),
            "preg_note": entry["preg_note"] if pregnant else "",
            "cautions": entry["cautions"],
        })
    a["otc"] = cleaned

    sd = a.get("see_doctor") or {}
    if sd.get("urgency") not in _URGENCIES:
        sd["urgency"] = "within_3_days"
    sd.setdefault("who", "General Physician")
    sd.setdefault("why", "")
    a["see_doctor"] = sd

    for key in ("possible_conditions", "red_flags", "precautions", "self_care",
                "questions_for_your_doctor"):
        a.setdefault(key, [])
    if not pregnant:
        a.pop("pregnancy_note", None)

    a = safety.scrub_deep(a)
    a["disclaimer"] = DISCLAIMER
    a["patient_line"] = _profile_line(profile)
    return a


# ---------------------------------------------------------------- LLM turns

def _llm_turn(sess: dict, force_assess: bool = False) -> dict:
    profile = sess["profile"]
    system = prompts.build_system(profile, sess["asked"], MAX_QUESTIONS)
    if sess["stage"] == "followup":
        system += prompts.FOLLOWUP_SUFFIX
    messages = list(sess["messages"])
    if force_assess:
        messages.append({"role": "user",
                         "content": "SYSTEM: You have asked enough questions. "
                                    "Produce the assessment JSON now."})

    raw = call_llm(system, messages)
    try:
        obj = _parse_llm_json(raw)
    except ValueError:
        messages.append({"role": "assistant", "content": raw})
        messages.append({"role": "user",
                         "content": "SYSTEM: Reply again with ONLY the JSON object, "
                                    "nothing else."})
        raw = call_llm(system, messages)
        obj = _parse_llm_json(raw)

    sess["messages"].append({"role": "assistant", "content": json.dumps(obj, ensure_ascii=False)})
    return obj


def _dispatch(sess: dict, obj: dict) -> dict:
    action = obj.get("action")
    if action == "emergency":
        sess["stage"] = "emergency"
        rule = {"label": "Medical emergency", "reason": obj.get("reason", ""),
                "protocol": obj.get("protocol") if obj.get("protocol") in firstaid.PROTOCOLS
                else "unconscious"}
        return _emergency_payload(rule)
    if action == "crisis":
        sess["stage"] = "crisis"
        return _crisis_payload()
    if action == "assess":
        sess["stage"] = "followup"
        assessment = _clean_assessment(obj.get("assessment") or {}, sess["profile"])
        return {"type": "assessment", "assessment": assessment,
                "session_id": sess["id"]}
    if action == "followup":
        return {"type": "followup", "answer": safety.scrub_text(obj.get("answer", "")),
                "session_id": sess["id"]}
    # default: a question
    sess["asked"] += 1
    return {"type": "question",
            "question": obj.get("question", "Tell me more about it."),
            "why_asking": obj.get("why_asking", ""),
            "quick_options": (obj.get("quick_options") or [])[:5],
            "progress": {"asked": sess["asked"], "max": MAX_QUESTIONS},
            "session_id": sess["id"]}


# ------------------------------------------------------------------- public

def start(profile: dict) -> dict:
    _prune()
    complaint = profile["complaint"]

    if safety.screen_crisis(complaint):
        return _crisis_payload()
    rule = safety.screen_emergency(complaint, profile)
    if rule:
        return _emergency_payload(rule)

    sess = {
        "id": uuid.uuid4().hex,
        "profile": profile,
        "messages": [{"role": "user",
                      "content": f"My problem: {complaint}"
                                 + (f" (since: {profile['duration']})" if profile.get("duration") else "")}],
        "asked": 0,
        "stage": "history",
        "touched": time.time(),
        "demo": not config()["configured"],
    }
    _SESSIONS[sess["id"]] = sess

    if sess["demo"]:
        sess["asked"] = 1
        q = _DEMO_QUESTIONS[0]
        return {"type": "question", **q,
                "progress": {"asked": 1, "max": len(_DEMO_QUESTIONS)},
                "session_id": sess["id"], "demo": True}

    # answer() already guarded this; start() did not, so a failing model
    # escaped as a 500 with no readable body and the page could only say
    # "Something went wrong" — hiding the actual cause from everyone.
    try:
        obj = _llm_turn(sess)
    except LLMError as exc:
        return {"type": "error", "message": str(exc), "session_id": sess["id"]}
    except ValueError:
        return {"type": "error", "session_id": sess["id"],
                "message": "The AI reply couldn't be read. Please try again."}
    return _dispatch(sess, obj)


def answer(session_id: str, text: str) -> dict:
    _prune()
    sess = _SESSIONS.get(session_id)
    if not sess:
        return {"type": "error",
                "message": "This consultation has expired. Please start again."}
    sess["touched"] = time.time()

    # deterministic screens on every patient message
    if safety.screen_crisis(text):
        sess["stage"] = "crisis"
        return _crisis_payload()
    rule = safety.screen_emergency(text, sess["profile"])
    if rule:
        sess["stage"] = "emergency"
        return _emergency_payload(rule)
    reason = safety.guard_dose(text)
    if reason:
        return {"type": "guard", "message": safety.GUARD_MESSAGES[reason],
                "session_id": sess["id"]}

    sess["messages"].append({"role": "user", "content": text})

    if sess["demo"]:
        if sess["stage"] == "followup":
            return {"type": "followup", "session_id": sess["id"],
                    "answer": ("Demo mode can't analyse follow-up questions - connect "
                               "your Anthropic API key for the full engine. For anything "
                               "urgent, use the Emergency & First Aid section or see a "
                               "doctor.")}
        if sess["asked"] < len(_DEMO_QUESTIONS):
            q = _DEMO_QUESTIONS[sess["asked"]]
            sess["asked"] += 1
            return {"type": "question", **q,
                    "progress": {"asked": sess["asked"], "max": len(_DEMO_QUESTIONS)},
                    "session_id": sess["id"], "demo": True}
        sess["stage"] = "followup"
        answers = [m["content"] for m in sess["messages"] if m["role"] == "user"]
        assessment = _clean_assessment(_demo_assessment(sess["profile"], answers[1:]),
                                       sess["profile"])
        assessment["demo"] = True
        return {"type": "assessment", "assessment": assessment,
                "session_id": sess["id"], "demo": True}

    try:
        force = sess["stage"] == "history" and sess["asked"] >= MAX_QUESTIONS
        obj = _llm_turn(sess, force_assess=force)
    except LLMError as exc:
        return {"type": "error", "message": str(exc), "session_id": sess["id"]}
    except ValueError:
        return {"type": "error", "session_id": sess["id"],
                "message": "The AI reply couldn't be read. Please send that again."}
    return _dispatch(sess, obj)
