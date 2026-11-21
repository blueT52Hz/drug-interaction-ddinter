"""Lưu ý bệnh lý / thức ăn theo từng thuốc."""
from app.knowledge.models import Drug, KnowledgeBase
from app.schemas.drug_warning import (
    DiseaseWarningItem,
    DrugWarnings,
    DrugWarningsResponse,
    FoodWarningItem,
    IngredientInfo,
)
from app.services.interaction_service import unique_in_order


def get_drug_warnings(knowledge_base: KnowledgeBase, registration_numbers: list[str]) -> DrugWarningsResponse:
    drugs: list[DrugWarnings] = []
    not_found: list[str] = []
    for registration_number in unique_in_order(registration_numbers):
        drug = knowledge_base.find_drug(registration_number)
        if drug is None:
            not_found.append(registration_number)
        else:
            drugs.append(build_drug_warnings(knowledge_base, drug))
    return DrugWarningsResponse(drugs=drugs, notFound=not_found)


def build_drug_warnings(knowledge_base: KnowledgeBase, drug: Drug) -> DrugWarnings:
    diseases: list[DiseaseWarningItem] = []
    foods: list[FoodWarningItem] = []
    for ingredient in drug.mapped_ingredients:
        for warning in knowledge_base.disease_warnings.get(ingredient.ddinter_id, []):
            diseases.append(
                DiseaseWarningItem(
                    ingredient=ingredient.ddinter_name,
                    severity=warning.severity,
                    diseaseName=warning.disease_name,
                    description=warning.description,
                )
            )
        for warning in knowledge_base.food_warnings.get(ingredient.ddinter_id, []):
            foods.append(
                FoodWarningItem(
                    ingredient=ingredient.ddinter_name,
                    severity=warning.severity,
                    foodName=warning.food_name,
                    description=warning.description,
                    management=warning.management,
                    mechanism=warning.mechanism,
                )
            )

    diseases.sort(key=lambda item: item.severity.rank, reverse=True)
    foods.sort(key=lambda item: item.severity.rank, reverse=True)
    return DrugWarnings(
        registrationNumber=drug.registration_number,
        name=drug.name,
        ingredients=[
            IngredientInfo(name=i.name, ddinterId=i.ddinter_id, ddinterName=i.ddinter_name) for i in drug.ingredients
        ],
        isFullyMapped=drug.is_fully_mapped,
        diseases=diseases,
        foods=foods,
    )
