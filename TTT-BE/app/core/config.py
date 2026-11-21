"""Cấu hình đọc từ biến môi trường (file .env)."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    # Thư mục chứa các file CSV dữ liệu (xem data/README.md)
    data_dir: Path
    # Khoá BE gửi qua header X-Internal-Key. Để trống = không kiểm khoá (chỉ dùng khi dev).
    internal_key: str
    # Số thuốc tối đa trong một lần kiểm tra
    max_drugs_per_request: int


def _resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


settings = Settings(
    data_dir=_resolve_path(os.getenv("DATA_DIR", "data")),
    internal_key=os.getenv("INTERACTION_INTERNAL_KEY", ""),
    max_drugs_per_request=int(os.getenv("MAX_DRUGS_PER_REQUEST", "100")),
)
