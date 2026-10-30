"""Parse the free-text `Thành phần` cell of national_drug.xlsx into ingredient names.

Pipeline per cell:
  preclean (NFC, µ->mc, newline->;) -> strip header ("Mỗi viên chứa:")
  -> split at bracket depth 0 on ; , (non-decimal) và + Name/Name
  -> per piece: drop brackets, cut "tương đương/dưới dạng..." tail, strip doses.
Bracket content such as "(dưới dạng Ciprofloxacin HCl)" or "(tương đương Pitavastatin)"
is kept as alternate names, used by the matcher when the main name does not match.
"""
import re
import unicodedata
from dataclasses import dataclass, field

LETTER = r"A-Za-zÀ-ỹ"
OPEN, CLOSE = "([{", ")]}"

HEADER_RE = re.compile(
    r"^\s*(?:(?:mỗi|trong|một|1)\b[^:;()]{0,70}?\b(?:chứa|có)\b\s*:?"  # "Mỗi viên nén chứa", "Trong 1 lọ có"
    r"|[^:;()]{0,50}?\bchứa\s*:"                                        # "Tuýp 10g chứa:"
    r"|[^:;()]{0,80}?\b(?:gồm|dược liệu|như sau)\s*:)",                 # "Bột mịn dược liệu gồm:"
    re.I)
# Generic herbal-extract descriptions, not an ingredient themselves ("Cao đặc hỗn hợp dược liệu");
# the herbs they list in brackets are promoted to ingredients instead.
GENERIC_HERBAL_RE = re.compile(
    r"^(?:(?:cao|bột|chất chiết|dịch chiết)\b.*\b(?:dược liệu|hỗn hợp|tổng hợp)\b|hỗn hợp\b|dược liệu$"
    r"|cao(?: (?:khô|đặc|lỏng))?$)", re.I)
# Leftover header pieces after splitting on ":" ("Bột mịn dược liệu gồm", "Mỗi liều bao gồm",
# "chất chiết xuất từ", "Mỗi chai", "Tuýp", "Bút chứa dung dịch tiêm", "nồng độ dung dịch sau hoàn nguyên")
HEADER_TAIL_RE = re.compile(r"\b(?:gồm|gồm có|như sau|chứa|tương đương|tương ứng|(?:chiết|xuất|chế|lấy|được)\s+từ)\s*$",
                            re.I)
# Packaging prefix in front of a real name: "Ống chứa Calcitonin salmon", "Mỗi cao khô Nhân sâm"
PACKAGING_PREFIX_RE = re.compile(
    r"^(?:mỗi\s+)?(?:ống|tuýp|túi|chai|lọ|gói|bút)\b(?:\s+\S+){0,3}?\s+(?:chứa|có)\s+"
    r"|^(?:mỗi|túi|chai|lọ|gói|ống|bút|tuýp)\s+(?:\d+(?:[.,]\d+)?\s*(?:g|mg|kg|ml|gam)\s+)?(?=cao\b)",  # "Mỗi 1g Cao khô X"
    re.I)
PACKAGING_PIECE_RE = re.compile(
    r"^(?:mỗi|tuýp|chai|lọ|gói|ống|bút|túi|sau khi|nồng độ|tỷ lệ|bào tử$)\b|\bbút chứa\b", re.I)
# Dose glued to a name: "Ezetimib10mg" -> "Ezetimib 10mg" (needs >=3 letters, so "B12" is untouched)
GLUED_DOSE_RE = re.compile(r"(?<=[A-Za-zÀ-ỹ]{3})(?=\d+(?:[.,]\d+)?\s*(?:mg|mcg|g|ml|iu|ui|%)(?![A-Za-zÀ-ỹ]))", re.I)
SPLIT_WORD_RE = re.compile(r"\s+(?:và|and|kết hợp với)\s+|\s*\+\s*", re.I)
# "Sacubitril/Valsartan" is a separator, "mg/ml" is not
SLASH_NAME_RE = re.compile(rf"(?<=[{LETTER}]{{3}})\s*/\s*(?=[A-ZÀ-Ỹ][{LETTER}]{{3}})")
CUT_MARKERS_RE = re.compile(
    r"\s(?:tương\s*đương|tương\s*ứng|dưới\s*dạng|dùng\s*dạng|tính\s*theo|quy\s*ra|hàm\s*lượng|"
    r"equivalent|equiv\.?|eq\.?|as)\b.*$", re.I)
ALT_MARKER_RE = re.compile(
    r"^\s*(?:tương\s*đương|tương\s*ứng|dưới\s*dạng|equivalent|as)\s*(?:với|to)?\s*:?\s*", re.I)

UNITS = (r"mg|mcg|mc|microgam|micrograms?|ug|ng|g|gam|kg|ml|l|lít|iu|ui|miu|mui|u|đvqt|đv|đơn vị|units?|"
         r"%|mmol|meq|mol|micro\s*katals?|mckatals?|katals?|usp|cfu|pfu|ffu|ccid50|tcid50|lf|mbq|mci|ppm|triệu|tỷ|"
         r"tế bào|log|w/w|w/v|v/v|kl/kl|kl/tt")
NUM = r"\d+(?:[.,\s]\d+)*"
DOSE_RE = re.compile(
    rf"(?<![{LETTER}\d]){NUM}\s*(?:{UNITS})(?![{LETTER}])"
    rf"(?:\s*/\s*(?:{NUM}\s*)?[{LETTER}]+(?:\s[{LETTER}]+)?)?", re.I)
TRAIL_NOISE_RE = re.compile(r"\s*/\s*(?:viên|gói|lọ|ống|ml|liều|nhát|túi|chai|tuýp)\b.*$", re.I)
VIT_LETTER_RE = re.compile(r"^(?:[A-K]\d{0,2}|PP)$")  # bare "C", "D3" after "Vitamin A, ..."
NOISE_PIECES = {"tá dược", "tá dược vừa đủ", "vừa đủ", "và", "các", "vitamin", ""}


@dataclass
class ParsedIngredient:
    name: str                                       # display name, e.g. "Losartan kali"
    alternates: list = field(default_factory=list)  # names found in "(dưới dạng/tương đương ...)"


def _mask(s: str) -> str:
    """Replace bracketed chars with '#' (same length) so regexes only see depth 0."""
    depth, out = 0, []
    for ch in s:
        if ch in OPEN:
            depth += 1
        out.append("#" if depth > 0 else ch)
        if ch in CLOSE and depth > 0:
            depth -= 1
    return "".join(out)


def _drop_brackets(s: str):
    """Remove (nested) bracketed content. Returns (text_without_brackets, inner_texts)."""
    out, inner, buf, depth = [], [], [], 0
    for ch in s:
        if ch in OPEN:
            depth += 1
            if depth == 1:
                buf = []
                continue
        elif ch in CLOSE and depth > 0:
            depth -= 1
            if depth == 0:
                inner.append("".join(buf))
                out.append(" ")
                continue
        (buf if depth > 0 else out).append(ch)
    if depth > 0:  # unbalanced "(" -> keep its tail as inner text
        inner.append("".join(buf))
    return "".join(out), inner


def _preclean(text: str) -> str:
    t = unicodedata.normalize("NFC", str(text))
    t = t.replace(" ", " ").replace("µ", "mc").replace("μ", "mc").replace("…", " ")
    t = re.sub(r"[\r\n]+", ";", t)
    t = GLUED_DOSE_RE.sub(" ", t)
    return HEADER_RE.sub("", t, count=1).strip()


def _split_top_level(t: str):
    """Split on ; and , : (unless between digits: "4,2mg", "1:1") at depth 0, then on và / + / Name/Name.

    ":" also separates mid-cell headers ("Bột mịn dược liệu gồm: Hương phụ") and "Cefoperazon : Sulbactam".
    """
    parts, buf, depth, n = [], [], 0, len(t)
    for i, ch in enumerate(t):
        if ch in OPEN:
            depth += 1
        elif ch in CLOSE:
            depth = max(0, depth - 1)
        between_digits = 0 < i < n - 1 and t[i - 1].isdigit() and t[i + 1].isdigit()
        if depth == 0 and (ch == ";" or (ch in ",:" and not between_digits)):
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    parts.append("".join(buf))

    pieces = []
    for p in parts:
        cut = CUT_MARKERS_RE.search(_mask(" " + p))  # "A và B tương đương A" -> drop tail first
        if cut:
            p = (" " + p)[:cut.start()]
        masked = _mask(p)
        seps = sorted((m.start(), m.end()) for rx in (SPLIT_WORD_RE, SLASH_NAME_RE) for m in rx.finditer(masked))
        last = 0
        for a, b in seps:
            if a >= last:
                pieces.append(p[last:a])
                last = b
        pieces.append(p[last:])
    return [s.strip() for s in pieces if s.strip()]


def _clean_name(text: str) -> str:
    """Strip prefixes, marker tails, doses and punctuation from one piece (no brackets)."""
    s = HEADER_RE.sub("", text, count=1)  # header inside a piece: "Mỗi 5ml chứa Calcium clorid"
    s = PACKAGING_PREFIX_RE.sub("", s.strip(), count=1)
    s = re.sub(r"^\s*(?:hỗn hợp|các|bột)\s+", "", s, flags=re.I)
    s = CUT_MARKERS_RE.sub("", " " + s)
    s = DOSE_RE.sub(" ", s)
    s = TRAIL_NOISE_RE.sub("", s)
    s = re.sub(r"(?<=\s)(?<!omega\s)\d[\d.,]*\b.*$", "", " " + s, flags=re.I)  # cut at first standalone number
    s = re.sub(r"^[\s\d.,:*\-–]+|[\s.,:;*\-–/)\]}]+$", "", s)  # trim punctuation / leading numbers
    s = re.sub(r"\s+", " ", s).strip()
    if VIT_LETTER_RE.match(s):
        return s
    if (s.lower() in NOISE_PIECES or GENERIC_HERBAL_RE.match(s) or HEADER_TAIL_RE.search(s)
            or PACKAGING_PIECE_RE.search(s) or not re.search(f"[{LETTER}]{{2,}}", s)):
        return ""
    return s


def _names_in_bracket(txt: str) -> list:
    """Bracket text -> cleaned names ("tương đương 1998 mg dược liệu: Hoàng kỳ 416 mg, ..." -> [Hoàng kỳ, ...])."""
    body = _drop_brackets(ALT_MARKER_RE.sub("", txt))[0]
    return [name for name in (_clean_name(p) for p in _split_top_level(body)) if name]


def _clean_piece(piece: str) -> list:
    """One top-level piece -> list[ParsedIngredient].

    Normal piece: one ingredient; "(dưới dạng/tương đương ...)" names become its alternates.
    Piece without a usable name:
      - generic herbal extract ("Cao đặc hỗn hợp dược liệu (tương đương ...: Hoàng kỳ, Cam thảo)",
        "Cao khô hỗn hợp (Nhân trần, Hoàng cầm)") -> every bracket's names become ingredients;
      - otherwise ("500mg (dưới dạng Amoxicilin trihydrat)") -> only "(dưới dạng/tương đương ...)" names do,
        so excipient lists like "Tá dược vừa đủ (lactose, ...)" are ignored.
    """
    no_br, inner = _drop_brackets(piece)
    name = _clean_name(no_br)
    if name:
        alternates = [alt for txt in inner if ALT_MARKER_RE.match(txt) for alt in _names_in_bracket(txt)]
        return [ParsedIngredient(name, alternates)]
    is_generic_extract = bool(GENERIC_HERBAL_RE.match(re.sub(r"\s+", " ", no_br).strip()))
    return [ParsedIngredient(herb) for txt in inner
            if is_generic_extract or ALT_MARKER_RE.match(txt) for herb in _names_in_bracket(txt)]


def parse_ingredients(text) -> list:
    """Free-text cell -> list[ParsedIngredient] (deduplicated, order kept)."""
    if text is None or (isinstance(text, float) and text != text) or not str(text).strip():
        return []
    result, seen, prev_vitamin = [], set(), False
    for piece in _split_top_level(_preclean(text)):
        for ing in _clean_piece(piece):
            if VIT_LETTER_RE.match(ing.name):  # "Vitamin A, C, D3" -> Vitamin C, Vitamin D3
                if not prev_vitamin:
                    continue
                ing.name = "Vitamin " + ing.name
            prev_vitamin = ing.name.lower().startswith("vitamin")
            if ing.name.lower() not in seen:
                seen.add(ing.name.lower())
                result.append(ing)
    return result
