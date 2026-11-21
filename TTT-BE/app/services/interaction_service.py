"""Kiểm tra tương tác giữa các thuốc trong giỏ hàng."""
from datetime import datetime, timezone

from app.knowledge.models import Drug, Ingredient, KnowledgeBase, Severity, pair_key
from app.schemas.common import DrugRef
from app.schemas.interaction import DuplicateIngredient, InteractionCheckResponse, InteractionPair


def unique_in_order(values: list[str]) -> list[str]:
    """Bỏ số đăng ký trùng (thêm cùng một thuốc 2 lần), giữ thứ tự gửi lên."""
    return list(dict.fromkeys(values))


def to_drug_ref(drug: Drug) -> DrugRef:
    return DrugRef(registrationNumber=drug.registration_number, name=drug.name)


def check_interactions(knowledge_base: KnowledgeBase, registration_numbers: list[str]) -> InteractionCheckResponse:
    drugs: list[Drug] = []
    not_found: list[str] = []
    for registration_number in unique_in_order(registration_numbers):
        drug = knowledge_base.find_drug(registration_number)
        if drug is None:
            not_found.append(registration_number)
        else:
            drugs.append(drug)

    interactions = find_interaction_pairs(knowledge_base, drugs)
    return InteractionCheckResponse(
        interactions=interactions,
        duplicates=find_duplicate_ingredients(drugs),
        hasMajor=any(pair.severity == Severity.MAJOR for pair in interactions),
        notFound=not_found,
        incomplete=[drug.registration_number for drug in drugs if not drug.is_fully_mapped],
        checkedAt=datetime.now(timezone.utc),
    )


def find_interaction_pairs(knowledge_base: KnowledgeBase, drugs: list[Drug]) -> list[InteractionPair]:
    """So từng cặp thuốc khác nhau, rồi từng cặp hoạt chất của hai thuốc đó."""
    pairs: list[InteractionPair] = []
    for index, first_drug in enumerate(drugs):
        for second_drug in drugs[index + 1 :]:
            for first_ingredient in first_drug.mapped_ingredients:
                for second_ingredient in second_drug.mapped_ingredients:
                    pair = build_pair(knowledge_base, first_drug, first_ingredient, second_drug, second_ingredient)
                    if pair is not None:
                        pairs.append(pair)

    # Nặng trước; cùng mức thì giữ thứ tự thuốc trong giỏ
    pairs.sort(key=lambda pair: pair.severity.rank, reverse=True)
    return pairs


def build_pair(
    knowledge_base: KnowledgeBase,
    first_drug: Drug,
    first_ingredient: Ingredient,
    second_drug: Drug,
    second_ingredient: Ingredient,
) -> InteractionPair | None:
    # Cùng hoạt chất không phải tương tác — đã báo ở phần trùng hoạt chất
    if first_ingredient.ddinter_id == second_ingredient.ddinter_id:
        return None

    detail = knowledge_base.find_interaction(first_ingredient.ddinter_id, second_ingredient.ddinter_id)
    if detail is None:
        return None

    low_id, high_id = pair_key(first_ingredient.ddinter_id, second_ingredient.ddinter_id)
    return InteractionPair(
        id=f"ddi:{low_id}:{high_id}",
        severity=detail.severity,
        drug1=to_drug_ref(first_drug),
        drug2=to_drug_ref(second_drug),
        ingredient1=first_ingredient.ddinter_name,
        ingredient2=second_ingredient.ddinter_name,
        description=detail.description,
        management=detail.management,
    )


def find_duplicate_ingredients(drugs: list[Drug]) -> list[DuplicateIngredient]:
    """Gom thuốc theo hoạt chất; hoạt chất nào có từ 2 thuốc trở lên là trùng."""
    drugs_by_ingredient: dict[str, list[Drug]] = {}
    ingredient_names: dict[str, str] = {}
    for drug in drugs:
        for ingredient in drug.mapped_ingredients:
            same_ingredient = drugs_by_ingredient.setdefault(ingredient.ddinter_id, [])
            if drug not in same_ingredient:
                same_ingredient.append(drug)
            ingredient_names[ingredient.ddinter_id] = ingredient.ddinter_name

    return [
        DuplicateIngredient(
            id=f"dup:{ddinter_id}",
            ingredient=ingredient_names[ddinter_id],
            drugs=[to_drug_ref(drug) for drug in same_ingredient],
        )
        for ddinter_id, same_ingredient in drugs_by_ingredient.items()
        if len(same_ingredient) >= 2
    ]
