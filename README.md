# SEHAT — Understand your symptoms. Then see your doctor.

A doctor-style health consultation and first-aid web app for Pakistan. Runs on
**Groq** (free tier) or **Anthropic Claude** — whichever key you provide.

SEHAT works the way a good physician works:

1. **Basics first** — age, sex, and if pregnant, **exactly how many weeks** (this changes
   what's safe, what's urgent, and what the possibilities even are).
2. **History taking** — one focused question at a time (onset, severity, associated
   symptoms, triggers, past history, medicines), like a real OPD consultation.
3. **Assessment** — a clinical-summary "prescription pad": what the symptoms **may** be
   (with honest likelihoods and reasoning), red flags, precautions, safe self-care,
   over-the-counter options only, which specialist to see and how urgently, plus
   questions to ask at the visit. Printable — literally made to take to your doctor.
4. **Emergencies** — a deterministic safety screen runs **before and during** every
   consultation. Unconsciousness, chest pain patterns, stroke signs, heavy bleeding,
   accidents, seizures, snake bite, pregnancy emergencies (Roman Urdu included:
   *behosh*, *saans nahi aa rahi*, *khoon ruk nahi raha*, *daura*) jump straight to
   step-by-step first aid — what to do now, what never to do, and what to keep doing
   **until you reach the hospital** — with one-tap calls to Rescue 1122 / Edhi 115.

> **What SEHAT is not.** It is information and preparation — not a diagnosis, and not
> a substitute for a qualified doctor. No AI (and no doctor, without examining you)
> can promise a correct diagnosis from text alone. SEHAT's job is to make you an
> informed patient and get you to the right doctor at the right speed.

---

## Quick start

```bash
python -m venv venv
venv\Scripts\activate          # Windows   (source venv/bin/activate on Linux/Mac)
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://127.0.0.1:8000

Without an API key the app runs in **demo mode**: emergency screening, all 20 first-aid
protocols and the medicine table are fully functional; the consultation asks a generic
scripted history and returns a clearly-labelled demo summary.

## Connect an AI provider

SEHAT supports **Groq** (free tier, no credit card) and **Anthropic**. It auto-detects
whichever key you set.

**Groq (free) — recommended for testing:**

```powershell
$env:GROQ_API_KEY="gsk_..."          # get it from console.groq.com
$env:MODEL="llama-3.3-70b-versatile" # optional, this is the default
python run.py
```

**Anthropic (Claude Fable 5):**

```powershell
$env:ANTHROPIC_API_KEY="sk-ant-..."
$env:MODEL="claude-fable-5"
python run.py
```

**Or use a config file:** copy `data/config.example.json` to `data/config.json` and paste
your key there. That file is gitignored — never commit it.

Free Groq models worth trying: `llama-3.3-70b-versatile` (best reasoning),
`llama-3.1-8b-instant` (fastest, highest daily limit), `qwen/qwen3-32b`.
Anthropic models: `claude-fable-5`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`.

> Note on quality: the safety layers (emergency detection, dose guard, OTC allow-list,
> pregnancy filtering) are deterministic Python and work identically on any provider.
> The model only affects the *quality of the clinical reasoning* — Claude reasons better
> on complex cases, Groq is free and fast. Both are safe to run.

## Deploy on Render

Push to GitHub, then **New → Blueprint** and point it at this repo — `render.yaml`
does the rest (Singapore region, free plan). Add `GROQ_API_KEY` (or `ANTHROPIC_API_KEY`) in the
environment settings when prompted. Free tier sleeps when idle; the first request
after a sleep takes ~30–50 s.

## Tests

```bash
python test_app.py
```

30 offline checks: pregnancy-weeks validation, English + Roman Urdu emergency
triggers, typo tolerance ("chst pian"), negation ("no chest pain" must NOT trigger,
"don't mind… speech slurred" MUST), pregnancy-aware red flags gated by gestational
week, crisis routing, prescription-dose guard, OTC pregnancy filtering, the full
demo consultation, and the output scrubber.

## Safety architecture (defense in depth)

| Layer | What it does |
|---|---|
| Emergency screen | Deterministic, runs on the complaint **and every message** — before any AI call. Fuzzy-matched, negation-aware, EN + Roman Urdu. |
| Pregnancy gating | Weeks are required at intake. Reduced-movement triggers activate ≥26 weeks; preeclampsia signs ≥20 weeks. Pregnancy-unsafe OTC medicines are filtered out server-side. |
| Crisis routing | Self-harm language routes to Umang (0311-7786264, 24/7, free) and 1122 — never to a symptom flow. |
| Dose guard | Questions about prescription-medicine doses (sedatives, antibiotics, opioids, abortion medicines) are refused and routed to a doctor/pharmacist. |
| OTC allow-list | The AI may only suggest 7 curated over-the-counter items; anything else it names is stripped server-side and its curated label-dose text is substituted. |
| Output scrubber | Any prescription drug + dose pattern in AI output is replaced with "(dose: ask your doctor)". |
| Framing | Every assessment carries the disclaimer and a specific route to a real doctor. |

## Project layout

```
main.py        FastAPI app + validation (pregnancy_weeks required when pregnant)
consult.py     consultation engine: sessions, JSON contract, demo mode, post-processing
prompts.py     the "doctor brain" system prompt + assessment schema
llm.py         LLM client - Groq (free) or Anthropic, auto-detected
safety.py      emergency/crisis screens, dose guard, scrubber
firstaid.py    20 step-by-step protocols incl. "until you reach the hospital"
otc.py         curated OTC table with pregnancy flags
static/        frontend (vanilla JS single-page app)
test_app.py    offline test suite
```
