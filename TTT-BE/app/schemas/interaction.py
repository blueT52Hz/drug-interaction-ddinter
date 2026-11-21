from datetime import datetime

from pydantic import BaseModel, Field

from app.knowledge.models import Severity
from app.schemas.common import DrugRef


class InteractionPair(BaseModel):
    """Một cặp hoạt chất tương tác giữa hai thuốc khác nhau trong giỏ."""

    id: str = Field(description="Mã cố định của cặp hoạt chất, vd 'ddi:DDInter1:DDInter14' — dùng để đối chiếu khi duyệt")
    severity: Severity
    drug1: DrugRef = Field(description="Thuốc đứng trước trong danh sách gửi lên")
    drug2: DrugRef
    ingredient1: str = Field(description="Tên hoạt chất (DDInter) của drug1")
    ingredient2: str
    description: str = Field(description="Cơ chế (tiếng Anh), rỗng nếu DDInter không có")
    management: str = Field(description="Cách xử trí (tiếng Anh), rỗng nếu DDInter không có")


class DuplicateIngredient(BaseModel):
    """Nhiều thuốc trong giỏ có cùng một hoạt chất (nguy cơ quá liều)."""

    id: str = Field(description="vd 'dup:DDInter14'")
    ingredient: str
    drugs: list[DrugRef]


class InteractionCheckResponse(BaseModel):
    interactions: list[InteractionPair] = Field(description="Sắp xếp từ nặng tới nhẹ")
    duplicates: list[DuplicateIngredient]
    hasMajor: bool = Field(description="Có ít nhất một cặp mức nghiêm trọng")
    notFound: list[str] = Field(description="Số đăng ký không có trong dữ liệu — KHÔNG kiểm tra được")
    incomplete: list[str] = Field(
        description="Thuốc còn hoạt chất chưa map sang DDInter — kết quả có thể thiếu, không có cảnh báo ≠ an toàn"
    )
    checkedAt: datetime
