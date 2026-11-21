from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.core.config import settings

RegistrationNumber = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class RegistrationNumbersRequest(BaseModel):
    """Danh sách số đăng ký lưu hành của các thuốc (BE lấy từ hàng hoá → thuốc trong danh mục)."""

    registrationNumbers: list[RegistrationNumber] = Field(
        min_length=1,
        max_length=settings.max_drugs_per_request,
        examples=[["400410038523", "001110334425"]],
    )


class DrugRef(BaseModel):
    registrationNumber: str
    name: str
