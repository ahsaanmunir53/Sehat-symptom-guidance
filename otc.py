"""
Curated over-the-counter reference table.

This is the ONLY set of medicines SEHAT is allowed to suggest.
Doses are the standard adult label doses. Everything prescription-only
is refused by design and routed to a doctor or pharmacist.

Each entry carries a pregnancy flag so the app can filter suggestions
the moment the patient says she is pregnant.
"""

OTC_TABLE = [
    {
        "key": "paracetamol",
        "name": "Paracetamol 500 mg (e.g. Panadol, Calpol)",
        "use": "Fever, headache, body aches, pain",
        "adult": "1-2 tablets every 6 hours when needed. Maximum 8 tablets (4 g) in 24 hours.",
        "pregnancy_safe": True,
        "preg_note": "First-choice pain and fever medicine in pregnancy at normal doses.",
        "cautions": "Never exceed the daily maximum - overdose silently damages the liver. Liver disease: ask a doctor first.",
    },
    {
        "key": "ors",
        "name": "ORS (oral rehydration salts, e.g. Nimkol)",
        "use": "Diarrhoea, vomiting, dehydration, heat exhaustion",
        "adult": "Dissolve one sachet in the exact amount of clean water written on it. Sip frequently; one glass after each loose motion.",
        "pregnancy_safe": True,
        "preg_note": "Safe and especially important in pregnancy - dehydration harms mother and baby.",
        "cautions": "Use the exact water amount on the packet - too concentrated makes diarrhoea worse.",
    },
    {
        "key": "antacid",
        "name": "Antacid / alginate (e.g. Gaviscon, Mucaine)",
        "use": "Acidity, heartburn, reflux",
        "adult": "As per pack, usually after meals and at bedtime.",
        "pregnancy_safe": True,
        "preg_note": "Alginate and simple antacid types are commonly used for pregnancy heartburn.",
        "cautions": "Heartburn every day for weeks, difficulty swallowing, or black stools need a doctor.",
    },
    {
        "key": "cetirizine",
        "name": "Cetirizine 10 mg (e.g. Zyrtec, T-Day)",
        "use": "Allergy, sneezing, itching, hives",
        "adult": "1 tablet once daily. Can cause drowsiness.",
        "pregnancy_safe": False,
        "preg_note": "In pregnancy, take antihistamines only if your doctor agrees.",
        "cautions": "Avoid driving if it makes you drowsy. Not for throat-swelling reactions - that is an emergency.",
    },
    {
        "key": "ibuprofen",
        "name": "Ibuprofen 200-400 mg (e.g. Brufen)",
        "use": "Pain with inflammation (sprains, toothache, period pain)",
        "adult": "200-400 mg every 6-8 hours WITH food. Maximum 1200 mg per day without a doctor.",
        "pregnancy_safe": False,
        "preg_note": "Avoid in pregnancy - it is specifically dangerous after 20 weeks. Use paracetamol instead.",
        "cautions": "Avoid with stomach ulcers, kidney problems, aspirin allergy, or on an empty stomach.",
    },
    {
        "key": "loperamide",
        "name": "Loperamide (e.g. Imodium)",
        "use": "Simple adult diarrhoea (travel, mild upset)",
        "adult": "2 capsules first, then 1 after each loose motion. Maximum 8 mg per day, 2 days only.",
        "pregnancy_safe": False,
        "preg_note": "Avoid in pregnancy - use ORS and see a doctor if it continues.",
        "cautions": "NEVER with fever or blood in the stool - that needs a doctor. Not for children.",
    },
    {
        "key": "calamine",
        "name": "Calamine lotion",
        "use": "Itchy rashes, insect bites, prickly heat",
        "adult": "Apply a thin layer on the itchy area 2-3 times daily.",
        "pregnancy_safe": True,
        "preg_note": "Safe on the skin in pregnancy.",
        "cautions": "Broken, weeping or spreading skin needs a doctor, not lotion.",
    },
]


def allowed_names():
    return [o["name"] for o in OTC_TABLE]


def allowed_keys():
    return [o["key"] for o in OTC_TABLE]


def table(pregnant: bool = False):
    if not pregnant:
        return OTC_TABLE
    return [o for o in OTC_TABLE if o["pregnancy_safe"]]


def match(name: str):
    """Return the curated entry whose key appears in a free-text name."""
    low = (name or "").lower()
    for o in OTC_TABLE:
        if o["key"] in low:
            return o
    return None
