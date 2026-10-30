"""Match a parsed ingredient name to a DDInter drug.

Deterministic tiers (first hit wins), tried on the main name then on bracket alternates:
  synonym          manual dictionary (data/mapping/vietnamese-ingredient-ddinter-synonyms.csv)
  exact            normalized key equals a DDInter name (route suffix ignored)
  salt_stripped    after removing salt/hydrate words
  spelling_variant after Vietnamese -> English spelling rules
  alternate_name   one of the above, on "(dưới dạng/tương đương X)" text
Unmatched names get a rapidfuzz suggestion only (never auto-accepted: fuzzy produced
many false hits such as Spiramycin -> Plicamycin during analysis).
"""
import csv
import re
from dataclasses import dataclass
from functools import lru_cache

from rapidfuzz import fuzz, process

from drug_name_normalizer import (base_key, extract_prefix_stripped, has_vietnamese_diacritics, salt_stripped,
                                  spelling_variants)

DD_SUFFIX_RE = re.compile(r"\s*\(([^()]*)\)\s*$")
SUFFIX_TO_ROUTE = {"topical": "topical", "topiclal": "topical", "ophthalmic": "ophthalmic",
                   "nasal": "nasal", "otic": "otic"}
TIER_CONFIDENCE = {"synonym": 100, "exact": 100, "salt_stripped": 95, "spelling_variant": 90}
ALTERNATE_CONFIDENCE = 85
FUZZY_CUTOFF = 88  # lower values suggested Spiramycin -> Plicamycin, Vitamin B1 -> Vitamin A


def _related_alternates(name: str, alternates: tuple) -> list:
    """Keep only alternates that describe the same substance as `name`.

    Brackets often list a whole mixture: "Cilastatin (dưới dạng hỗn hợp Imipenem, Cilastatin natri,
    Natri bicarbonat)" must not map Cilastatin -> Imipenem. An alternate is related when it contains the
    first word of the name ("Cilastatin natri"); a single alternate is trusted as is
    ("Vitamin A (dưới dạng Retinyl palmitat)").
    """
    first_word = extract_prefix_stripped(base_key(name)).split(" ")[0]  # "Dried aluminum hydroxide gel" -> "aluminum"
    related = [a for a in alternates if len(first_word) >= 3 and first_word in base_key(a).split(" ")]
    return related or (list(alternates) if len(alternates) == 1 else [])


@dataclass
class MatchResult:
    method: str
    ddinter_id: str = ""
    ddinter_drug: str = ""
    confidence: int = 0
    needs_review: bool = False
    suggested_ddinter_id: str = ""
    suggested_ddinter_drug: str = ""
    suggested_score: float = 0.0


class DDInterNameMatcher:
    def __init__(self, ddinter_csv_path: str, synonyms_csv_path: str | None = None):
        self.id_by_name = {}
        self.variants_by_base = {}   # base key -> [(ddinter name, route or None, has_suffix)]
        with open(ddinter_csv_path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                self._add_ddinter_name(row["Drug"].strip(), row["DDInterID"].strip())
        self.base_keys = list(self.variants_by_base)
        self.synonyms = {}           # source key -> exact DDInter name
        self.invalid_synonyms = []   # rows whose target is not in DDInter
        if synonyms_csv_path:
            self._load_synonyms(synonyms_csv_path)

    def _add_ddinter_name(self, name: str, ddinter_id: str):
        self.id_by_name[name] = ddinter_id
        key = base_key(name)
        m = DD_SUFFIX_RE.search(key)
        base = DD_SUFFIX_RE.sub("", key).strip()
        route = SUFFIX_TO_ROUTE.get(m.group(1).strip()) if m else None
        self.variants_by_base.setdefault(base, []).append((name, route, bool(m)))

    def _load_synonyms(self, path: str):
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                source, target = (row.get("source_name") or "").strip(), (row.get("ddinter_drug") or "").strip()
                if not source or not target:
                    continue
                if target in self.id_by_name:
                    self.synonyms[base_key(source)] = target
                else:
                    self.invalid_synonyms.append((source, target))

    def _pick_variant(self, base: str, route: str | None):
        """Choose among DDInter route variants. Returns (name, needs_review).

        Order: same-route variant > plain name > fallback. A fallback is flagged for review when
        there were several candidates or its route differs from the inferred one
        (e.g. nasal drug -> "Sulfacetamide (ophthalmic)", unknown route -> "Naphazoline (nasal)").
        """
        variants = self.variants_by_base[base]
        if route:
            for name, r, _ in variants:
                if r == route:
                    return name, False
        plain = [name for name, _, has_suffix in variants if not has_suffix]
        if plain:
            return plain[0], False
        non_route = [(name, r) for name, r, _ in variants if r is None]
        name, picked_route = (non_route or [(n, r) for n, r, _ in variants])[0]
        return name, len(variants) > 1 or (picked_route is not None and picked_route != route)

    def _resolve_synonym_target(self, target: str, route: str | None):
        if DD_SUFFIX_RE.search(target):          # explicit variant chosen by the dictionary author
            return target, False
        base = base_key(target)
        return self._pick_variant(base, route) if base in self.variants_by_base else (target, False)

    def _match_deterministic(self, name: str, route: str | None):
        """Return (tier, ddinter_name, ambiguous) or None."""
        full_key = base_key(name)
        # also try without herbal-extract prefix: "Cao khô Nhân sâm" -> "nhan sam"
        keys = list(dict.fromkeys((full_key, extract_prefix_stripped(full_key))))
        stripped_keys = list(dict.fromkeys(salt_stripped(k) for k in keys))
        for cand in dict.fromkeys(keys + stripped_keys):
            if cand in self.synonyms:
                return ("synonym", *self._resolve_synonym_target(self.synonyms[cand], route))
        for tier, candidates in (("exact", keys), ("salt_stripped", stripped_keys)):
            for cand in candidates:
                if cand in self.variants_by_base:
                    return (tier, *self._pick_variant(cand, route))
        for cand in dict.fromkeys(keys + stripped_keys):
            for variant in spelling_variants(cand):
                if variant in self.variants_by_base:
                    return ("spelling_variant", *self._pick_variant(variant, route))
        return None

    def _fuzzy_suggestion(self, name: str):
        """Best fuzzy candidate; skipped for Vietnamese-diacritic (mostly herbal) names."""
        if has_vietnamese_diacritics(name):
            return None
        hit = process.extractOne(base_key(name), self.base_keys, scorer=fuzz.ratio, score_cutoff=FUZZY_CUTOFF)
        if not hit:
            return None
        ddinter_name, _ = self._pick_variant(hit[0], None)
        return ddinter_name, round(hit[1], 1)

    @lru_cache(maxsize=None)
    def match(self, name: str, alternates: tuple = (), route: str | None = None) -> MatchResult:
        hit = self._match_deterministic(name, route)
        if hit:
            tier, ddinter_name, ambiguous = hit
            confidence = TIER_CONFIDENCE[tier]
        else:
            related = _related_alternates(name, alternates)
            hit = next((h for h in (self._match_deterministic(a, route) for a in related) if h), None)
            if hit:
                tier, ddinter_name, ambiguous = "alternate_name", hit[1], hit[2]
                confidence = ALTERNATE_CONFIDENCE
        if hit:
            return MatchResult(tier, self.id_by_name[ddinter_name], ddinter_name, confidence, ambiguous)

        suggestion = self._fuzzy_suggestion(name)
        if suggestion:
            return MatchResult("fuzzy_suggestion", needs_review=True,
                               suggested_ddinter_id=self.id_by_name[suggestion[0]],
                               suggested_ddinter_drug=suggestion[0], suggested_score=suggestion[1])
        return MatchResult("no_match")
