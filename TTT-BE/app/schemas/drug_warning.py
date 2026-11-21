from pydantic import BaseModel

from app.knowledge.models import Severity


class IngredientInfo(BaseModel):
    name: str
    ddinterId: str | None
    ddinterName: str | None


class DiseaseWarningItem(BaseModel):
    ingredient: str
    severity: Severity
    diseaseName: str
    description: str


class FoodWarningItem(BaseModel):
    ingredient: str
    severity: Severity
    foodName: str
    description: str
    management: str
    mechanism: str


class DrugWarnings(BaseModel):
    """Lưu ý bệnh lý / thức ăn của một thuốc — chỉ để tham khảo, nội dung tiếng Anh của DDInter."""

    registrationNumber: str
    name: str
    ingredients: list[IngredientInfo]
    isFullyMapped: bool
    diseases: list[DiseaseWarningItem]
    foods: list[FoodWarningItem]


class DrugWarningsResponse(BaseModel):
    drugs: list[DrugWarnings]
    notFound: list[str]
