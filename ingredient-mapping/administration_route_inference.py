"""Infer administration route from drug name + packaging text.

`Đường dùng` in national_drug.xlsx is 100% empty, but DDInter splits some drugs by route
(e.g. "Acyclovir" vs "Acyclovir (topical)"), so the route is guessed from keywords in
`Tên thuốc` and `Quy cách đóng gói`. Returns one of ROUTES or None.
"""
import re
import unicodedata

# Checked in order: specific routes first, generic "topical" last.
ROUTE_PATTERNS = (
    ("ophthalmic", r"nhỏ mắt|tra mắt|thuốc mắt|mỡ mắt|\beye\b|ophthalmic"),  # "Eye/Ear Drops" -> ophthalmic
    ("otic", r"nhỏ tai|\botic\b|ear drops?"),  # \b: avoid "Amoxybiotic", "Neotica"
    ("nasal", r"xịt mũi|nhỏ mũi|phun mù mũi|nasal"),
    ("topical", r"\bkem\b|\bgel\b|thuốc mỡ|mỡ bôi|\bbôi\b|dùng ngoài|dầu xoa|dầu gió|lotion|cream|"
                r"ointment|nhũ tương bôi|dung dịch bôi|\bcồn\b|thuốc rửa|dầu gội|sữa tắm|topical"),
)
_COMPILED = [(route, re.compile(pattern, re.I)) for route, pattern in ROUTE_PATTERNS]
ROUTES = tuple(route for route, _ in ROUTE_PATTERNS)


def infer_route(*texts) -> str | None:
    """Return the first route whose keywords appear in any of the given texts."""
    joined = " ".join(unicodedata.normalize("NFC", str(t)) for t in texts if t is not None and t == t)
    for route, rx in _COMPILED:
        if rx.search(joined):
            return route
    return None
