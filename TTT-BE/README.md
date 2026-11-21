# TTT-BE – Service kiểm tra tương tác thuốc

API FastAPI cho BE NestJS gọi khi bán hàng: kiểm tra tương tác giữa các thuốc trong giỏ, trùng hoạt chất, và lưu ý bệnh lý / thức ăn. Dữ liệu từ [DDInter 2.0](https://ddinter2.scbdd.com/), thuốc tra theo **số đăng ký lưu hành** của danh mục thuốc Việt Nam.

Không dùng cơ sở dữ liệu: lúc khởi động service đọc 4 file CSV vào bộ nhớ (~3 giây, ~170 MB RAM).

## Cấu trúc

```
app/
  main.py                  tạo app FastAPI, nạp dữ liệu lúc khởi động
  core/
    config.py              đọc biến môi trường (.env)
    security.py            kiểm header X-Internal-Key
  knowledge/
    models.py              kiểu dữ liệu: Drug, Ingredient, InteractionDetail, KnowledgeBase...
    loader.py              đọc CSV → KnowledgeBase
  schemas/                 kiểu request / response của API (Pydantic)
  services/
    interaction_service.py kiểm tra tương tác + trùng hoạt chất
    drug_warning_service.py lưu ý bệnh lý / thức ăn
  api/
    router.py              gom các route, gắn kiểm khoá
    dependencies.py        lấy KnowledgeBase cho route
    routes/                mỗi nhóm API một file
tests/                     pytest, dùng dữ liệu nhỏ dựng tay
data/                      4 file CSV (không đưa vào git, xem data/README.md)
```

Thêm tính năng mới: kiểu dữ liệu ở `schemas/`, xử lý ở `services/`, route ở `api/routes/` rồi include trong `api/router.py`.

## Cài đặt và chạy

Cần Python 3.10+.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# chép 4 file CSV vào data/ (xem data/README.md)

.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8791 --reload
```

Tài liệu API tự sinh: http://127.0.0.1:8791/docs

Chạy test: `.venv/bin/python -m pytest -q`

## API

Mọi API cần header `X-Internal-Key` khi `.env` có `INTERACTION_INTERNAL_KEY` (để trống = không kiểm, chỉ dùng khi dev).

| API | Dùng để |
|---|---|
| `GET /health` | Service còn chạy không, đã nạp bao nhiêu dữ liệu |
| `POST /interactions/check` | Kiểm tra giỏ hàng |
| `POST /drug-warnings` | Lưu ý bệnh lý / thức ăn của từng thuốc |

### POST /interactions/check

```json
{ "registrationNumbers": ["001110334425", "400410038523"] }
```

Trả về:

```json
{
  "interactions": [
    {
      "id": "ddi:DDInter27:DDInter7",
      "severity": "major",
      "drug1": { "registrationNumber": "001110334425", "name": "Verzenio" },
      "drug2": { "registrationNumber": "400410038523", "name": "Humira" },
      "ingredient1": "Abemaciclib",
      "ingredient2": "Adalimumab",
      "description": "...",
      "management": "..."
    }
  ],
  "duplicates": [],
  "hasMajor": true,
  "notFound": [],
  "incomplete": [],
  "checkedAt": "2026-11-21T01:32:24.492873Z"
}
```

| Trường | Ý nghĩa |
|---|---|
| `interactions` | Cặp hoạt chất tương tác, nặng trước. `severity`: `major` / `moderate` / `minor` / `unknown` |
| `id` | Mã cố định của cặp (không phụ thuộc thứ tự thuốc). BE dùng để đối chiếu cảnh báo nào đã được dược sĩ duyệt |
| `duplicates` | Hoạt chất có ở từ 2 thuốc trở lên (vd Panadol + Panadol Extra cùng Paracetamol), `id` dạng `dup:DDInter14` |
| `hasMajor` | Có cặp mức nghiêm trọng → BE chặn thanh toán tới khi dược sĩ duyệt |
| `notFound` | Số đăng ký không có trong dữ liệu → **không kiểm tra được** |
| `incomplete` | Thuốc còn hoạt chất chưa map sang DDInter → kết quả có thể thiếu |

**Không có cảnh báo không có nghĩa là an toàn** khi thuốc nằm trong `notFound` hoặc `incomplete`.

### POST /drug-warnings

Body giống trên. Trả về `drugs[]` (mỗi thuốc: hoạt chất, `diseases[]`, `foods[]`) và `notFound[]`. Nội dung tiếng Anh của DDInter, chỉ để tham khảo.

## Thử nhanh

| Gửi | Kết quả |
|---|---|
| `001110334425` (Verzenio) + `400410038523` (Humira) | 1 cặp `major` |
| `890110007300` (Abacavir) + `481114088523` (Methotrexate) | 1 cặp `moderate` |
| `890110007300` (Abacavir) + `400100354725` (Acyclovir) | 1 cặp `unknown` |
