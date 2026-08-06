"""
SEHAT first-aid library.

Every protocol answers three questions in order:
  steps          - what to do right now, numbered
  do_not         - the mistakes that make it worse
  until_hospital - what to keep doing on the way, until doctors take over

Content follows standard first-aid teaching (Red Cross / St John style),
written for Pakistan: Rescue 1122, Edhi 115, everyday materials
(dupatta, charpai, clean cloth) instead of kit that people don't have.
"""

CALL = "1122"

PROTOCOLS = {
    "unconscious": {
        "title": "Unconscious but breathing",
        "icon": "😵",
        "signs": "Does not respond to voice or a firm shoulder tap, but chest is rising and falling.",
        "steps": [
            "Shout for help and call 1122 - put the phone on speaker.",
            "Check response: call their name loudly, tap both shoulders firmly.",
            "Open the airway: tilt the head back gently and lift the chin.",
            "Check breathing for 10 seconds - watch the chest, feel for air on your cheek.",
            "If breathing: roll them onto their side (recovery position) - bend the top knee, rest the top hand under the cheek, head tilted slightly back so the mouth faces down.",
            "Loosen anything tight at the neck and waist.",
            "Put nothing in the mouth - no water, no food, no medicine.",
            "If breathing stops or becomes only gasps, start CPR immediately (see CPR card).",
        ],
        "do_not": [
            "Do not give water or anything by mouth.",
            "Do not put a pillow under the head - it blocks the airway.",
            "Do not leave them alone.",
            "Do not shake violently or throw lots of water on the face.",
        ],
        "until_hospital": [
            "Re-check breathing every minute.",
            "Keep them on their side and keep them warm.",
            "Note the time they became unconscious - doctors will ask.",
            "Collect their medicines, sugar/BP history, and any empty pill packets to show the doctor.",
        ],
    },
    "cpr": {
        "title": "CPR - not breathing",
        "icon": "❤️",
        "signs": "No breathing, or only occasional gasps. Every minute matters.",
        "steps": [
            "Call 1122 on speaker, or point at one person and tell them to call.",
            "Lay the person flat on their back on a firm surface (floor, not a bed).",
            "Kneel beside the chest. Put the heel of one hand on the centre of the chest, the other hand on top, fingers interlocked, arms straight.",
            "Push hard and fast: press down 5-6 cm, at 100-120 pushes per minute.",
            "Let the chest come all the way back up between pushes.",
            "If trained: 30 compressions, then 2 rescue breaths. If not trained: just keep pushing without stopping.",
            "If someone else is there, swap every 2 minutes - good CPR is exhausting.",
        ],
        "do_not": [
            "Do not stop to check your phone or the person - keep compressions going.",
            "Do not give water.",
            "Do not press on the ribs at the side or the very bottom tip of the breastbone.",
        ],
        "until_hospital": [
            "Do not stop until they start breathing, trained help takes over, or you physically cannot continue.",
            "If they start breathing, roll them into the recovery position and keep watching.",
        ],
    },
    "choking": {
        "title": "Choking",
        "icon": "🫁",
        "signs": "Clutching the throat, cannot speak, cough or breathe. If they CAN cough - encourage coughing, do nothing else.",
        "steps": [
            "Ask loudly: \"Are you choking?\" If they can speak or cough, encourage hard coughing only.",
            "If they cannot breathe or speak: bend them forward and give 5 firm back blows between the shoulder blades with the heel of your hand.",
            "If still stuck: stand behind them, make a fist just above the navel, grasp it with the other hand, and pull sharply inward and upward - 5 times (abdominal thrusts).",
            "Keep alternating 5 back blows and 5 thrusts.",
            "If they collapse: call 1122 and start CPR - the compressions can also push the object out.",
            "For a baby under 1 year: lay face-down along your forearm, head low - 5 back blows, then turn over for 5 chest pushes with two fingers. Never do abdominal thrusts on a baby.",
        ],
        "do_not": [
            "Do not put fingers blindly into the mouth to fish for the object.",
            "Do not give water while they are choking.",
            "Do not slap the back of someone who is coughing well - let them cough.",
        ],
        "until_hospital": [
            "Anyone who needed abdominal thrusts should be checked by a doctor even if they seem fine - the thrusts can injure inside.",
        ],
    },
    "severe_bleeding": {
        "title": "Severe bleeding",
        "icon": "🩸",
        "signs": "Blood flowing continuously, spurting, or soaking through cloth.",
        "steps": [
            "Call 1122 if the bleeding is heavy or spurting.",
            "Press hard directly on the wound with a clean cloth - use both hands and your body weight if needed.",
            "Keep pressing for a full 10 minutes without lifting to peek.",
            "If blood soaks through, add more cloth ON TOP - never remove the first layer.",
            "Bind it: wrap a bandage, cloth or dupatta firmly over the pad to hold the pressure while you move.",
            "Raise the bleeding limb above heart level if no bone seems broken.",
            "If something is stuck in the wound (glass, rod): do NOT pull it out - pad and bandage around it.",
            "Last resort for a limb bleed that will not stop: tie a tight band (belt/cloth) 5-7 cm above the wound, tighten until bleeding stops, and WRITE DOWN THE TIME. Never loosen it yourself.",
        ],
        "do_not": [
            "Do not put powder, haldi, soil, coffee or any totka on the wound.",
            "Do not remove objects embedded in the wound.",
            "Do not keep lifting the cloth to look.",
        ],
        "until_hospital": [
            "Lie them down, raise the legs slightly, cover with a sheet to keep warm.",
            "Watch for shock: pale, cold, sweaty skin, fast breathing, confusion - tell the hospital.",
            "Nothing to eat or drink - surgery may be needed.",
        ],
    },
    "fracture": {
        "title": "Broken bone (fracture)",
        "icon": "🦴",
        "signs": "Severe pain, swelling, odd shape or angle, cannot bear weight, or bone visible.",
        "steps": [
            "Keep the person still. Support the injured part in the position you found it.",
            "Hold it and bind it: splint with something rigid (stick, board, rolled magazine) padded with cloth.",
            "Tie the splint above and below the break - never directly over it.",
            "For an arm: make a sling from a dupatta or scarf and support it against the chest.",
            "Remove rings, bangles and watches near the injury before swelling starts.",
            "Cold pack wrapped in cloth for 15 minutes to reduce swelling.",
            "If bone is visible (open fracture): cover with a clean cloth, press around - not on - the bone, and treat as severe bleeding.",
            "Call 1122 for leg, hip, back or open fractures - do not transport these yourself unless there is no other option.",
        ],
        "do_not": [
            "Do not straighten the limb or push bone back in.",
            "Do not let them walk on a suspected leg fracture.",
            "Do not massage the area or apply heat.",
        ],
        "until_hospital": [
            "Check fingers/toes beyond the splint every few minutes - they should stay warm and pink. If cold, blue or numb, loosen the ties slightly.",
            "Nothing to eat or drink - the bone may need surgery under anaesthesia.",
        ],
    },
    "burns": {
        "title": "Burns and scalds",
        "icon": "🔥",
        "signs": "From boiling water, fire, hot oil, chemicals or electricity.",
        "steps": [
            "Cool the burn under gently running cool water for a FULL 20 minutes. This is the single most important step - even starting within 3 hours still helps.",
            "While cooling, remove rings, bangles and tight clothing near the burn before swelling starts.",
            "Remove clothing over the burn unless it is stuck to the skin - if stuck, leave it.",
            "Cover loosely with cling film laid lengthwise, or a clean non-fluffy cloth.",
            "Paracetamol is fine for the pain.",
            "For chemical burns: brush off any dry powder first, then rinse with running water for at least 20 minutes.",
            "Go to hospital if the burn is bigger than the person's palm, on the face, hands, feet, genitals or over a joint, looks white/charred/painless, is from chemicals or electricity, or the person is a child or elderly.",
        ],
        "do_not": [
            "No ice or ice water - it deepens the burn.",
            "No toothpaste, butter, ghee, haldi or egg - these trap heat and cause infection.",
            "Do not burst blisters.",
            "Do not peel off stuck clothing.",
        ],
        "until_hospital": [
            "Keep the burnt area covered and elevated if possible.",
            "Small sips of water are fine if fully conscious and the burn is small; nothing by mouth for large burns.",
            "Keep the person warm - large burns lose body heat fast.",
        ],
    },
    "seizure": {
        "title": "Seizure / fits",
        "icon": "⚡",
        "signs": "Sudden stiffening, jerking movements, unresponsive, possibly frothing or urinating.",
        "steps": [
            "Note the exact time it started - the length decides everything.",
            "Move hard or sharp objects away. Cushion the head with something soft (folded cloth).",
            "Put NOTHING in the mouth - it is impossible to swallow the tongue; objects break teeth and block breathing.",
            "Do not hold them down - let the fit run its course.",
            "Loosen anything tight around the neck.",
            "When the jerking stops, roll them into the recovery position and stay with them until fully awake.",
            "Call 1122 if: the fit lasts more than 5 minutes, another fit starts, it is their first-ever fit, they are pregnant, injured, in water, or do not wake up properly.",
        ],
        "do_not": [
            "Nothing in the mouth - no spoon, no cloth, no fingers, no water.",
            "Do not restrain the jerking limbs.",
            "Do not give food, drink or medicine until fully awake.",
        ],
        "until_hospital": [
            "Keep them on their side, keep timing any further fits.",
            "They will be confused and sleepy afterwards - reassure them quietly.",
            "Tell doctors: how long it lasted, what it looked like, any known epilepsy or diabetes, any medicines.",
        ],
    },
    "heart_attack": {
        "title": "Heart attack",
        "icon": "💔",
        "signs": "Chest pressure, tightness or pain; may spread to the left arm, jaw, back; sweating, nausea, breathlessness. Women, elderly and diabetics may mainly feel breathless, weak or sick with little chest pain.",
        "steps": [
            "Call 1122 NOW. Do not wait to see if it passes.",
            "Stop all activity. Sit them on the floor, back against a wall, knees bent - this eases the heart's work.",
            "Loosen tight clothing.",
            "If fully conscious, not allergic to aspirin, and no bleeding disorder: let them slowly CHEW one adult aspirin/Disprin (300 mg).",
            "If they have their own prescribed tongue spray or tablet (GTN/Angised), let them take it as prescribed.",
            "Stay with them, keep them calm and still.",
            "If they become unconscious and stop breathing normally: start CPR immediately.",
        ],
        "do_not": [
            "Do not let them walk around, climb stairs or drive themselves.",
            "Do not give food or water.",
            "Do not massage the chest of a conscious person or delay the 1122 call for home remedies.",
        ],
        "until_hospital": [
            "Keep them seated and still; keep talking to them.",
            "Note the time the pain started and any medicines taken - tell the hospital.",
            "Go to a hospital with a cardiac unit if there is a choice nearby.",
        ],
    },
    "stroke": {
        "title": "Stroke - act FAST",
        "icon": "🧠",
        "signs": "F - Face droops on one side when smiling. A - Arms: one drifts down when both are raised. S - Speech slurred or strange. T - Time to call 1122 immediately.",
        "steps": [
            "Do the FAST check above. Any one sign = call 1122 now.",
            "Note the EXACT time symptoms started - stroke treatment is time-limited and doctors will ask first.",
            "Lie them down with head and shoulders slightly raised.",
            "Give NOTHING to eat or drink - swallowing often fails and they can choke.",
            "Loosen the collar; remove glasses and dentures.",
            "If they become unconscious but are breathing: recovery position, monitor breathing.",
        ],
        "do_not": [
            "Do NOT give aspirin - some strokes are bleeds and aspirin makes those worse.",
            "No water, food or medicine by mouth.",
            "Do not wait for symptoms to pass - even if they improve, go.",
        ],
        "until_hospital": [
            "Keep re-checking FAST signs and breathing.",
            "Bring their medicine list; tell doctors the exact start time and any blood thinners.",
        ],
    },
    "snake_bite": {
        "title": "Snake bite",
        "icon": "🐍",
        "signs": "Puncture marks, spreading pain and swelling; later drooping eyelids, difficulty swallowing or breathing.",
        "steps": [
            "Move the person away from the snake. Keep them CALM and as STILL as possible - movement spreads venom.",
            "Call 1122 and head for a hospital that stocks anti-venom (DHQ/THQ level).",
            "Immobilise the bitten limb with a splint or sling, kept at about heart level.",
            "Remove rings, bangles, watch and tight clothing from the limb before it swells.",
            "Mark the edge of the swelling with a pen and write the time - doctors track its spread.",
            "Try to remember the snake's colour and shape, or photograph it from a safe distance. Do not chase it.",
        ],
        "do_not": [
            "Do NOT cut the wound or try to suck out venom.",
            "Do NOT tie a tight tourniquet.",
            "No ice, no electric shock, no totkay or spiritual delays.",
            "Do not let them run or walk if it can be avoided - carry them.",
        ],
        "until_hospital": [
            "Keep the limb still and at heart level; keep the person lying quietly.",
            "Watch breathing closely - be ready to do CPR.",
            "Nothing to eat or drink.",
        ],
    },
    "heatstroke": {
        "title": "Heat stroke",
        "icon": "🌡️",
        "signs": "Very hot red skin (often dry), confusion or strange behaviour, staggering, possible collapse - usually after heat exposure or loo.",
        "steps": [
            "Call 1122 - heat stroke kills. This is beyond simple dehydration.",
            "Move them to shade or a cool room immediately.",
            "Remove extra clothing.",
            "Cool aggressively: pour or sponge water over the body and fan continuously; put cloth-wrapped ice packs on the neck, armpits and groin.",
            "If fully conscious and alert: small sips of cool water or ORS.",
            "If confused or unconscious: nothing by mouth; recovery position if unconscious and breathing.",
        ],
        "do_not": [
            "Do not give fluids to a confused or unconscious person.",
            "Do not stop cooling while waiting - cooling IS the treatment.",
            "No paracetamol - it does not lower this kind of temperature.",
        ],
        "until_hospital": [
            "Keep cooling and fanning in the vehicle too.",
            "Re-check response and breathing every minute.",
        ],
    },
    "poisoning": {
        "title": "Poisoning / overdose",
        "icon": "☠️",
        "signs": "Swallowed medicine overdose, household chemicals, kerosene, pesticides, or unknown substances.",
        "steps": [
            "Call 1122. Speak clearly: what was taken, how much, and when.",
            "Keep the bottle, packet or a sample to show the doctors - this changes the treatment.",
            "Do NOT make them vomit - acids, bleach and kerosene burn twice on the way back up.",
            "Poison on skin or in eyes: rinse under running water for 15-20 minutes.",
            "Breathed-in fumes: get them to fresh air fast, without endangering yourself.",
            "If conscious: nothing to eat or drink unless the hospital tells you.",
            "If unconscious and breathing: recovery position; if not breathing: CPR.",
        ],
        "do_not": [
            "Do not induce vomiting.",
            "Do not give milk, lassi, salt water or 'antidote' totkay.",
            "Do not wait for symptoms - some poisons act silently for hours.",
        ],
        "until_hospital": [
            "Bring the container/sample and any suicide-risk information honestly - it changes care and is kept confidential.",
            "Keep checking breathing on the way.",
        ],
    },
    "electric_shock": {
        "title": "Electric shock",
        "icon": "🔌",
        "signs": "Person in contact with a live wire or appliance, possibly collapsed.",
        "steps": [
            "Do NOT touch them while they may still be connected - you will be shocked too.",
            "Switch off the main power. If you cannot, push the cable away with dry wood or plastic while standing on a dry surface.",
            "High-voltage lines (poles, transformers): stay at least 20 metres back and call 1122 - only the power company can make it safe.",
            "Once safe: check response and breathing. Not breathing → CPR.",
            "Cool and cover any burns at the entry and exit points.",
            "Everyone who had a significant shock needs a hospital check even if they look fine - electricity can disturb the heart rhythm hours later.",
        ],
        "do_not": [
            "Never use anything wet or metallic to move the wire.",
            "Do not move someone who fell from a height after the shock unless in danger - protect the neck.",
        ],
        "until_hospital": [
            "Watch breathing and responsiveness continuously.",
            "Note the voltage source (home wiring vs main line) for the doctors.",
        ],
    },
    "drowning": {
        "title": "Drowning",
        "icon": "🌊",
        "signs": "Pulled from water, not breathing or coughing badly.",
        "steps": [
            "Get them out without becoming the second victim - reach with a stick, throw a rope or float; enter water only as a last resort.",
            "Call 1122. Check response and breathing.",
            "Not breathing: if trained, give 5 initial rescue breaths, then CPR 30:2. If untrained, do continuous chest compressions.",
            "Breathing: recovery position, remove wet clothes, cover and keep warm.",
            "Everyone who nearly drowned must be checked at a hospital - water in the lungs causes trouble hours later, even after they feel fine.",
        ],
        "do_not": [
            "Do not waste time trying to 'drain water' by holding them upside down or pressing the belly.",
            "Do not leave them alone after recovery - secondary drowning is real.",
        ],
        "until_hospital": [
            "Keep them warm and lying on their side.",
            "Watch for coughing, frothy spit or worsening breathing and tell the hospital.",
        ],
    },
    "head_injury": {
        "title": "Head injury",
        "icon": "🤕",
        "signs": "A blow to the head. Danger signs: was knocked out (even briefly), repeated vomiting, worsening headache, confusion, unequal pupils, clear fluid or blood from ear/nose, fits, or unusually sleepy.",
        "steps": [
            "Sit or lie them down and keep them still, head and shoulders slightly raised.",
            "Cold pack wrapped in cloth on the bump for 15 minutes.",
            "Scalp bleeding: press firmly with a clean cloth (scalps bleed a lot - that alone is not the danger).",
            "If they fell from height or a vehicle: assume neck injury - hold the head still with both hands, in line with the body, and do not move them.",
            "Any danger sign above → hospital now / call 1122.",
            "If no danger signs: watch closely for 24 hours; wake them gently every few hours during the first night to check they respond normally.",
        ],
        "do_not": [
            "Do not give sleeping or strong pain medicine - it hides the danger signs (paracetamol only).",
            "Do not let them play sports, drive or be alone for 24 hours.",
            "Do not plug the ear or nose if fluid leaks - let it drain onto a clean cloth.",
        ],
        "until_hospital": [
            "Keep the head supported and still if the neck is suspected.",
            "Note vomiting episodes, confusion and the time of injury for the doctors.",
        ],
    },
    "road_accident": {
        "title": "Road accident",
        "icon": "🚗",
        "signs": "Any vehicle crash - car, bike, rickshaw, pedestrian hit.",
        "steps": [
            "Make the scene safe first: park behind the crash, hazard lights on, ask someone to slow traffic, switch off the crashed vehicle's ignition.",
            "Call 1122. Say the location clearly and how many people are hurt.",
            "Do NOT move the injured unless there is fire, traffic or another immediate danger.",
            "Talk to each casualty; check who responds and who is breathing - help the quiet ones first.",
            "Heavy bleeding: press hard with cloth and bind it firmly (see Severe bleeding card).",
            "Assume a neck/spine injury in every crash: kneel behind the head and hold it steady with both hands, in line with the body.",
            "Motorcycle helmet: leave it ON unless they are not breathing and you must open the airway.",
            "Cover them with a chaddar or jacket - injured people lose heat fast even in summer.",
        ],
        "do_not": [
            "Do not pull people out of vehicles unless there is immediate danger.",
            "Do not give water, even if they ask - surgery may be needed.",
            "Do not remove a helmet unnecessarily.",
            "Do not crowd around - give air and space.",
        ],
        "until_hospital": [
            "Keep talking to them; re-check breathing every minute.",
            "Keep the head held steady if the neck is suspected, even during transport.",
            "Send someone ahead to alert the hospital if it is close.",
        ],
    },
    "allergic_reaction": {
        "title": "Severe allergic reaction",
        "icon": "🐝",
        "signs": "After food, a sting or a medicine: swelling of lips/tongue/throat, breathing difficulty, widespread rash, dizziness or collapse.",
        "steps": [
            "Call 1122 at the first sign of throat swelling or breathing trouble.",
            "If they carry their own adrenaline pen (EpiPen): use it immediately on the outer thigh - it can go through clothing.",
            "Lie them flat with legs raised. If breathing is hard, let them sit up instead.",
            "Remove the trigger: scrape out a bee sting sideways with a card edge; stop the food or medicine.",
            "An antihistamine tablet helps only mild skin reactions - it will NOT treat throat swelling; never delay 1122 for it.",
            "If they collapse and stop breathing: CPR.",
        ],
        "do_not": [
            "Do not have them stand or walk - it can crash the blood pressure.",
            "Do not induce vomiting after a food trigger.",
            "Do not assume it is over if symptoms ease - reactions rebound.",
        ],
        "until_hospital": [
            "Keep them lying down with legs raised (or seated if breathless).",
            "A second adrenaline dose can be given after 5 minutes if there is no improvement and a second pen exists.",
            "Even after a pen works, hospital observation is compulsory.",
        ],
    },
    "pregnancy_emergency": {
        "title": "Pregnancy emergency",
        "icon": "🤰",
        "signs": "Heavy bleeding, severe abdominal pain, fits, water broken with cord visible, baby not moving (after 26 weeks), or severe headache with blurred vision/swelling (after 20 weeks).",
        "steps": [
            "Call 1122 and head to a hospital WITH a delivery/obstetric facility - take her antenatal card and reports.",
            "Lie her on her LEFT side - this keeps blood flowing to the baby.",
            "Bleeding: use a pad (never a tampon). Keep the soaked pads in a bag - doctors measure blood loss from them.",
            "Fits: protect her from injury, put nothing in her mouth, roll to the left side after the fit, note the time.",
            "If the water has broken and a loop of cord is visible at the opening: get her into knee-to-chest position (kneeling, chest down on the bed) and do NOT touch or push the cord.",
            "Nothing to eat or drink - an operation may be needed.",
        ],
        "do_not": [
            "Do not wait for morning or for the clinic to open.",
            "Do not give any medicine, totka or gutti on the way.",
            "Do not press or massage the belly.",
        ],
        "until_hospital": [
            "Keep her on the left side; keep her talking to you.",
            "Call the hospital or her doctor while travelling so they prepare.",
            "Bring her medicine list, sugar/BP record and scan reports.",
        ],
    },
    "nosebleed": {
        "title": "Nosebleed",
        "icon": "👃",
        "signs": "Bleeding from one or both nostrils.",
        "steps": [
            "Sit them down and lean the head FORWARD - not back.",
            "Pinch the soft part of the nose (just below the bone) firmly for a full 10 minutes without letting go to check.",
            "Breathe through the mouth; spit out blood rather than swallowing it.",
            "A cold pack on the bridge of the nose helps.",
            "If still bleeding after 10 minutes, pinch for another 10.",
            "After it stops: no nose-blowing, picking or hot drinks for a few hours.",
        ],
        "do_not": [
            "Do not tilt the head back - blood runs down the throat and causes vomiting.",
            "Do not stuff cloth or tissue deep inside.",
        ],
        "until_hospital": [
            "Go to hospital if it has not stopped after 20-30 minutes of proper pressure, follows a head injury, or the person takes blood thinners.",
        ],
    },
    "breathing": {
        "title": "Severe breathing difficulty",
        "icon": "😮‍💨",
        "signs": "Struggling for air, cannot finish a sentence, blue lips, loud wheezing, sucking-in at the throat/ribs.",
        "steps": [
            "Call 1122 if lips are turning blue, they cannot speak in sentences, or they are getting worse.",
            "Sit them UPRIGHT, leaning slightly forward with arms supported on a table - do not lie them down.",
            "Loosen tight clothing; open windows for fresh air; keep everyone calm.",
            "Known asthma: help them take their own reliever inhaler (usually blue) - 1 puff every 30-60 seconds, up to 10 puffs, through a spacer or cupped hands if available.",
            "If choking is the cause, switch to the Choking card.",
            "If they stop breathing: CPR.",
        ],
        "do_not": [
            "Do not lie them flat.",
            "Do not crowd around them.",
            "Do not delay the 1122 call for steam or home remedies when lips are blue.",
        ],
        "until_hospital": [
            "Keep them upright, keep the inhaler with you, and count the puffs given to tell the doctors.",
            "Watch for drowsiness or quietness - a tiring patient is an emergency, not an improvement.",
        ],
    },
}


def list_protocols():
    return [
        {"id": pid, "title": p["title"], "icon": p["icon"], "signs": p["signs"]}
        for pid, p in PROTOCOLS.items()
    ]


def get_protocol(pid: str):
    p = PROTOCOLS.get(pid)
    if not p:
        return None
    return {"id": pid, "call": CALL, **p}
