import re
from collections import Counter

CATEGORIES = {
    "temple": ["temple", "mandir", "shrine", "deity", "gopuram"],
    "fort": ["fort", "fortress", "rampart", "bastion", "citadel"],
    "palace": ["palace", "mahal", "haveli"],
    "inscription": ["inscription", "epigraph", "edict", "copper plate"],
    "manuscript": ["manuscript", "folio", "scroll", "parchment"],
    "stepwell": ["stepwell", "vav", "baoli", "kund"],
    "mosque/tomb": ["mosque", "masjid", "dargah", "tomb", "mausoleum"],
    "stupa/cave": ["stupa", "vihara", "cave", "chaitya"],
}
ERAS = {
    "Ancient": ["maurya", "gupta", "ashoka", "satavahana", "bce", "buddhist"],
    "Medieval": ["chalukya", "solanki", "rajput", "sultanate", "delhi sultan", "vijayanagara", "mughal", "akbar"],
    "Colonial": ["british", "colonial", "east india company", "raj", "portuguese"],
    "Modern": ["independence", "republic", "restored", "conservation"],
}
PLACES = ["Gujarat", "Maharashtra", "Rajasthan", "Madhya Pradesh", "Karnataka", "Tamil Nadu", "Odisha",
          "Uttar Pradesh", "Delhi", "Bhopal", "Nagpur", "Ahmedabad", "Patan", "Modhera", "Hampi",
          "Khajuraho", "Sanchi", "Jaipur", "Agra", "Ajanta", "Ellora", "Mumbai", "Pune", "Varanasi"]
STOP = set("""the and for with that this from were was are has had have its into over upon their there which
also been being than then them they his her but not all can may one two about after before between these those
such more most other some any only very will would should could out our who whom what when where""".split())

def _best(text, table):
    low = text.lower()
    scores = {k: sum(low.count(w) for w in words) for k, words in table.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Unclassified"

def analyse(text):
    low = text.lower()
    deva = len(re.findall(r"[\u0900-\u097F]", text))
    language = "Hindi/Marathi (Devanagari)" if deva > len(text) * 0.3 and text else "English"
    place = next((p for p in PLACES if p.lower() in low), "")
    era = _best(text, ERAS)
    century = re.search(r"(\d{1,2})(?:st|nd|rd|th)\s+century", low)
    if century:
        c = int(century.group(1))
        era = "Ancient" if c <= 5 else "Medieval" if c <= 17 else "Colonial" if c <= 19 else "Modern"
    words = [w for w in re.findall(r"[a-z]{4,}", low) if w not in STOP]
    keywords = [w for w, _ in Counter(words).most_common(6)]
    category = _best(text, CATEGORIES)
    tags = keywords + ([category] if category != "Unclassified" else []) + ([place.lower()] if place else [])
    return {"category": category, "era": era, "location": place, "language": language, "tags": tags}
