"""Build a long-format CSV mapping active ingredients of national_drug.xlsx to DDInter drugs.

One output row per (registered drug x parsed ingredient); drugs with no parsable ingredient
get a single row with match_method = no_ingredient.

Usage (from repo root):
    python ingredient-mapping/build-national-drug-ddinter-mapping.py [--output PATH]
"""
import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from administration_route_inference import infer_route
from ddinter_name_matcher import DDInterNameMatcher, MatchResult
from ingredient_text_parser import parse_ingredients

PROJECT_ROOT = Path(__file__).resolve().parents[1]  # repo root (this file lives in ingredient-mapping/)
SHEET_NAME = "DanhSach"
# Source headers after whitespace cleanup (raw headers contain trailing spaces / newlines)
COL_REG_NO = "Số đăng ký lưu hành (*)"
COL_NAME = "Tên thuốc (*)"
COL_GROUP = "Nhóm thuốc (*)"
COL_INGREDIENTS = "Thành phần"
COL_PACKAGING = "Quy cách đóng gói"
REQUIRED_COLUMNS = (COL_REG_NO, COL_NAME, COL_GROUP, COL_INGREDIENTS, COL_PACKAGING)

OUTPUT_COLUMNS = [
    "registration_number", "drug_name", "drug_group", "inferred_route", "ingredient_text_raw",
    "ingredient_order", "ingredient_name", "ingredient_alternates", "match_method", "ddinter_id",
    "ddinter_drug", "confidence", "needs_review", "suggested_ddinter_id", "suggested_ddinter_drug",
    "suggested_score",
]


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--xlsx", default=PROJECT_ROOT / "data" / "national_drug.xlsx", type=Path)
    p.add_argument("--ddinter", default=PROJECT_ROOT / "data" / "ddinter" / "ddinter_drug_list.csv", type=Path)
    p.add_argument("--synonyms", default=PROJECT_ROOT / "data" / "mapping" / "vietnamese-ingredient-ddinter-synonyms.csv",
                   type=Path)
    p.add_argument("--output", default=PROJECT_ROOT / "data" / "mapping" / "national-drug-ddinter-mapping.csv", type=Path)
    return p.parse_args()


def load_national_drugs(xlsx_path: Path) -> pd.DataFrame:
    # dtype=str keeps leading zeros of registration numbers (e.g. 001110009924)
    df = pd.read_excel(xlsx_path, sheet_name=SHEET_NAME, dtype=str, engine="openpyxl")
    df.columns = [" ".join(str(c).split()) for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in sheet {SHEET_NAME}: {missing}")
    return df[list(REQUIRED_COLUMNS)].fillna("")


def mapping_rows(df: pd.DataFrame, matcher: DDInterNameMatcher):
    """Yield output dicts, one per drug x ingredient."""
    for reg_no, name, group, ingredients_text, packaging in df.itertuples(index=False, name=None):
        route = infer_route(name, packaging)
        base = {"registration_number": reg_no.strip(), "drug_name": name.strip(), "drug_group": group.strip(),
                "inferred_route": route or "", "ingredient_text_raw": ingredients_text.strip()}
        ingredients = parse_ingredients(ingredients_text)
        if not ingredients:
            yield {**base, **_result_fields(MatchResult("no_ingredient")), "ingredient_order": 0,
                   "ingredient_name": "", "ingredient_alternates": ""}
            continue
        for order, ing in enumerate(ingredients, start=1):
            result = matcher.match(ing.name, tuple(ing.alternates), route)
            yield {**base, **_result_fields(result), "ingredient_order": order, "ingredient_name": ing.name,
                   "ingredient_alternates": " | ".join(ing.alternates)}


def _result_fields(r: MatchResult) -> dict:
    return {"match_method": r.method, "ddinter_id": r.ddinter_id, "ddinter_drug": r.ddinter_drug,
            "confidence": r.confidence or "", "needs_review": r.needs_review,
            "suggested_ddinter_id": r.suggested_ddinter_id, "suggested_ddinter_drug": r.suggested_ddinter_drug,
            "suggested_score": r.suggested_score or ""}


def print_summary(rows: list, matcher: DDInterNameMatcher):
    methods = Counter(r["match_method"] for r in rows)
    per_drug = {}
    for r in rows:
        if r["match_method"] != "no_ingredient":
            per_drug.setdefault(r["registration_number"], []).append(bool(r["ddinter_id"]))
    n_drugs = len(per_drug) or 1
    print(f"Output rows: {len(rows):,}")
    for method, count in methods.most_common():
        print(f"  {method:<18} {count:>7,} ({count / len(rows):.1%})")
    print(f"Drugs with ingredients: {len(per_drug):,}")
    print(f"  all ingredients matched : {sum(all(v) for v in per_drug.values()) / n_drugs:.1%}")
    print(f"  >=1 ingredient matched  : {sum(any(v) for v in per_drug.values()) / n_drugs:.1%}")
    print(f"Rows needing review: {sum(1 for r in rows if r['needs_review']):,}")
    for source, target in matcher.invalid_synonyms:
        print(f"WARNING: synonym target not in DDInter: {source!r} -> {target!r}", file=sys.stderr)


def main():
    args = parse_args()
    try:
        matcher = DDInterNameMatcher(str(args.ddinter), str(args.synonyms) if args.synonyms.exists() else None)
        df = load_national_drugs(args.xlsx)
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    rows = list(mapping_rows(df, matcher))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig so Excel displays Vietnamese characters correctly
    with open(args.output, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {args.output}")
    print_summary(rows, matcher)
    return 0


if __name__ == "__main__":
    sys.exit(main())
