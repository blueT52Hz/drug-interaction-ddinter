"""
Parse a DDInter 2.0 interaction page (https://ddinter2.scbdd.com/server/interact/<id>/).

The page holds a key/value table: <td class="key">Label</td><td class="value">...</td>.
We extract:
    ID          -> "DDInter90 and DDInter1" (two links to /server/drug-detail/<DDInterID>/)
    Interaction -> free text
    Management  -> free text ("-" when the site has none)
"""

import re

from bs4 import BeautifulSoup

DDINTER_ID_RE = re.compile(r"DDInter\d+")
RECORD_FIELDS = ["InteractionID", "DDInterID_A", "DDInterID_B", "Interaction", "Management"]


def _clean_text(element) -> str:
    """Collapse all whitespace (the HTML is heavily indented) into single spaces."""
    return " ".join(element.get_text(" ").split()) if element else ""


def _find_value_cell(soup, label: str):
    """Return the <td class="value"> next to the <td class="key"> whose text equals label."""
    for key_cell in soup.select("td.key"):
        if _clean_text(key_cell) == label:
            return key_cell.find_next_sibling("td")
    return None


def parse_interaction_page(html: str, interaction_id: int):
    """
    Return a dict with RECORD_FIELDS, or None if the page doesn't look like an
    interaction page (e.g. blocked / captcha / error page).
    """
    soup = BeautifulSoup(html, "html.parser")
    id_cell = _find_value_cell(soup, "ID")
    if id_cell is None:
        return None

    # Prefer the drug-detail links; fall back to regex over the cell text
    drug_ids = [DDINTER_ID_RE.search(a.get("href", "")) for a in id_cell.find_all("a")]
    drug_ids = [m.group(0) for m in drug_ids if m] or DDINTER_ID_RE.findall(_clean_text(id_cell))
    if len(drug_ids) != 2:
        return None

    return {
        "InteractionID": interaction_id,
        "DDInterID_A": drug_ids[0],
        "DDInterID_B": drug_ids[1],
        "Interaction": _clean_text(_find_value_cell(soup, "Interaction")),
        "Management": _clean_text(_find_value_cell(soup, "Management")),
    }
