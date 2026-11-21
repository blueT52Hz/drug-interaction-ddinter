from fastapi import APIRouter, Depends

from app.api.dependencies import get_knowledge_base
from app.knowledge.models import KnowledgeBase
from app.schemas.common import RegistrationNumbersRequest
from app.schemas.drug_warning import DrugWarningsResponse
from app.services.drug_warning_service import get_drug_warnings

router = APIRouter(prefix="/drug-warnings", tags=["drug-warnings"])


@router.post("", response_model=DrugWarningsResponse)
def drug_warnings(
    body: RegistrationNumbersRequest,
    knowledge_base: KnowledgeBase = Depends(get_knowledge_base),
) -> DrugWarningsResponse:
    """Lưu ý bệnh lý / thức ăn của từng thuốc (gửi nhiều số đăng ký một lần)."""
    return get_drug_warnings(knowledge_base, body.registrationNumbers)
