"""Đọc CSV mẫu nhỏ đúng định dạng file thật."""
import pytest

from app.knowledge.loader import load_knowledge_base
from app.knowledge.models import Severity


def write(path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def data_dir(tmp_path):
    write(
        tmp_path / "national-drug-ddinter-mapping.csv",
        "﻿registration_number,drug_name,drug_group,inferred_route,ingredient_text_raw,ingredient_order,"
        "ingredient_name,ingredient_alternates,match_method,ddinter_id,ddinter_drug,confidence,needs_review,"
        "suggested_ddinter_id,suggested_ddinter_drug,suggested_score\n"
        "VD-1,Thuoc A,Hóa dược,,Abacavir 300mg,1,Abacavir,,exact,DDInter1,Abacavir,1,False,,,\n"
        "VD-1,Thuoc A,Hóa dược,,Abacavir 300mg,2,Cao xyz,,no_match,,,,False,,,\n"
        "VD-2,Thuoc B,Hóa dược,,,0,,,no_ingredient,,,,False,,,\n",
    )
    write(
        tmp_path / "ddinter_interactions_final.csv",
        "InteractionID,DDInterID_A,Drug_A,DDInterID_B,Drug_B,Level,Interaction,Management\n"
        "1,DDInter2,B,DDInter1,Abacavir,Major,Some text,-\n",
    )
    write(
        tmp_path / "drug_disease_interactions.csv",
        "﻿id,drug_id,drug_name,level,severity,disease_name,description,references\n"
        "1,DDInter1,Abacavir,3,Major,Liver Diseases,Hepatotoxicity,ref\n",
    )
    write(
        tmp_path / "drug_food_interactions.csv",
        "﻿id,drug_id,drug_name,level,severity,food_name,description,management,mechanism,references\n",
    )
    return tmp_path


def test_load_knowledge_base(data_dir):
    knowledge_base = load_knowledge_base(data_dir)

    drug = knowledge_base.find_drug("VD-1")
    assert drug.name == "Thuoc A"
    assert [i.ddinter_id for i in drug.ingredients] == ["DDInter1", None]
    assert drug.is_fully_mapped is False

    assert knowledge_base.find_drug("VD-2").ingredients == []

    detail = knowledge_base.find_interaction("DDInter1", "DDInter2")
    assert detail.severity == Severity.MAJOR
    assert detail.management == ""  # '-' nghĩa là không có

    assert knowledge_base.disease_warnings["DDInter1"][0].disease_name == "Liver Diseases"
    assert knowledge_base.food_warnings == {}


def test_missing_file_raises_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="Thiếu file dữ liệu"):
        load_knowledge_base(tmp_path)
