# Map hoạt chất thuốc Việt Nam sang DDInter

Đọc cột `Thành phần` của `data/national_drug.xlsx` rồi tách thành từng hoạt chất. Sau đó map mỗi hoạt chất sang một thuốc trong DDInter (`data/ddinter/ddinter_drug_list.csv`).

Kết quả là `data/mapping/national-drug-ddinter-mapping.csv`, mỗi dòng ứng với một cặp (thuốc, hoạt chất). Giải thích từng cột: [mapping-csv-columns.md](mapping-csv-columns.md).

## Cài đặt

Cần Python 3.9 trở lên.

```bash
pip install -r ingredient-mapping/requirements.txt
```

## Chạy

Chạy từ gốc repo. Trước đó cần có `data/national_drug.xlsx` (tải từ Drive, xem [../data/README.md](../data/README.md)).

```bash
python ingredient-mapping/build-national-drug-ddinter-mapping.py
```

Cách map, theo thứ tự ưu tiên:
1. Từ điển `data/mapping/vietnamese-ingredient-ddinter-synonyms.csv`.
2. Trùng khớp chính xác.
3. Trùng khớp sau khi bỏ gốc muối.
4. Biến thể chính tả.
5. Tên thay thế.

Fuzzy match **không** tự gán. Kết quả fuzzy chỉ ghi vào cột gợi ý (`suggested_*`) và gắn cờ `needs_review`.

Muốn sinh lại `data/ddinter/ddinter_drug_list.csv` (file này đã có sẵn trong git):

```bash
python crawler/download-ddinter-csv.py
python ingredient-mapping/build-ddinter-drug-list.py --input-dir crawler/data/downloads
```

## Các module

| File | Vai trò |
|---|---|
| `build-national-drug-ddinter-mapping.py` | Điểm chạy chính: đọc xlsx, ghi CSV, in thống kê |
| `ingredient_text_parser.py` | Tách ô `Thành phần` thành danh sách hoạt chất |
| `drug_name_normalizer.py` | Chuẩn hoá tên hoạt chất trước khi so khớp |
| `ddinter_name_matcher.py` | Map tên hoạt chất sang DDInter theo các tầng ở trên |
| `administration_route_inference.py` | Suy ra đường dùng từ tên và quy cách thuốc |
| `build-ddinter-drug-list.py`, `ddinter_csv_utils.py` | Tạo danh sách hoạt chất DDInter từ các file tải về |
