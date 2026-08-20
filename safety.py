"""
SEHAT safety layer.

Deterministic screens that run BEFORE and AFTER the AI:
  1. emergency screen  - detects life-threatening situations (EN + Roman Urdu),
                         with typo tolerance and negation awareness
  2. crisis screen     - self-harm routing to human help
  3. dose guard        - blocks prescription-medicine dosing questions
  4. scrub             - strips prescription doses from AI output

Lessons baked in from the SEHAT adversarial eval harness:
  - negation is token-scoped, with a whitelist for polite formulas
    ("don't mind", "don't worry") that deny nothing clinical
  - fuzzy matching is first-letter-anchored Damerau-Levenshtein <= 1,
    so "chst pian" matches but "wanted" never matches "fainted"
  - spaced-out letters ("f i t s") are collapsed before matching
"""

import re
import unicodedata

# ---------------------------------------------------------------- normalize

_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
                       "7": "t", "8": "b", "@": "a", "$": "s", "!": "i"})


def normalize(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "").lower()
    t = t.replace("'", "").replace("\u2019", "")  # don't -> dont (one token)
    t = t.translate(_LEET)
    # collapse spaced-out letters:  "f i t s" -> "fits"
    t = re.sub(r"\b(?:[a-z] ){2,}[a-z]\b", lambda m: m.group(0).replace(" ", ""), t)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# ------------------------------------------------------------- fuzzy match

def _dl1(a: str, b: str) -> bool:
    """True if Damerau-Levenshtein distance <= 1."""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        # substitution or adjacent transposition
        diff = [i for i in range(la) if a[i] != b[i]]
        if len(diff) == 1:
            return True
        if len(diff) == 2 and diff[1] == diff[0] + 1:
            i = diff[0]
            return a[i] == b[i + 1] and a[i + 1] == b[i]
        return False
    # insertion/deletion
    if la > lb:
        a, b = b, a
        la, lb = lb, la
    i = j = 0
    skipped = False
    while i < la and j < lb:
        if a[i] == b[j]:
            i += 1
            j += 1
        elif not skipped:
            skipped = True
            j += 1
        else:
            return False
    return True


def _tok_match(word: str, target: str) -> bool:
    if word == target:
        return True
    # fuzzy only for longer words, anchored on the first letter -
    # people mistype the middle of a word, not its start
    if len(target) >= 5 and len(word) >= 4 and word[0] == target[0]:
        return _dl1(word, target)
    return False


# --------------------------------------------------------------- negation

_NEGATORS = {"no", "not", "dont", "don", "never", "without", "nahi", "nahin",
             "nai", "nhi", "deny", "denies", "koi"}
# polite formulas that deny nothing clinical (the "don't mind" bug)
_NEG_WHITELIST = {"mind", "worry", "know", "sure", "think", "panic", "problem"}


def _negated(tokens, idx, window=3):
    for j in range(max(0, idx - window), idx):
        if tokens[j] in _NEGATORS:
            if j + 1 < len(tokens) and tokens[j + 1] in _NEG_WHITELIST:
                continue
            return True
    return False


def _find_phrase(tokens, phrase):
    """Yield start indices of non-negated occurrences of phrase in tokens."""
    p = phrase.split()
    n, m = len(tokens), len(p)
    for i in range(n - m + 1):
        if all(_tok_match(tokens[i + k], p[k]) for k in range(m)):
            if not _negated(tokens, i):
                yield i


def _hit(tokens, phrases) -> bool:
    return any(True for ph in phrases for _ in _find_phrase(tokens, ph))


# ------------------------------------------------------- emergency ruleset

# any  : one non-negated phrase fires the rule
# all  : every group must have at least one non-negated phrase (co-occurrence)
EMERGENCY_RULES = [
    dict(id="not_breathing", label="Not breathing", protocol="cpr",
         any=["not breathing", "stopped breathing", "no pulse", "only gasping",
              "saans ruk gayi", "saans nahi le raha", "saans nahi le rahi",
              "saans band"]),
    dict(id="unconscious", label="Unconscious / not responding", protocol="unconscious",
         any=["unconscious", "unresponsive", "behosh", "behosh ho gaya",
              "behosh ho gayi", "not waking up", "wont wake up", "passed out",
              "collapsed suddenly", "fainted and not waking", "hosh nahi"]),
    dict(id="breathing", label="Severe breathing difficulty", protocol="breathing",
         any=["cant breathe", "can not breathe", "cannot breathe",
              "difficulty breathing", "struggling to breathe", "gasping for air",
              "lips turning blue", "blue lips", "saans lene mein mushkil",
              "saans nahi aa rahi", "saans nahi aa raha", "wheezing badly",
              "severe asthma attack"]),
    dict(id="choking", label="Choking", protocol="choking",
         any=["choking", "cant cough", "food stuck cant breathe",
              "gala atak gaya", "sans atak", "something stuck in my throat cant"]),
    dict(id="cardiac", label="Possible heart attack", protocol="heart_attack",
         all=[["chest", "seenay", "seene", "sinay", "chhati"],
              ["pain", "pressure", "tight", "tightness", "heavy", "heaviness",
               "squeezing", "crushing", "dard", "bhari", "bojh"]]),
    dict(id="stroke", label="Possible stroke", protocol="stroke",
         any=["face drooping", "face droop", "slurred speech", "speech slurred",
              "speech is slurred", "suddenly cant speak", "one side weak",
              "weakness on one side", "arm suddenly weak", "face suddenly numb",
              "sudden numbness one side", "chehra ter ho gaya",
              "zuban laraz rahi", "aik taraf kamzori", "worst headache of my life"]),
    dict(id="stroke_speech", label="Possible stroke", protocol="stroke",
         all=[["speech", "speak", "words", "zuban", "bolne"],
              ["slurred", "slurring", "slur", "jumbled", "laraz"]]),
    dict(id="bleeding", label="Severe bleeding", protocol="severe_bleeding",
         all=[["bleeding", "blood", "khoon", "bleed"],
              ["heavy", "heavily", "severe", "severely", "lot", "lots", "bohat",
               "wont stop", "not stopping", "spurting", "soaked", "soaking",
               "ruk nahi", "band nahi", "everywhere", "pouring"]]),
    dict(id="seizure", label="Seizure / fits", protocol="seizure",
         any=["seizure", "seizures", "convulsion", "convulsions", "fits",
              "fitting", "having a fit", "jhatke lag rahe", "daura par gaya",
              "daura par raha", "dora par gaya", "mirgi ka daura",
              "shaking uncontrollably", "jerking and not responding"]),
    dict(id="anaphylaxis", label="Severe allergic reaction", protocol="allergic_reaction",
         any=["throat closing", "throat is closing", "throat swelling",
              "tongue swelling", "tongue is swelling", "face swelling fast",
              "anaphylaxis", "gala band ho raha", "hives and cant breathe"]),
    dict(id="poisoning", label="Poisoning / overdose", protocol="poisoning",
         any=["swallowed poison", "drank poison", "poisoned", "overdose",
              "took too many pills", "took too many tablets", "zehar kha",
              "zeher kha", "zeher pi", "drank bleach", "drank kerosene",
              "mitti ka tel pi", "drank acid"]),
    dict(id="snake", label="Snake bite", protocol="snake_bite",
         any=["snake bit", "snake bite", "bitten by a snake", "bitten by snake",
              "saanp ne kata", "samp ne kata", "saanp ne kaat"]),
    dict(id="burn_major", label="Serious burn", protocol="burns",
         all=[["burn", "burns", "burnt", "burned", "jal", "jhulas", "scalded"],
              ["severe", "large", "big", "deep", "face", "whole", "boiling",
               "acid", "fire", "chemical", "electric", "gaya", "gayi", "gaye",
               "bura", "buri", "badly", "child"]]),
    dict(id="accident", label="Accident / major injury", protocol="road_accident",
         any=["road accident", "car accident", "bike accident", "car crash",
              "motorcycle accident", "hit by a car", "hit by car",
              "accident hua", "accident ho gaya", "fell from height",
              "fell from the roof", "fell off the roof", "chhat se gira",
              "chhat se gir"]),
    dict(id="fracture_bad", label="Broken bone", protocol="fracture",
         any=["bone sticking out", "open fracture", "bone broke through",
              "bone is broken", "broke my bone", "broken bone",
              "haddi toot gayi", "haddi toot gai", "fracture ho gaya",
              "leg bent the wrong way", "arm bent the wrong way"]),
    dict(id="electric", label="Electric shock", protocol="electric_shock",
         any=["electric shock", "electrocuted", "current laga", "current lag",
              "bijli ka jhatka"]),
    dict(id="drowning", label="Drowning", protocol="drowning",
         any=["drowning", "drowned", "nearly drowned", "pani mein doob",
              "pulled from the water not"]),
    dict(id="heatstroke", label="Heat stroke", protocol="heatstroke",
         any=["heat stroke", "heatstroke", "collapsed in the heat",
              "garmi se behosh", "loo lag gayi", "loo lag gai"]),
    dict(id="head", label="Serious head injury", protocol="head_injury",
         all=[["head", "sir", "sar", "skull"],
              ["injury", "hit hard", "bleeding", "vomiting after", "chot",
               "phat gaya", "cracked", "knocked out", "unconscious after"]]),
    dict(id="preg_general", label="Pregnancy emergency", protocol="pregnancy_emergency",
         all=[["pregnant", "pregnancy", "hamal", "hamila"],
              ["bleeding", "khoon", "water broke", "pani nikal", "fits",
               "daura", "seizure", "severe pain", "shadeed dard",
               "baby not moving", "no movement", "harkat nahi"]]),
]

# extra red flags that fire on their own when the patient is known pregnant
_PREG_ANY = ["heavy bleeding", "bleeding a lot", "bleeding heavily",
             "khoon aa raha", "khoon aa rha", "spotting a lot",
             "water broke", "pani nikal gaya", "pani nikal gya",
             "severe abdominal pain", "pait mein shadeed dard",
             "shadeed dard", "fits", "daura", "seizure"]
_PREG_MOVEMENT = ["baby not moving", "no fetal movement", "no movement",
                  "movement nahi", "harkat nahi", "baby is not moving",
                  "not felt the baby", "havent felt the baby",
                  "bachay ki harkat nahi"]
_PREG_PREECLAMPSIA = ["severe headache", "blurred vision", "nazar dhundla",
                      "dhundla nazar", "vision blurry", "seeing spots",
                      "flashing lights", "sar mein shadeed dard"]


def screen_emergency(text: str, profile: dict | None = None):
    """Return the first matching emergency rule, or None."""
    tokens = normalize(text).split()
    if not tokens:
        return None
    for rule in EMERGENCY_RULES:
        if "any" in rule and _hit(tokens, rule["any"]):
            return {k: rule[k] for k in ("id", "label", "protocol")}
        if "all" in rule and all(_hit(tokens, group) for group in rule["all"]):
            return {k: rule[k] for k in ("id", "label", "protocol")}
    p = profile or {}
    if p.get("pregnant"):
        weeks = int(p.get("pregnancy_weeks") or 0)
        preg = dict(id="preg_flag", label="Pregnancy emergency",
                    protocol="pregnancy_emergency")
        if _hit(tokens, _PREG_ANY):
            return preg
        if weeks >= 26 and _hit(tokens, _PREG_MOVEMENT):
            return preg
        if weeks >= 20 and _hit(tokens, _PREG_PREECLAMPSIA):
            return preg
    return None


# ----------------------------------------------------------------- crisis

# The form invites Roman Urdu — "English ya Roman Urdu, jaise aap bolte hain" —
# so the Roman Urdu side of this list has to be as thorough as the English one.
# A miss here routes someone in crisis into a symptom questionnaire instead of
# a helpline, so phrases are added generously. Showing crisis support to
# someone who did not need it costs almost nothing; the opposite does not.
#
# Single ambiguous words are deliberately absent. "khatam" alone is "finished"
# (dawai khatam ho gayi) and "maut" alone appears in ordinary fear-of-illness
# talk, so both only count inside a longer phrase.
_CRISIS = [
    # English
    "kill myself", "killing myself", "end my life", "ending my life",
    "end it all", "take my own life", "taking my own life", "suicide",
    "suicidal", "want to die", "i want to die", "wish i was dead",
    "wish i were dead", "dont want to live", "do not want to live",
    "no reason to live", "nothing to live for", "dont want to be here",
    "better off dead", "hurt myself", "harm myself", "self harm",
    "cut myself", "cutting myself", "overdose on",

    # Roman Urdu - ending one's life
    "khudkushi", "khud kushi", "khudkhushi", "khud khushi",
    "marna chahta", "marna chahti", "mar jana chahta", "mar jana chahti",
    "mar jaon", "mar jaun", "mar jaunga", "mar jaungi",
    "khud ko khatam", "apne aap ko khatam", "zindagi khatam",
    "khud ko maar", "khud ko marna", "apni jaan lena", "apni jaan le",
    "jaan de dun", "jaan dena chahta", "jaan dena chahti",

    # Roman Urdu - not wanting to live
    "jeena nahi chahta", "jeena nahi chahti", "ab nahi jeena",
    "jeene ka dil nahi", "jeene ko dil nahi", "zinda nahi rehna",
    "zindagi se tang", "jeene ka maza nahi",

    # Roman Urdu - method words, which signal intent on their own
    "zeher kha", "zeher pi", "phansi laga", "nas kaat", "nasein kaat",
    "goliyan kha lun", "apne aap ko nuksan", "khud ko nuksan",
]


def screen_crisis(text: str) -> bool:
    tokens = normalize(text).split()
    return bool(tokens) and _hit(tokens, _CRISIS)


# ------------------------------------------------------------- dose guard

_RX_DRUGS = ["xanax", "alprazolam", "valium", "diazepam", "lexotanil",
             "bromazepam", "tramadol", "tramal", "morphine", "codeine",
             "oxycodone", "fentanyl", "pethidine", "augmentin", "amoxicillin",
             "amoxil", "azithromycin", "azomax", "ciprofloxacin", "cipro",
             "flagyl", "metronidazole", "ceftriaxone", "rocephin", "antibiotic",
             "antibiotics", "warfarin", "insulin", "misoprostol", "cytotec",
             "mifepristone", "abortion pill", "abortion pills",
             "sleeping pills", "sleeping tablets", "lithium", "seroquel",
             "risperidone", "methotrexate", "steroids", "prednisolone",
             "dexamethasone", "epival", "rivotril", "clonazepam"]

_DOSE_WORDS = ["dose", "dosage", "doses", "how many", "how much", "mg",
               "milligram", "kitni", "kitna", "kitne", "le lun", "kha lun",
               "khaun", "should i take", "can i take", "safe to take"]

_ABORTION_TERMS = ["misoprostol", "cytotec", "mifepristone", "abortion pill",
                   "abortion pills", "end a pregnancy", "end the pregnancy",
                   "end my pregnancy", "hamal khatam", "hamal gira",
                   "bacha gira"]


def guard_dose(text: str):
    """Return a reason string when the message asks for prescription dosing."""
    t = normalize(text)
    tokens = t.split()
    if _hit(tokens, _ABORTION_TERMS):
        return "abortion"
    has_drug = any(d in t for d in _RX_DRUGS)
    has_dose = any(w in t for w in _DOSE_WORDS)
    if has_drug and has_dose:
        return "rx_dose"
    return None


GUARD_MESSAGES = {
    "rx_dose": ("I can't give doses for prescription medicines - the right dose "
                "depends on your weight, kidneys, liver, other medicines and the "
                "exact diagnosis, and getting it wrong can be dangerous. Please "
                "ask the prescribing doctor or a licensed pharmacist. I'm happy "
                "to keep helping with your symptoms."),
    "abortion": ("Decisions and medicines around ending a pregnancy are medical "
                 "and legal matters that must go through a qualified doctor - "
                 "taking these medicines without supervision can cause "
                 "life-threatening bleeding. Please speak to a gynaecologist. "
                 "If heavy bleeding or severe pain is already happening, go to "
                 "a hospital now or call 1122."),
}


# ---------------------------------------------------------------- scrubber

_MG_PATTERNS = [re.compile(rf"\b{re.escape(d)}\b[^.,;\n]*?\d+\s*(?:mg|ml|mcg|g)\b",
                           re.IGNORECASE) for d in _RX_DRUGS]


def scrub_text(s: str) -> str:
    """Remove any prescription-drug dosing the model might have emitted."""
    if not isinstance(s, str):
        return s
    for pat in _MG_PATTERNS:
        s = pat.sub(lambda m: m.group(0).split()[0] + " (dose: ask your doctor)", s)
    return s


def scrub_deep(obj):
    if isinstance(obj, str):
        return scrub_text(obj)
    if isinstance(obj, list):
        return [scrub_deep(x) for x in obj]
    if isinstance(obj, dict):
        return {k: scrub_deep(v) for k, v in obj.items()}
    return obj


# ----------------------------------------------------------------- language

# Function words, not medical words. People mix English symptom terms into
# Roman Urdu constantly — "gala ma pain ha", "flu sa feel ho raha" — so keying
# off "pain" or "fever" would read those as English. Grammar gives the language
# away, because grammar words are the ones that never get swapped out.
#
# Split into strong and weak on purpose. "to", "main", "par" and "or" are
# ordinary English words as well as Urdu ones, and counting them freely made
# "i dont want to live anymore" look like Urdu. They only count as support
# once something unambiguous has already been seen.
_URDU_STRONG = {
    "hai", "hain", "hy", "hei", "hoon", "hun", "tha", "thi", "thay",
    "raha", "rahi", "rha", "rhi", "rahe", "hota", "hoti", "hogaya",
    "mujhe", "muje", "mujhy", "mera", "meri", "mere", "aap", "tum",
    "uska", "uski", "apne", "apna", "apni", "humein", "kya", "kia",
    "kyun", "kiun", "nahi", "nai", "bhi", "lekin", "magar", "agar",
    "phir", "abhi", "kuch", "koi", "bohat", "bhut", "bahut", "boht",
    "zyada", "ziada", "thora", "zara", "halka", "acha", "theek", "thik",
    "jab", "kaise", "kahan", "kitna", "kitni", "wala", "wali",
}

# Only counted when a strong marker is already present.
_URDU_WEAK = {"ka", "ki", "ko", "se", "sa", "si", "ha", "ma", "main", "mein",
              "or", "aur", "to", "par", "pe", "ab", "b", "na", "ya", "hum",
              "sab", "kam", "gaya", "gayi", "bura", "buri"}

# Urdu even when everything around them is English.
_URDU_CONTENT = {
    "dard", "bukhar", "bukhaar", "gala", "pait", "peit", "sar", "sir", "chakkar",
    "kamzori", "khansi", "ulti", "qabz", "saans", "jism", "hath", "pao", "paon",
    "aankh", "kaan", "seena", "seene", "dawai", "dawa", "goli", "tabiyat",
    "beemar", "bimar", "bemari", "khaana", "khana", "neend", "khoon",
}


def detect_language(text: str) -> str:
    """Return "roman_urdu" or "english" for a patient's own words.

    Leans towards Roman Urdu on genuine ambiguity: answering an Urdu speaker
    in English is a real failure, while a stray Urdu word in an English
    sentence costs almost nothing.
    """
    tokens = normalize(text).split()
    if not tokens:
        return "english"

    if any(t in _URDU_CONTENT for t in tokens):
        return "roman_urdu"

    strong = sum(1 for t in tokens if t in _URDU_STRONG)
    if strong >= 2:
        return "roman_urdu"
    if strong == 1:
        # One clear marker plus supporting particles, or a very short message
        # where one marker is most of the sentence.
        weak = sum(1 for t in tokens if t in _URDU_WEAK)
        if weak >= 1 or len(tokens) <= 4:
            return "roman_urdu"
    return "english"
