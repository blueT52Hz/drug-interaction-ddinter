from fastapi import APIRouter, Depends

from app.api.dependencies import get_knowledge_base
from app.knowledge.models import KnowledgeBase
from app.schemas.common import RegistrationNumbersRequest
from app.schemas.interaction import InteractionCheckResponse
from app.services.interaction_service import check_interactions

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("/check", response_model=InteractionCheckResponse)
def check(
    body: RegistrationNumbersRequest,
    knowledge_base: KnowledgeBase = Depends(get_knowledge_base),
) -> InteractionCheckResponse:
    """Kiểm tra tương tác + trùng hoạt chất giữa các thuốc trong giỏ."""
    return check_interactions(knowledge_base, body.registrationNumbers)
