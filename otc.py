"""
Curated over-the-counter reference.

WHY THIS IS A STATIC FILE AND NOT LLM OUTPUT
--------------------------------------------
A language model asked "what should I take for a fever" will happily produce a
drug name and a dose. That is the single most dangerous thing this app could do:

  * Antibiotics are sold without prescription in Pakistan. A model that suggests
    them drives resistance and treats viral illness with something useless.
  * Paracetamol overdose is a leading cause of acute liver failure worldwide.
  * Ibuprofen is unsafe in late pregnancy, in kidney disease, with stomach
    ulcers, and alongside several common blood-pressure medicines.
  * Aspirin can cause Reye's syndrome in children.

So the medicine layer is a fixed table written by hand, reviewed once, and
identical for every user. The model never chooses it — it only picks a category
key from a closed list, and if it picks something not in this file, nothing is
shown.

DELIBERATE OMISSIONS
  * No doses. Dose depends on weight, age, kidney and liver function.
  * No prescription-only medicines, ever.
  * No antibiotics, ever.
Every entry ends at a pharmacist, who is free to consult and needs no appointment.
"""

# key -> guidance. Keys are the closed list the model must choose from.
OTC_GUIDE = {
    "fever_pain": {
        "category": "Simple fever and pain reliever",
        "common_names": "Paracetamol (also sold as acetaminophen)",
        "what_it_does": "Brings a temperature down and eases aches. It treats how you feel, not the cause.",
        "who_must_not": [
            "Anyone with liver disease, or who drinks alcohol heavily",
            "Anyone already taking a combination cold remedy — most already contain it, and doubling up is the most common cause of accidental overdose",
        ],
        "ask_pharmacist": "Confirm the right amount for your weight and age, and check nothing else you take already contains it.",
    },
    "inflammation": {
        "category": "Anti-inflammatory pain reliever",
        "common_names": "Ibuprofen (the NSAID group)",
        "what_it_does": "Reduces swelling and inflammatory pain — sprains, period pain, dental pain.",
        "who_must_not": [
            "Anyone pregnant, especially after 20 weeks",
            "Anyone with stomach ulcers, acid reflux or a history of stomach bleeding",
            "Anyone with kidney disease, heart failure, or on blood-pressure or blood-thinning medicines",
            "Anyone with asthma that worsens with painkillers",
        ],
        "ask_pharmacist": "This group has more restrictions than most people realise. Confirm it is safe for you before taking any.",
    },
    "cough_cold": {
        "category": "Soothing measures for cough and congestion",
        "common_names": "Steam inhalation, saline nasal rinse, honey in warm water (not for infants under 1 year)",
        "what_it_does": "Loosens congestion and soothes an irritated throat while a viral illness runs its course.",
        "who_must_not": [
            "Never give honey to a baby under one year old — risk of infant botulism",
            "Cough syrups are not recommended for young children; ask a pharmacist first",
        ],
        "ask_pharmacist": "Most coughs and colds are viral and get better on their own. Antibiotics do nothing for them and cause harm when overused.",
    },
    "allergy": {
        "category": "Antihistamine for allergy symptoms",
        "common_names": "The non-drowsy antihistamine group",
        "what_it_does": "Eases sneezing, itching, watery eyes and hives caused by an allergic reaction.",
        "who_must_not": [
            "Anyone with glaucoma, an enlarged prostate, or liver or kidney disease should check first",
            "Some older types cause heavy drowsiness — do not drive after taking them",
        ],
        "ask_pharmacist": "If your face, lips or throat are swelling, or you are wheezing, that is an emergency — not something to treat at the counter.",
    },
    "stomach": {
        "category": "Rehydration and stomach settling",
        "common_names": "Oral rehydration salts (ORS)",
        "what_it_does": "Replaces the water and salts lost through vomiting or diarrhoea. This matters far more than stopping the symptom.",
        "who_must_not": [
            "Anti-diarrhoea medicines should be avoided if there is blood in the stool or a high fever — they can trap infection",
            "Young children and older adults dehydrate quickly and need to be seen sooner",
        ],
        "ask_pharmacist": "ORS is the priority. Ask before taking anything that stops diarrhoea.",
    },
    "skin": {
        "category": "Gentle skin care",
        "common_names": "Plain emollient or moisturiser, cool compress",
        "what_it_does": "Calms irritation and protects the skin barrier while it settles.",
        "who_must_not": [
            "Do not use steroid creams on the face or on broken skin without advice",
            "A rash with fever, or one that does not fade when pressed with a glass, needs urgent medical attention",
        ],
        "ask_pharmacist": "Describe the rash — location and how it changed — so they can tell whether it needs a doctor.",
    },
    "rest_only": {
        "category": "No medicine indicated",
        "common_names": "Rest, fluids, and time",
        "what_it_does": "Most mild illness settles on its own. Medicine would add risk without adding benefit.",
        "who_must_not": [],
        "ask_pharmacist": "If it has not started improving in the expected time, that is the signal to see a doctor.",
    },
}

ALLOWED_KEYS = list(OTC_GUIDE.keys())


def lookup(keys):
    """Return curated entries for model-chosen keys. Unknown keys are dropped."""
    out = []
    seen = set()
    for k in keys or []:
        k = str(k).strip().lower()
        if k in OTC_GUIDE and k not in seen:
            seen.add(k)
            out.append({"key": k, **OTC_GUIDE[k]})
    return out[:3]
