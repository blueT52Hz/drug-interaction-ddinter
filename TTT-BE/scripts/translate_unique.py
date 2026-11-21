#!/usr/bin/env python3
"""Dịch file CSV lớn theo kiểu dedup: tách các đoạn unique -> dịch -> ghép lại.

File ddinter_interactions_final.csv có 234.981 dòng nhưng chỉ ~10.151 đoạn văn
unique (DDInter lặp cùng một đoạn cho nhiều cặp thuốc). Dịch theo đoạn unique
nhanh hơn ~23 lần số lần gọi model và ~42 lần lượng token.

Quy trình:

    # 1) Tách đoạn unique, sắp theo số lần xuất hiện giảm dần
    python scripts/translate_unique.py extract \
        --input data/ddinter_interactions_final.csv \
        --columns Interaction Management \
        --output unique_texts.csv

    # 2) Dịch unique_texts.csv trên Kaggle (cột 'text'), kết quả lưu thành
    #    CSV có 2 cột: text_id,translation  (giữ nguyên text_id)

    # 3) Ghép bản dịch trở lại file gốc, thêm cột <tên_cột>_vi
    python scripts/translate_unique.py apply \
        --input data/ddinter_interactions_final.csv \
        --columns Interaction Management \
        --unique unique_texts.csv \
        --translations unique_texts_translated.csv \
        --output data/ddinter_interactions_final_vi.csv

Có thể tách riêng từng cột (tổng token y hệt, mỗi phiên Kaggle ngắn hơn):

    python scripts/translate_unique.py extract --input data/ddinter_interactions_final.csv \
        --columns Interaction --output interaction_unique_texts.csv
    python scripts/translate_unique.py extract --input data/ddinter_interactions_final.csv \
        --columns Management --output management_unique_texts.csv

    # ... dịch 2 file trên Kaggle ...

    python scripts/translate_unique.py apply \
        --input data/ddinter_interactions_final.csv \
        --columns Interaction Management \
        --unique interaction_unique_texts.csv management_unique_texts.csv \
        --translations interaction_vi.csv management_vi.csv \
        --output data/ddinter_interactions_final_vi.csv

Với --columns A B, có thể truyền 1 file (áp dụng cho mọi cột) hoặc đúng bằng
số cột (mỗi cột một file, theo đúng thứ tự).

Cột text_id trong file unique ổn định (không đổi giữa các lần chạy) nên có thể
chia nhỏ file unique để dịch nhiều phiên Kaggle rồi ghép lại.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

PLACEHOLDERS = {"", "None", "-"}


def clean(value: str | None) -> str:
    """DDInter ghi 'None' / '-' khi không có nội dung."""
    text = (value or "").strip()
    return "" if text in PLACEHOLDERS else text


def read_csv_rows(path: Path) -> tuple[list[str], "csv.DictReader"]:
    file = path.open(encoding="utf-8-sig", newline="")
    reader = csv.DictReader(file)
    return list(reader.fieldnames or []), reader, file


def write_csv_atomic(path: Path, fieldnames: list[str], rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp_path, path)


def cmd_extract(args: argparse.Namespace) -> int:
    columns = args.columns
    counts: dict[str, int] = {}
    first_seen: dict[str, int] = {}

    fieldnames, reader, file = read_csv_rows(args.input)
    try:
        missing = [c for c in columns if c not in fieldnames]
        if missing:
            sys.exit(f"Không có cột {missing} trong {args.input} (cột hiện có: {fieldnames})")
        n_rows = 0
        for row in reader:
            n_rows += 1
            for column in columns:
                text = clean(row.get(column))
                if not text:
                    continue
                if text not in counts:
                    first_seen[text] = len(first_seen)
                    counts[text] = 0
                counts[text] += 1
    finally:
        file.close()

    # Sắp theo tần suất giảm dần: lỡ phiên Kaggle dừng giữa chừng thì các đoạn
    # đã dịch vẫn phủ được nhiều dòng nhất.
    ordered = sorted(counts, key=lambda t: (-counts[t], first_seen[t]))
    rows = [
        {"text_id": i, "n_rows": counts[text], "text": text}
        for i, text in enumerate(ordered, start=1)
    ]
    write_csv_atomic(args.output, ["text_id", "n_rows", "text"], rows)

    covered = sum(counts.values())
    print(f"Đọc {n_rows:,} dòng, cột {', '.join(columns)}")
    print(f"Đoạn unique: {len(rows):,}  (tổng lần xuất hiện: {covered:,})")
    print(f"Đã ghi {args.output}")
    print(f"Top 5 đoạn lặp nhiều nhất: " + ", ".join(f"#{i} ({counts[t]:,} lần)" for i, t in enumerate(ordered[:5], 1)))
    return 0


def _load_translation_map(unique_path: Path, translations_path: Path) -> tuple[dict[str, str], int]:
    """Trả về ({text gốc: bản dịch}, số đoạn chưa có bản dịch)."""
    # 1) text_id -> text gốc
    ids_to_text: dict[str, str] = {}
    fieldnames, reader, file = read_csv_rows(unique_path)
    try:
        for row in reader:
            text_id = (row.get("text_id") or "").strip()
            text = row.get("text")
            if text_id and text is not None:
                ids_to_text[text_id] = text
    finally:
        file.close()

    # 2) text_id -> bản dịch
    translations: dict[str, str] = {}
    fieldnames, reader, file = read_csv_rows(translations_path)
    try:
        if "text_id" not in fieldnames:
            sys.exit(f"File {translations_path} thiếu cột text_id")
        translation_col = next(
            (c for c in ("translation", "translated", "text_vi", "vi") if c in fieldnames),
            None,
        )
        in_place = False
        if translation_col is None and "text" in fieldnames:
            # Code dịch ghi đè ngay vào cột 'text' thay vì thêm cột mới
            translation_col = "text"
            in_place = True
        if translation_col is None:
            sys.exit(f"File {translations_path} cần một cột bản dịch (translation/translated/text_vi/vi, hoặc 'text' nếu dịch tại chỗ); cột hiện có: {fieldnames}")
        print(f"{translations_path.name}: cột bản dịch '{translation_col}'" + (" (dịch tại chỗ)" if in_place else ""))
        for row in reader:
            text_id = (row.get("text_id") or "").strip()
            if text_id:
                translations[text_id] = (row.get(translation_col) or "").strip()
    finally:
        file.close()

    # 3) text gốc -> bản dịch
    text_to_translation: dict[str, str] = {}
    empty = 0
    for text_id, text in ids_to_text.items():
        translation = translations.get(text_id)
        if translation is None:
            empty += 1
            continue
        text_to_translation[text] = translation
    if empty:
        print(f"CẢNH BÁO: {empty}/{len(ids_to_text)} đoạn chưa có bản dịch trong {translations_path.name}; các ô đó để trống")
    unchanged = sum(1 for text_id, text in ids_to_text.items() if translations.get(text_id) == text)
    if unchanged:
        print(f"CẢNH BÁO: {unchanged} đoạn trong {translations_path.name} có bản dịch giống hệt bản gốc (có thể chưa dịch)")
    extra = len(set(translations) - set(ids_to_text))
    if extra:
        print(f"CẢNH BÁO: {extra} text_id trong {translations_path.name} không có trong {unique_path.name} (sai file?)")
    return text_to_translation, empty


def cmd_apply(args: argparse.Namespace) -> int:
    columns = args.columns
    if len(args.unique) not in (1, len(columns)) or len(args.translations) not in (1, len(columns)):
        sys.exit("--unique và --translations phải có 1 file (áp dụng cho mọi cột) hoặc đúng bằng số cột")
    uniques = args.unique * len(columns) if len(args.unique) == 1 else args.unique
    translation_files = args.translations * len(columns) if len(args.translations) == 1 else args.translations

    # Mỗi cột một từ điển text gốc -> bản dịch
    maps: list[dict[str, str]] = []
    empty_total = 0
    for column, unique_path, translations_path in zip(columns, uniques, translation_files):
        print(f"[{column}] ghép từ {translations_path.name}")
        text_map, empty = _load_translation_map(unique_path, translations_path)
        maps.append(text_map)
        empty_total += empty

    # Ghi file gốc + cột _vi, giữ nguyên mọi cột khác
    suffix = args.suffix
    fieldnames, reader, file = read_csv_rows(args.input)
    try:
        missing_cols = [c for c in columns if c not in fieldnames]
        if missing_cols:
            sys.exit(f"Không có cột {missing_cols} trong {args.input}")
        out_fields = fieldnames + [c + suffix for c in columns]

        args.output.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = args.output.with_suffix(args.output.suffix + ".tmp")
        n_rows = n_translated = 0
        with tmp_path.open("w", encoding="utf-8", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=out_fields)
            writer.writeheader()
            for row in reader:
                out_row = {c: row.get(c, "") for c in fieldnames}
                for column, text_map in zip(columns, maps):
                    text = clean(row.get(column))
                    translation = text_map.get(text, "") if text else ""
                    out_row[column + suffix] = translation
                    if translation:
                        n_translated += 1
                writer.writerow(out_row)
                n_rows += 1
        os.replace(tmp_path, args.output)
    finally:
        file.close()

    print(f"Đọc {n_rows:,} dòng, ghi {n_translated:,} ô dịch vào {args.output}")
    print(f"Cột thêm vào: {', '.join(c + suffix for c in columns)}")
    return 1 if empty_total else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    sub = parser.add_subparsers(dest="command", required=True)

    p_ex = sub.add_parser("extract", help="Tách các đoạn unique ra file nhỏ để dịch")
    p_ex.add_argument("--input", type=Path, required=True)
    p_ex.add_argument("--columns", nargs="+", required=True)
    p_ex.add_argument("--output", type=Path, required=True)
    p_ex.set_defaults(func=cmd_extract)

    p_ap = sub.add_parser("apply", help="Ghép bản dịch trở lại file gốc")
    p_ap.add_argument("--input", type=Path, required=True)
    p_ap.add_argument("--columns", nargs="+", required=True)
    p_ap.add_argument("--unique", type=Path, nargs="+", required=True,
                      help="1 file cho mọi cột, hoặc mỗi cột 1 file (đúng thứ tự --columns)")
    p_ap.add_argument("--translations", type=Path, nargs="+", required=True,
                      help="1 file cho mọi cột, hoặc mỗi cột 1 file (đúng thứ tự --columns)")
    p_ap.add_argument("--output", type=Path, required=True)
    p_ap.add_argument("--suffix", default="_vi", help="hậu tố cột bản dịch (mặc định: _vi)")
    p_ap.set_defaults(func=cmd_apply)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
