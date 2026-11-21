"""Đọc các file CSV trong thư mục data/ thành KnowledgeBase (chạy một lần lúc khởi động, ~3 giây)."""
import csv
import logging
import sys
from collections.abc import Iterator
from pathlib import Path

from app.knowledge.models import (
    DiseaseWarning,
    Drug,
    FoodWarning,
    Ingredient,
    InteractionDetail,
    KnowledgeBase,
    Severity,
    pair_key,
)

logger = logging.getLogger(__name__)

MAPPING_FILE = "national-drug-ddinter-mapping.csv"
INTERACTIONS_FILE = "ddinter_interactions_final.csv"
DISEASE_FILE = "drug_disease_interactions.csv"
FOOD_FILE = "drug_food_interactions.csv"

REQUIRED_FILES = [MAPPING_FILE, INTERACTIONS_FILE, DISEASE_FILE, FOOD_FILE]


def load_knowledge_base(data_dir: Path) -> KnowledgeBase:
    missing = [name for name in REQUIRED_FILES if not (data_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Thiếu file dữ liệu trong {data_dir}: {', '.join(missing)} (xem data/README.md)")

    knowledge_base = KnowledgeBase(
        drugs=load_drugs(data_dir / MAPPING_FILE),
        interactions=load_interactions(data_dir / INTERACTIONS_FILE),
        disease_warnings=load_disease_warnings(data_dir / DISEASE_FILE),
        food_warnings=load_food_warnings(data_dir / FOOD_FILE),
    )
    logger.info(
        "Đã nạp %d thuốc, %d cặp tương tác, %d hoạt chất có lưu ý bệnh lý, %d hoạt chất có lưu ý thức ăn",
        len(knowledge_base.drugs),
        len(knowledge_base.interactions),
        len(knowledge_base.disease_warnings),
        len(knowledge_base.food_warnings),
    )
    return knowledge_base


def read_csv_rows(path: Path) -> Iterator[dict[str, str]]:
    # utf-8-sig: bỏ ký tự BOM ở đầu một số file
    with path.open(encoding="utf-8-sig", newline="") as file:
        yield from csv.DictReader(file)


def clean_text(value: str | None) -> str:
    """DDInter ghi 'None' hoặc '-' khi không có nội dung. Gộp chuỗi trùng để tiết kiệm bộ nhớ."""
    text = (value or "").strip()
    if text in ("None", "-"):
        return ""
    return sys.intern(text)


def load_drugs(path: Path) -> dict[str, Drug]:
    """Mỗi dòng của file map là một hoạt chất của một thuốc (theo số đăng ký)."""
    drugs: dict[str, Drug] = {}
    for row in read_csv_rows(path):
        registration_number = row["registration_number"].strip()
        if not registration_number:
            continue

        drug = drugs.get(registration_number)
        if drug is None:
            drug = Drug(registration_number=registration_number, name=row["drug_name"].strip())
            drugs[registration_number] = drug

        order = int(row["ingredient_order"] or 0)
        if order == 0:  # dòng 'no_ingredient': thuốc không ghi thành phần
            continue

        ddinter_id = row["ddinter_id"].strip() or None
        drug.ingredients.append(
            Ingredient(
                order=order,
                name=row["ingredient_name"].strip(),
                ddinter_id=ddinter_id,
                ddinter_name=row["ddinter_drug"].strip() if ddinter_id else None,
            )
        )
    return drugs


def load_interactions(path: Path) -> dict[tuple[str, str], InteractionDetail]:
    interactions: dict[tuple[str, str], InteractionDetail] = {}
    for row in read_csv_rows(path):
        key = pair_key(row["DDInterID_A"].strip(), row["DDInterID_B"].strip())
        interactions[key] = InteractionDetail(
            severity=Severity.from_ddinter(row["Level"]),
            description=clean_text(row["Interaction"]),
            management=clean_text(row["Management"]),
        )
    return interactions


def load_disease_warnings(path: Path) -> dict[str, list[DiseaseWarning]]:
    warnings: dict[str, list[DiseaseWarning]] = {}
    for row in read_csv_rows(path):
        ddinter_id = row["drug_id"].strip()
        if not ddinter_id:
            continue
        warnings.setdefault(ddinter_id, []).append(
            DiseaseWarning(
                severity=Severity.from_ddinter(row["severity"]),
                disease_name=row["disease_name"].strip(),
                description=clean_text(row["description"]),
            )
        )
    return warnings


def load_food_warnings(path: Path) -> dict[str, list[FoodWarning]]:
    warnings: dict[str, list[FoodWarning]] = {}
    for row in read_csv_rows(path):
        ddinter_id = row["drug_id"].strip()
        if not ddinter_id:
            continue
        warnings.setdefault(ddinter_id, []).append(
            FoodWarning(
                severity=Severity.from_ddinter(row["severity"]),
                food_name=row["food_name"].strip(),
                description=clean_text(row["description"]),
                management=clean_text(row["management"]),
                mechanism=clean_text(row["mechanism"]),
            )
        )
    return warnings
