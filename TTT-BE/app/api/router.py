"""Gom các route. Thêm tính năng mới: tạo file trong routes/ rồi include ở đây."""
from fastapi import APIRouter, Depends

from app.api.routes import drug_warnings, health, interactions
from app.core.security import require_internal_key

api_router = APIRouter(dependencies=[Depends(require_internal_key)])
api_router.include_router(health.router)
api_router.include_router(interactions.router)
api_router.include_router(drug_warnings.router)
