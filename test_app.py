"""
SEHAT test suite - runs fully offline in demo mode (no API key needed).

    python test_app.py
"""

import os

for _k in ("ANTHROPIC_API_KEY", "GROQ_API_KEY", "LLM_PROVIDER", "MODEL"):
    os.environ.pop(_k, None)  # force demo mode for tests

from fastapi.testclient import TestClient  # noqa: E402

import safety  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)
PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


def start(**over):
    body = {"age": 30, "sex": "male", "pregnant": False,
            "complaint": "mild headache since yesterday", "duration": "1-3 days"}
    body.update(over)
    return client.post("/api/consult/start", json=body)


print("== health & static ==")
r = client.get("/api/health")
check("health ok / demo mode", r.status_code == 200 and r.json()["mode"] == "demo", r.text)
r = client.get("/")
check("index served", r.status_code == 200 and "SEHAT" in r.text)

print("== intake validation ==")
r = start(sex="female", pregnant=True, pregnancy_weeks=None)
check("pregnant without weeks rejected", r.status_code == 422, r.text[:120])
r = start(sex="female", pregnant=True, pregnancy_weeks=32,
          complaint="acidity after meals")
check("pregnant with weeks accepted -> question",
      r.status_code == 200 and r.json()["type"] == "question", r.text[:120])

print("== emergency screen (deterministic, before AI) ==")
r = start(complaint="my father suddenly became unconscious and is not waking up")
j = r.json()
check("unconscious -> emergency", j.get("type") == "emergency", str(j)[:120])
check("emergency includes first-aid steps",
      bool(j.get("protocol", {}).get("steps")))
check("emergency includes until-hospital guidance",
      bool(j.get("protocol", {}).get("until_hospital")))

r = start(complaint="abbu behosh ho gaye hain")
check("Roman Urdu 'behosh' -> emergency", r.json().get("type") == "emergency")

r = start(complaint="road accident hua hai, bohat khoon beh raha hai")
check("accident (Roman Urdu) -> emergency", r.json().get("type") == "emergency")

r = start(complaint="I have no chest pain, just a mild cough for two days")
check("negated chest pain does NOT trigger", r.json().get("type") == "question",
      str(r.json())[:120])

r = start(complaint="don't mind my typing, my father's speech is suddenly slurred")
check("polite 'don't mind' whitelist still catches stroke",
      r.json().get("type") == "emergency", str(r.json())[:120])

r = start(complaint="chst pian and pressure with sweating")  # typo fuzz
check("typo 'chst pian' still catches cardiac",
      r.json().get("type") == "emergency", str(r.json())[:120])

print("== pregnancy-profile-aware red flags ==")
r = start(sex="female", pregnant=True, pregnancy_weeks=32,
          complaint="baby not moving since morning")
check("32w reduced movements -> pregnancy emergency",
      r.json().get("type") == "emergency" and
      r.json().get("protocol", {}).get("id") == "pregnancy_emergency",
      str(r.json())[:160])
r = start(sex="female", pregnant=True, pregnancy_weeks=8,
          complaint="baby not moving since morning")
check("8w movement worry does NOT hard-trigger (too early to feel)",
      r.json().get("type") == "question", str(r.json())[:120])

print("== crisis routing ==")
r = start(complaint="i dont want to live anymore")
j = r.json()
check("crisis -> helplines", j.get("type") == "crisis" and j.get("helplines"))
check("Umang number present", any("0311" in h["number"] for h in j.get("helplines", [])))

print("== full demo consultation ==")
r = start(complaint="stomach pain after eating")
j = r.json()
sid = j["session_id"]
check("start -> first question", j["type"] == "question" and j["progress"]["asked"] == 1)
answers = ["Today, gradually", "4-6 moderate", "None of these",
           "worse after spicy food", "None", "First time"]
last = None
for a in answers:
    last = client.post("/api/consult/answer",
                       json={"session_id": sid, "answer": a}).json()
check("history complete -> assessment", last and last.get("type") == "assessment",
      str(last)[:160])
a = last["assessment"]
check("assessment has disclaimer", "not a medical diagnosis" in a.get("disclaimer", ""))
check("assessment routes to specialist",
      a.get("see_doctor", {}).get("who", "").startswith("Gastro"), str(a.get("see_doctor")))
check("assessment carries patient line", bool(a.get("patient_line")))

print("== mid-consultation safety ==")
r = start(complaint="feeling a bit dizzy since morning")
sid = r.json()["session_id"]
j = client.post("/api/consult/answer",
                json={"session_id": sid,
                      "answer": "now I have chest pressure and I am sweating a lot"}).json()
check("mid-flow emergency caught", j.get("type") == "emergency", str(j)[:120])

r = start(complaint="trouble sleeping lately")
sid = r.json()["session_id"]
j = client.post("/api/consult/answer",
                json={"session_id": sid,
                      "answer": "what dose of xanax should i take for this"}).json()
check("prescription dose guard fires", j.get("type") == "guard", str(j)[:120])

print("== first aid library ==")
r = client.get("/api/firstaid")
j = r.json()
check("protocol list >= 18", len(j.get("protocols", [])) >= 18, str(len(j.get("protocols", []))))
r = client.get("/api/firstaid/fracture")
j = r.json()
check("fracture protocol has splint step",
      any("bind" in s.lower() for s in j.get("steps", [])))
r = client.get("/api/firstaid/nope")
check("unknown protocol -> 404", r.status_code == 404)

print("== OTC pregnancy filter ==")
full = client.get("/api/otc").json()["medicines"]
preg = client.get("/api/otc", params={"pregnant": True}).json()["medicines"]
check("full table has ibuprofen", any("Ibuprofen" in m["name"] for m in full))
check("pregnant table excludes ibuprofen",
      not any("Ibuprofen" in m["name"] for m in preg))
check("pregnant table keeps paracetamol",
      any("Paracetamol" in m["name"] for m in preg))

print("== output scrubber ==")
s = safety.scrub_text("Take tramadol 100 mg tonight and rest.")
check("rx dose scrubbed", "100 mg" not in s and "ask your doctor" in s, s)

print()
print(f"RESULT: {PASS} passed, {FAIL} failed")
raise SystemExit(1 if FAIL else 0)
