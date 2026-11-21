"""Dữ liệu nhỏ dựng tay cho test — không cần file CSV thật."""
import pytest
from fastapi.testclient import TestClient

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
from app.main import create_app


def ingredient(order: int, ddinter_id: str | None, name: str) -> Ingredient:
    return Ingredient(order=order, name=name, ddinter_id=ddinter_id, ddinter_name=name if ddinter_id else None)


@pytest.fixture
def knowledge_base() -> KnowledgeBase:
    drugs = [
        Drug("REG-WARFARIN", "Warfarin 5mg", [ingredient(1, "DD1", "Warfarin")]),
        Drug("REG-ASPIRIN", "Aspirin 81mg", [ingredient(1, "DD2", "Aspirin")]),
        Drug("REG-PARA", "Panadol", [ingredient(1, "DD3", "Acetaminophen")]),
        # Thuốc phối hợp: Paracetamol + Cafein — trùng hoạt chất với Panadol
        Drug("REG-PARA-CAF", "Panadol Extra", [ingredient(1, "DD3", "Acetaminophen"), ingredient(2, "DD4", "Caffeine")]),
        # Còn một hoạt chất chưa map
        Drug("REG-PARTIAL", "Thuốc nửa map", [ingredient(1, "DD2", "Aspirin"), ingredient(2, None, "Cao lá xyz")]),
        Drug("REG-EMPTY", "Thuốc không ghi thành phần", []),
    ]
    return KnowledgeBase(
        drugs={drug.registration_number: drug for drug in drugs},
        interactions={
            pair_key("DD1", "DD2"): InteractionDetail(Severity.MAJOR, "Increased bleeding risk.", "Avoid combination."),
            pair_key("DD3", "DD1"): InteractionDetail(Severity.MODERATE, "May increase INR.", "Monitor INR."),
            pair_key("DD4", "DD2"): InteractionDetail(Severity.UNKNOWN, "", ""),
        },
        disease_warnings={"DD2": [DiseaseWarning(Severity.MAJOR, "Peptic Ulcer", "GI bleeding.")]},
        food_warnings={"DD1": [FoodWarning(Severity.MODERATE, "spinach", "Vitamin K.", "Keep intake steady.", "")]},
    )


@pytest.fixture
def client(knowledge_base: KnowledgeBase):
    with TestClient(create_app(knowledge_base)) as test_client:
        yield test_client
