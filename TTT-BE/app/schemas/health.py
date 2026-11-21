from pydantic import BaseModel


class KnowledgeStats(BaseModel):
    drugs: int
    interactionPairs: int
    ingredientsWithDiseaseWarnings: int
    ingredientsWithFoodWarnings: int


class HealthResponse(BaseModel):
    status: str
    stats: KnowledgeStats
