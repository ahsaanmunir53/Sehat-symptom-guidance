# SEHAT — symptom guidance

Describe how you feel in plain words. Get back what it could be, what helps,
what to avoid, when to see a doctor, and what's available at the pharmacy counter.

**Not a doctor. Does not prescribe. Shows no doses, ever.**

---

## Run it

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open **http://127.0.0.1:8000**

To enable the AI guidance, create a file named `.env` — or just set it in your shell:

```powershell
$env:GROQ_API_KEY="gsk_your_key_here"
uvicorn app:app --reload
```

Free key at **console.groq.com**. Without it the app still runs: safety screening
and the pharmacy table are plain Python, so nothing appears broken.

## Deploy

Push to GitHub → Render → **New + → Blueprint** → pick the repo → paste
`GROQ_API_KEY` → Apply. Single service, no build step for the frontend.

---

## How safety is built

The language model is the only untrusted part, and it sits **between two
deterministic gates**:

```
validate → crisis screen → red-flag screen → [ MODEL ] → drug scrub → curated pharmacy table
```

**1. Emergency screening runs before the model is ever called.**
Chest pain, stroke signs, breathing difficulty, severe bleeding and a dozen other
patterns return "get help now" from plain regex. A language model never gets a
vote on whether a heart attack is urgent.

**2. The model is forbidden from naming any medicine**, and a regex strips drug
names and doses from its output anyway. Prompts can be jailbroken; the filter cannot.

**3. Medicine guidance is a hand-written table** (`otc.py`), not model output.
The model may only choose a *category key* from a closed list of seven. Anything
outside that list is dropped. This exists because:

- Antibiotics are sold over the counter in Pakistan — a model that suggests them
  drives resistance and treats viral illness with something useless.
- Paracetamol overdose is a leading cause of acute liver failure.
- Ibuprofen is unsafe in late pregnancy, kidney disease, and with several common
  blood-pressure medicines.

**4. No dose appears anywhere**, by design. Dose depends on weight, age, kidney
and liver function, pregnancy and interactions. Every entry routes to a
pharmacist — free, no appointment, legally able to advise.

**5. Self-harm language routes to crisis support**, not triage, with real
Pakistani helplines.

---

## API

| Method | Route | |
|---|---|---|
| `GET` | `/api/health` | is the service up, is AI enabled |
| `POST` | `/api/triage` | `{age, sex, duration, symptoms, conditions[]}` |
| `GET` | `/api/docs` | interactive OpenAPI docs |

Response bands: `emergency` · `crisis` · `guidance`.

---

## Stack

FastAPI + vanilla JS frontend. No build step deliberately — no node_modules,
no bundler, nothing to break on deploy. Deploys as one service in about a minute.
