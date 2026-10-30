"""Normalize Vietnamese/INN drug names into comparison keys and English spelling variants.

- base_key: lowercase, accents stripped (đ->d), hyphens/hydrate/L- prefix normalized.
- salt_stripped: drop salt/hydrate/ester words ("Losartan kali" -> "losartan").
- spelling_variants: Vietnamese -> English spelling rules
  (Amoxicilin -> amoxicillin, Clorpheniramin -> chlorpheniramine, Acid folic -> folic acid, Natri clorid -> sodium chloride).
"""
import re
import unicodedata
from itertools import product


def strip_accents(s: str) -> str:
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def has_vietnamese_diacritics(s: str) -> bool:
    return strip_accents(s) != s


def base_key(name: str) -> str:
    s = strip_accents(name).lower()
    s = re.sub(r"[‐-―]", "-", s)
    s = re.sub(r"\s*-\s*", "-", s)
    s = re.sub(r"\s*[.·]?\s*\d*\s*h2o", "", s)           # "Magnesi clorid.6H2O"
    s = re.sub(r"(?<=[a-z])\s*\.\s*(?=[a-z])", " ", s)   # "Dextromethorphan.HBr" -> "dextromethorphan hbr"
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"^(?:dl|d|l)-(?=[a-z]{3})", "", s)    # L-Tryptophan -> tryptophan


SALT_WORDS = set("""
hydroclorid hydrochlorid hydrochloride hcl dihydroclorid dihydrochloride hydrobromid hydrobromide hbr
natri sodium dinatri disodium kali potassium dikali calci calcium magnesi magnesium kem zinc
maleat maleate dimaleat sulfat sulfate sulphat sulphate bisulfat
acetat acetate phosphat phosphate citrat citrate tartrat tartrate bitartrat bitartrate
besylat besylate besilat besilate mesylat mesylate mesilat mesilate dimesylat tosylat tosilat
fumarat fumarate hemifumarat succinat succinate bromid bromide iodid iodide nitrat nitrate mononitrat
lactat lactate gluconat gluconate carbonat carbonate bicarbonat oxalat oxalate valerat valerate
propionat propionate dipropionat dipropionate butyrat butyrate furoat furoate xinafoat xinafoate
hyclat hyclate pamoat pamoate embonat stearat estolat estolate ethylsuccinat palmitat palmitate
monohydrat monohydrate dihydrat dihydrate trihydrat trihydrate pentahydrat pentahydrate
sesquihydrat sesquihydrate hemihydrat hemihydrate heptahydrat heptahydrate hexahydrat hexahydrate
hydrat hydrate khan anhydrous anhydrat tert-butylamin tert-butylamine erbumin erbumine
arginin arginine lysin lysine meglumin meglumine trometamol tromethamine pivoxil axetil proxetil
medoxomil cilexetil disoproxil alafenamid alafenamide dipivoxil mofetil
""".split())


EXTRACT_PREFIX_RE = re.compile(r"^(?:cao|bot|dried|dry)(?:\s+(?:kho|dac|long|qua|toan phan|chiet xuat))*\s+")


def extract_prefix_stripped(key: str) -> str:
    """Drop herbal-extract/dosage prefixes: "cao kho carduus marianus" -> "carduus marianus"."""
    return EXTRACT_PREFIX_RE.sub("", key)


def salt_stripped(key: str) -> str:
    """Drop salt words; keep the key unchanged if nothing would remain ("natri clorid")."""
    tokens = [t for t in key.split() if t not in SALT_WORDS]
    return " ".join(tokens) if tokens else key


ELEMENT_MAP = {
    "natri": "sodium", "kali": "potassium", "calci": "calcium", "magnesi": "magnesium", "kem": "zinc",
    "sat": "iron", "nhom": "aluminum", "clorid": "chloride", "iodid": "iodide", "sulfat": "sulfate",
    "carbonat": "carbonate", "bicarbonat": "bicarbonate", "oxyd": "oxide", "hydroxyd": "hydroxide",
    "phosphat": "phosphate", "citrat": "citrate", "gluconat": "gluconate", "lactat": "lactate",
    "acetat": "acetate", "fluorid": "fluoride", "bromid": "bromide",
}
# Vietnamese ending -> English ending (Paracetamol stays, Metronidazol -> metronidazole)
SUFFIX_RULES = (("in", "ine"), ("im", "ime"), ("ol", "ole"), ("on", "one"), ("at", "ate"),
                ("id", "ide"), ("an", "ane"), ("yl", "yle"))
MAX_WORD_VARIANTS = 24


def _word_variants(w: str) -> list:
    v = {w}
    if w in ELEMENT_MAP:
        v.add(ELEMENT_MAP[w])
    if "cilin" in w:
        v.add(w.replace("cilin", "cillin"))
    if "clo" in w and not w.startswith("clon"):           # hydroclorothiazid -> hydrochlorothiazide
        v |= {x.replace("clo", "chlo") for x in list(v)}
    if "ciclo" in w:                                       # aciclovir, ciclosporin
        v |= {x.replace("ciclo", "cyclo") for x in list(v)}
    if w.startswith("cafe"):
        v.add("caffeine")
    if w.startswith("cef"):
        v |= {"ceph" + x[3:] for x in list(v)}
    if "ph" in w:
        v |= {x.replace("ph", "f") for x in list(v)}
    if "f" in w:
        v |= {x.replace("f", "ph") for x in list(v)}
    for suf, rep in SUFFIX_RULES:
        v |= {x + rep[len(suf):] for x in list(v) if x.endswith(suf)}
    v |= {x[:-1] for x in list(v) if x.endswith("e") and len(x) > 4}   # fluorouracile -> fluorouracil
    return sorted(v)[:MAX_WORD_VARIANTS]


def spelling_variants(key: str, limit: int = 400) -> list:
    """All English spelling candidates for a key (bounded to avoid combinatorial blow-up)."""
    m = re.match(r"^acid (.+)$", key)                      # "acid folic" -> "folic acid"
    if m:
        key = m.group(1) + " acid"
    words = key.split()
    if not words or len(words) > 4:
        return [key]
    out = []
    for combo in product(*[_word_variants(w) for w in words]):
        out.append(" ".join(combo))
        if len(out) >= limit:
            break
    return out
