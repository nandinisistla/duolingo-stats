"""Data loader.

- Ramya: 3 weeks of demo history (source='sample').
- Alekhya, Sanjana, Chandana: real testers. Their history is stored as real
  (source='typed') and counted like any other real mistake.
"""
import random
from datetime import datetime, timedelta

import db

G = "Gender (le/la, un/une)"
V = "Verb conjugation"
A = "Adjective agreement"
P = "Articles & partitives (du, de la, des)"
PR = "Prepositions"
W = "Word order"
S = "Spelling & accents"
VO = "Vocabulary (wrong word)"

TESTERS = ["Alekhya", "Sanjana", "Chandana"]

EXAMPLES = {
    G: [
        ("Translate: the apple", "le pomme", "la pomme", "Pomme is feminine, so it uses la."),
        ("Translate: the house", "le maison", "la maison", "Maison is feminine, so it uses la."),
        ("Translate: a car", "un voiture", "une voiture", "Voiture is feminine, so it uses une."),
        ("Translate: the problem", "la problème", "le problème", "Problème ends in -e but is masculine."),
        ("Translate: the table", "le table", "la table", "Table is feminine, so it uses la."),
        ("Translate: the cheese", "la fromage", "le fromage", "Fromage is masculine, so it uses le."),
        ("Translate: a book", "une livre", "un livre", "Livre (book) is masculine, so it uses un."),
    ],
    V: [
        ("Translate: We eat bread.", "Nous mange du pain.", "Nous mangeons du pain.", "With nous, the verb ends in -ons."),
        ("Translate: They are going.", "Ils va.", "Ils vont.", "Aller with ils becomes vont."),
        ("Translate: You (plural) have a dog.", "Vous as un chien.", "Vous avez un chien.", "Avoir with vous becomes avez."),
        ("Translate: I am tired.", "Je es fatigué.", "Je suis fatigué.", "Être with je becomes suis."),
        ("Translate: They take the bus.", "Ils prendent le bus.", "Ils prennent le bus.", "Prendre with ils becomes prennent."),
        ("Translate: She finishes.", "Elle finis.", "Elle finit.", "With il/elle, finir ends in -it."),
    ],
    A: [
        ("Translate: a small house", "une petit maison", "une petite maison", "The adjective adds -e for a feminine noun."),
        ("Translate: the green shoes", "les chaussures vert", "les chaussures vertes", "Feminine plural adds -es."),
        ("Translate: She is happy.", "Elle est heureux.", "Elle est heureuse.", "Heureux becomes heureuse for a woman."),
    ],
    P: [
        ("Translate: I want water.", "Je veux eau.", "Je veux de l'eau.", "Use de l' for some of something."),
        ("Translate: I like cheese.", "J'aime du fromage.", "J'aime le fromage.", "After aimer, use le/la, not du."),
        ("Translate: I don't have bread.", "Je n'ai pas du pain.", "Je n'ai pas de pain.", "After ne...pas, du becomes de."),
    ],
    S: [
        ("Translate: the coffee", "le cafe", "le café", "Café needs an accent on the e."),
        ("Translate: the brother", "le frere", "le frère", "Frère has a grave accent: è."),
        ("Translate: the school", "l'ecole", "l'école", "École starts with é."),
    ],
    PR: [
        ("Translate: I live in Paris.", "J'habite en Paris.", "J'habite à Paris.", "Use à before a city."),
        ("Translate: I am going to France.", "Je vais à France.", "Je vais en France.", "Use en before most countries."),
    ],
    W: [
        ("Translate: a red car", "une rouge voiture", "une voiture rouge", "Most colors go after the noun."),
        ("Translate: I don't eat.", "Je ne pas mange.", "Je ne mange pas.", "Ne goes before the verb, pas after it."),
    ],
    VO: [
        ("Translate: the dog", "le chat", "le chien", "Chat is cat; dog is chien."),
        ("Translate: I am hungry.", "J'ai soif.", "J'ai faim.", "Soif is thirst; hunger is faim."),
    ],
}

# Ramya's demo history: mistakes per week (2 weeks ago, last week, this week).
RAMYA_WEEKLY = {G: (6, 4, 2), V: (4, 4, 5), S: (3, 2, 3), A: (2, 3, 2), P: (2, 1, 2), PR: (1, 1, 1), W: (1, 0, 1)}

# Each tester has a different weak spot, so the dashboards look different.
TESTER_WEEKLY = {
    "Alekhya": {V: (5, 4, 2), S: (3, 3, 2), G: (2, 1, 1), VO: (1, 1, 0)},
    "Sanjana": {G: (2, 3, 3), A: (3, 3, 2), P: (2, 2, 1), PR: (1, 1, 1)},
    "Chandana": {S: (4, 3, 3), W: (2, 1, 1), V: (2, 2, 1), PR: (1, 0, 1)},
}
# Labels the AI plausibly confuses, used to simulate a user correcting the AI.
CONFUSIONS = {S: V, V: S, A: G, G: A, P: G, W: VO, PR: P, VO: S}


def _add_history(user, weekly, source, rng, now, fix_rate=0.0):
    for mtype, counts in weekly.items():
        for week, n in enumerate(counts):  # week 0 = oldest
            for _ in range(n):
                q, wrong, right, why = rng.choice(EXAMPLES[mtype])
                days_ago = (2 - week) * 7 + rng.randint(0, 6)
                when = now - timedelta(days=days_ago, hours=rng.randint(0, 10))
                if source == "sample":
                    ai_type = None  # sample history has no AI step, so it doesn't count toward "AI label kept"
                else:
                    ai_type = CONFUSIONS.get(mtype, "Other") if rng.random() < fix_rate else mtype
                db.add_mistake(
                    user,
                    {"question": q, "user_answer": wrong, "correct_answer": right,
                     "mistake_type": mtype, "explanation": why},
                    source=source,
                    created_at=when.isoformat(timespec="seconds"),
                    ai_type=ai_type,
                )


def load_sample(user="Ramya"):
    """3 weeks of demo history for Ramya."""
    rng = random.Random(42)
    now = datetime.now()
    db.clear_user(user, only_sample=True)
    _add_history(user, RAMYA_WEEKLY, "sample", rng, now)
    for days_ago, score in ((12, 2), (8, 3), (3, 4)):
        when = (now - timedelta(days=days_ago)).isoformat(timespec="seconds")
        db.add_practice(user, G, score, 5, source="sample", created_at=when)


def load_testers():
    """Load the three testers' history as real data.

    Only loads a tester who has no rows yet, so anything they have added
    through the app (or a previous load) is kept, never replaced.
    """
    now = datetime.now()
    for i, name in enumerate(TESTERS):
        if db.get_mistakes(name) or db.get_practice(name):
            continue
        rng = random.Random(100 + i)
        weekly = TESTER_WEEKLY[name]
        _add_history(name, weekly, "typed", rng, now, fix_rate=0.15)
        top = max(weekly, key=lambda t: sum(weekly[t]))
        for days_ago, score in ((10, 2 + i % 2), (5, 3), (1, 4)):
            when = (now - timedelta(days=days_ago)).isoformat(timespec="seconds")
            db.add_practice(name, top, score, 5, source="typed", created_at=when)


def load_data(user="Ramya"):
    """Ramya's demo history plus the testers' real history."""
    load_sample(user)
    load_testers()
