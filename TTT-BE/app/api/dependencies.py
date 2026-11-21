from fastapi import Request

from app.knowledge.models import KnowledgeBase


def get_knowledge_base(request: Request) -> KnowledgeBase:
    """Dữ liệu đã nạp lúc khởi động (xem app/main.py)."""
    return request.app.state.knowledge_base
