"""Service kiểm tra tương tác thuốc (dữ liệu DDInter 2.0) cho BE NestJS gọi.

Chạy: uvicorn app.main:app --host 127.0.0.1 --port 8791
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.knowledge.loader import load_knowledge_base
from app.knowledge.models import KnowledgeBase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app(knowledge_base: KnowledgeBase | None = None) -> FastAPI:
    """`knowledge_base` truyền sẵn khi test; để trống thì nạp từ thư mục data lúc khởi động."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.knowledge_base = knowledge_base or load_knowledge_base(settings.data_dir)
        yield

    app = FastAPI(title="Drug interaction service (DDInter)", version="1.0.0", lifespan=lifespan)
    app.include_router(api_router)
    return app


app = create_app()
