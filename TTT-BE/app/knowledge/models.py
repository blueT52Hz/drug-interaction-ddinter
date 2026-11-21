"""Dữ liệu tri thức nạp sẵn trong bộ nhớ: thuốc → hoạt chất, cặp tương tác, lưu ý bệnh lý / thức ăn."""
from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"
    UNKNOWN = "unknown"

    @property
    def rank(self) -> int:
        """Dùng để sắp xếp: số lớn hơn = nặng hơn."""
        return {"major": 3, "moderate": 2, "minor": 1, "unknown": 0}[self.value]

    @classmethod
    def from_ddinter(cls, value: str) -> "Severity":
        """DDInter ghi 'Major' / 'Moderate' / 'Minor' / 'Unknown'. Giá trị lạ coi là chưa rõ."""
        try:
            return cls(value.strip().lower())
        except ValueError:
            return cls.UNKNOWN


@dataclass(frozen=True)
class Ingredient:
    order: int
    name: str  # tên hoạt chất trong danh mục thuốc Việt Nam
    ddinter_id: str | None  # None = chưa map được sang DDInter
    ddinter_name: str | None


@dataclass
class Drug:
    registration_number: str
    name: str
    ingredients: list[Ingredient] = field(default_factory=list)

    @property
    def mapped_ingredients(self) -> list[Ingredient]:
        return [i for i in self.ingredients if i.ddinter_id]

    @property
    def is_fully_mapped(self) -> bool:
        """False khi thuốc không có hoạt chất nào hoặc còn hoạt chất chưa map → kết quả kiểm tra có thể thiếu."""
        return bool(self.ingredients) and all(i.ddinter_id for i in self.ingredients)


@dataclass(frozen=True)
class InteractionDetail:
    severity: Severity
    description: str  # cơ chế (tiếng Anh), "" nếu DDInter không có
    management: str  # cách xử trí (tiếng Anh), "" nếu DDInter không có


@dataclass(frozen=True)
class DiseaseWarning:
    severity: Severity
    disease_name: str
    description: str


@dataclass(frozen=True)
class FoodWarning:
    severity: Severity
    food_name: str
    description: str
    management: str
    mechanism: str


def pair_key(ddinter_id_a: str, ddinter_id_b: str) -> tuple[str, str]:
    """Khoá không phụ thuộc thứ tự: (A, B) và (B, A) là cùng một cặp."""
    return (ddinter_id_a, ddinter_id_b) if ddinter_id_a <= ddinter_id_b else (ddinter_id_b, ddinter_id_a)


@dataclass
class KnowledgeBase:
    drugs: dict[str, Drug]  # khoá: số đăng ký
    interactions: dict[tuple[str, str], InteractionDetail]  # khoá: pair_key
    disease_warnings: dict[str, list[DiseaseWarning]]  # khoá: DDInter id
    food_warnings: dict[str, list[FoodWarning]]  # khoá: DDInter id

    def find_drug(self, registration_number: str) -> Drug | None:
        return self.drugs.get(registration_number.strip())

    def find_interaction(self, ddinter_id_a: str, ddinter_id_b: str) -> InteractionDetail | None:
        return self.interactions.get(pair_key(ddinter_id_a, ddinter_id_b))
