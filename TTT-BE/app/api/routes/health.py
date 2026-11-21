from fastapi import APIRouter, Depends

from app.api.dependencies import get_knowledge_base
from app.knowledge.models import KnowledgeBase
from app.schemas.health import HealthResponse, KnowledgeStats

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(knowledge_base: KnowledgeBase = Depends(get_knowledge_base)) -> HealthResponse:
    """BE gọi để biết service còn chạy và dữ liệu đã nạp."""
    return HealthResponse(
        status="ok",
        stats=KnowledgeStats(
            drugs=len(knowledge_base.drugs),
            interactionPairs=len(knowledge_base.interactions),
            ingredientsWithDiseaseWarnings=len(knowledge_base.disease_warnings),
            ingredientsWithFoodWarnings=len(knowledge_base.food_warnings),
        ),
    )
