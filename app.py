"""
SEHAT — symptom guidance service.

Request flow, in order. Each layer can stop the request before the next runs.

    1. validate        age / description sanity
    2. crisis screen   self-harm language -> support resources, never triage
    3. red-flag screen emergency phrases  -> "go now", model never called
    4. model           Groq, constrained to JSON, forbidden from naming drugs
    5. scrub           strip any drug name or dose that got through anyway
    6. otc lookup      curated table, keyed by the model's category choice

The model is the only untrusted part, and it sits between two deterministic
gates. It can never decide that chest pain is minor, and it can never put a
drug name in front of a user.
"""
from __future__ import annotations

import json
import os
import re
from typing import List, Optional

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from otc import ALLOWED_KEYS, lookup

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")

app = FastAPI(title="SEHAT", docs_url="/api/docs", redoc_url=None)

# ── screening tables ──────────────────────────────────────────────────────
RED_FLAGS = [
    (r"\bchest (pain|pressure|tight|heav)", "chest pain or pressure"),
    (r"pain (in|down|to) (my )?(left |right )?(arm|jaw|shoulder)", "pain spreading to the arm or jaw"),
    (r"can'?t breathe|cannot breathe|struggling to breathe|gasping|fighting for (air|breath)", "difficulty breathing"),
    (r"short(ness)? of breath (at rest|even resting)|breathless (at rest|doing nothing)", "breathlessness at rest"),
    (r"face (is )?droop|slurred speech|can'?t speak|cannot speak|sudden confusion", "possible stroke signs"),
    (r"(sudden )?weak(ness)? (on |down )?one side|numb (on|down) one side|one side of my body", "sudden one-sided weakness"),
    (r"(heavy|severe|profuse|won'?t stop|wont stop) bleeding|bleeding (a lot|heavily|non ?stop)", "severe bleeding"),
    (r"unconscious|passed out|fainted|blacked out|collapsed", "loss of consciousness"),
    (r"seizure|convulsion|fitting|fits", "seizure"),
    (r"cough(ing)? (up )?blood|vomit(ing)? blood|blood in (my )?(vomit|stool|urine)", "bleeding"),
    (r"stiff neck", "stiff neck"),
    (r"(throat|face|tongue|lip)s? (is |are )?swell|swollen (throat|tongue|face)", "swelling of the face or throat"),
    (r"worst (pain|headache) of my life|thunderclap", "sudden severe pain"),
    (r"severe abdominal pain|rigid (stomach|abdomen)", "severe abdominal pain"),
    (r"head injury|hit my head", "head injury"),
    (r"blue lips|turning blue|lips are blue", "blue lips or skin"),
    (r"rash that (does ?n'?t|doesnt|does not) fade", "a rash that does not fade under pressure"),
    (r"not (waking|responding)|unresponsive", "unresponsiveness"),
]

CRISIS = [r"kill myself", r"suicid", r"end my life", r"want to die", r"take my own life",
          r"harm myself", r"hurt myself", r"self[- ]?harm", r"no reason to live"]

DRUGS = re.compile(
    r"\b(paracetamol|acetaminophen|panadol|calpol|tylenol|"
    r"ibuprofen|brufen|advil|nurofen|naproxen|diclofenac|"
    r"aspirin|disprin|codeine|tramadol|morphine|"
    r"amoxicillin|augmentin|azithromycin|ciprofloxacin|cephalexin|antibiotic|"
    r"omeprazole|ranitidine|prednisolone|dexamethasone|steroid|"
    r"cetirizine|loratadine|chlorpheniramine|"
    r"\d+\s?mg\b|\d+\s?ml\b|\d+\s?tablets?\b|twice a day|three times a day)",
    re.IGNORECASE,
)

SYSTEM = f"""You are a careful health-information assistant for a public website in Pakistan. You are NOT a doctor.

HARD RULES — breaking any is a failure:
1. NEVER write the name of any medicine, drug, brand or dose. Not paracetamol, not anything. Medicine guidance is handled elsewhere by a reviewed table; your job is only to choose a category key.
2. NEVER state a diagnosis as fact. Write "this pattern can be caused by", never "you have".
3. Every answer ends at a clinician.

Return ONLY valid JSON, no markdown fences:
{{
  "summary": "2-3 calm plain sentences reflecting what they described",
  "severity": "mild" | "moderate" | "see_doctor_soon",
  "possible_causes": [
    {{"name": "Common cold", "why": "one sentence on why their description fits", "likelihood": "common"|"less common"|"uncommon"}}
  ],
  "self_care": ["4-6 specific NON-MEDICINE actions"],
  "avoid": ["3-4 things to avoid"],
  "red_flags": ["4-5 specific signs meaning see a doctor sooner"],
  "expected_course": "one sentence on how long this usually takes to settle",
  "otc_keys": ["choose 1-2 ONLY from this exact list: {', '.join(ALLOWED_KEYS)}"]
}}

Give 2-4 possible causes, most likely first. Simple words. Reassuring when mild, clear without alarming when not."""


# ── models ────────────────────────────────────────────────────────────────
class TriageIn(BaseModel):
    age: int = Field(..., ge=1, le=119)
    sex: Optional[str] = ""
    duration: Optional[str] = ""
    symptoms: str = Field(..., min_length=8, max_length=1500)
    conditions: Optional[List[str]] = []


# ── helpers ───────────────────────────────────────────────────────────────
def scrub(obj):
    if isinstance(obj, str):
        return DRUGS.sub("[see the pharmacy note below]", obj)
    if isinstance(obj, list):
        return [scrub(x) for x in obj]
    if isinstance(obj, dict):
        return {k: scrub(v) for k, v in obj.items()}
    return obj


def screen(text: str):
    low = " ".join(text.lower().split())
    for p in CRISIS:
        if re.search(p, low):
            return "crisis", None
    for p, reason in RED_FLAGS:
        if re.search(p, low):
            return "emergency", reason
    return None, None


def fallback(age: int) -> dict:
    return {
        "summary": "Here is general guidance. The detailed assessment is unavailable right now, "
                   "but the safety checks below still apply.",
        "severity": "moderate",
        "possible_causes": [{
            "name": "Needs assessment by a clinician",
            "why": "Symptoms overlap across many conditions and cannot be separated from a description alone.",
            "likelihood": "common",
        }],
        "self_care": ["Rest and let your body recover.",
                      "Drink fluids steadily through the day.",
                      "Note your symptoms and when they change.",
                      "Check your temperature morning and evening."],
        "avoid": ["Strenuous activity", "Smoky rooms", "Taking anything without asking a pharmacist"],
        "red_flags": ["Symptoms getting worse rather than better",
                      "A high fever that will not come down",
                      "Any trouble breathing",
                      "Symptoms lasting more than a week"],
        "expected_course": "Most mild illness settles within a week.",
        "otc_keys": ["rest_only"],
    }


async def ask_model(payload: TriageIn) -> dict:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return fallback(payload.age)

    conditions = ", ".join(payload.conditions or []) or "none stated"
    user = (f"Age: {payload.age}\nSex: {payload.sex or 'not stated'}\n"
            f"Duration: {payload.duration or 'not stated'}\n"
            f"Existing conditions: {conditions}\n"
            f"They describe: {payload.symptoms}")

    async with httpx.AsyncClient(timeout=45) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": os.environ.get("SEHAT_MODEL", "openai/gpt-oss-120b"),
                "messages": [{"role": "system", "content": SYSTEM},
                             {"role": "user", "content": user}],
                "temperature": 0.3,
                "max_tokens": 1200,
            },
        )
        r.raise_for_status()
        raw = r.json()["choices"][0]["message"]["content"].strip()
    raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


# ── routes ────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"ok": True, "ai_enabled": bool(os.environ.get("GROQ_API_KEY", "").strip())}


@app.post("/api/triage")
async def triage(body: TriageIn):
    kind, reason = screen(body.symptoms)

    if kind == "crisis":
        return {
            "band": "crisis",
            "headline": "Please talk to someone today",
            "message": ("What you have written suggests you may be carrying something very "
                        "heavy. You deserve support from a person, not a website."),
            "actions": [
                "Tell someone you trust today — a family member, a friend, your doctor.",
                "In Pakistan: Umang 0311-7786264, or Rozan 0304-1111741.",
                "If you are in immediate danger, go to the nearest emergency department.",
            ],
            "note": "This site cannot provide crisis care, and will not try to.",
        }

    if kind == "emergency":
        return {
            "band": "emergency",
            "headline": "Get medical help now",
            "reason": reason,
            "message": (f"You mentioned {reason}. That can signal something serious that needs "
                        "checking immediately — not later today."),
            "actions": [
                "Go to the nearest emergency department now, or call Rescue 1122.",
                "Do not drive yourself — have someone take you.",
                "If it worsens while waiting, call again.",
            ],
            "note": "This is an automated safety check, not a diagnosis. Treat it as a reason to be seen urgently.",
        }

    try:
        data = await ask_model(body)
    except json.JSONDecodeError:
        data = fallback(body.age)
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            {"error": "assistant_unavailable",
             "detail": f"The guidance service returned {e.response.status_code}. Check the API key."},
            status_code=503)
    except Exception as e:
        return JSONResponse({"error": "assistant_unavailable", "detail": str(e)[:150]}, status_code=503)

    data = scrub(data)
    data["pharmacy"] = lookup(data.get("otc_keys"))
    data.pop("otc_keys", None)

    notes = []
    if body.age < 5:
        notes.append("Young children can worsen quickly — see a doctor sooner rather than waiting.")
    if body.age >= 65:
        notes.append("Over 65, symptoms are often milder than the underlying problem. Do not wait it out.")
    if body.conditions:
        notes.append("You mentioned an existing condition — mention it to the pharmacist, it changes what is safe.")

    data.update({
        "band": "guidance",
        "age_notes": notes,
        "dose_notice": ("No dose is shown anywhere on this page, on purpose. The right amount depends on "
                        "your weight, age, kidney and liver function, pregnancy, and everything else you "
                        "take. Your pharmacist can check all of that in two minutes, free, without an "
                        "appointment. Ask them before taking anything."),
        "disclaimer": ("General health information — not a diagnosis, not a prescription, and not a "
                       "substitute for being examined. See a qualified doctor for diagnosis and treatment."),
    })
    return data


app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
