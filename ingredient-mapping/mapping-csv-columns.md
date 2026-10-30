# Giải thích cột: `data/mapping/national-drug-ddinter-mapping.csv`

File map hoạt chất (cột `Thành phần`) của danh mục thuốc quốc gia `data/national_drug.xlsx` (sheet `DanhSach`)
sang danh sách thuốc DDInter `data/ddinter/ddinter_drug_list.csv`.

- **Sinh bởi:** `python ingredient-mapping/build-national-drug-ddinter-mapping.py`
- **Encoding:** UTF-8 có BOM (`utf-8-sig`) để Excel hiển thị đúng tiếng Việt.
- **Dạng dài:** mỗi dòng = 1 thuốc × 1 hoạt chất. Thuốc có 3 hoạt chất → 3 dòng, các cột thông tin thuốc lặp lại.
  Thuốc không tách được hoạt chất nào → đúng 1 dòng với `match_method = no_ingredient`.
- **Khóa duy nhất:** (`registration_number`, `ingredient_order`).
- **Đọc file:** luôn đọc dạng chuỗi để giữ số 0 đầu của số đăng ký:
  ```python
  pd.read_csv(path, dtype=str, encoding="utf-8-sig")
  ```

## Danh sách cột

### Nhóm thông tin thuốc (lấy từ `national_drug.xlsx`)

| Cột | Nguồn | Ý nghĩa | Ví dụ |
|---|---|---|---|
| `registration_number` | `Số đăng ký lưu hành (*)` | Số đăng ký lưu hành, định danh thuốc. Giữ nguyên dạng chuỗi (có số 0 đầu) | `VD-12777-10`, `893110565724`, `001110009924` |
| `drug_name` | `Tên thuốc (*)` | Tên thương mại của thuốc | `α- Kiisin` |
| `drug_group` | `Nhóm thuốc (*)` | Nhóm thuốc: Hóa dược, Dược liệu, Sinh phẩm, Vắc xin, Nguyên liệu làm thuốc, Thuốc gia công, Thuốc chuyển giao công nghệ | `Hóa dược` |
| `inferred_route` | Suy ra từ `Tên thuốc` + `Quy cách đóng gói` | Đường dùng **đoán** từ từ khóa (cột `Đường dùng` gốc trống 100%). Dùng để chọn biến thể DDInter theo đường dùng. Giá trị: `ophthalmic` (nhỏ/tra mắt), `otic` (nhỏ tai), `nasal` (xịt/nhỏ mũi), `topical` (kem, gel, thuốc mỡ, bôi, dùng ngoài, cồn…), hoặc rỗng = không xác định (thường là đường uống/tiêm) | `topical` |
| `ingredient_text_raw` | `Thành phần` | Nguyên văn ô thành phần, giữ lại để đối chiếu khi rà soát | `Mỗi viên chứa: Losartan kali 50mg; Hydroclorothiazid 12,5mg` |

### Nhóm hoạt chất (kết quả tách từ `ingredient_text_raw`)

| Cột | Ý nghĩa | Ví dụ |
|---|---|---|
| `ingredient_order` | Thứ tự hoạt chất trong thuốc, bắt đầu từ 1. Bằng `0` khi `match_method = no_ingredient` | `1`, `2` |
| `ingredient_name` | Tên hoạt chất đã làm sạch: bỏ liều lượng, đơn vị, câu dẫn ("Mỗi viên chứa:"), phần "(dưới dạng…)/(tương đương…)". Giữ nguyên chính tả gốc (có dấu, có muối) | `Losartan kali`, `Hydroclorothiazid`, `Cam thảo` |
| `ingredient_alternates` | Các tên phụ lấy từ ngoặc "(dưới dạng X)", "(tương đương Y)", nối bằng ` \| `. Chỉ dùng để map khi tên chính không khớp. Rỗng nếu không có | `Ciprofloxacin hydroclorid` |

### Nhóm kết quả map sang DDInter

| Cột | Ý nghĩa | Ví dụ |
|---|---|---|
| `match_method` | Cách khớp (xem bảng dưới) | `salt_stripped` |
| `ddinter_id` | `DDInterID` của thuốc DDInter đã khớp. **Chỉ có giá trị khi khớp chắc chắn**; rỗng với `fuzzy_suggestion`, `no_match`, `no_ingredient` | `DDInter1095` |
| `ddinter_drug` | Tên thuốc trong DDInter tương ứng `ddinter_id` (có thể kèm hậu tố đường dùng) | `Losartan`, `Acyclovir (topical)` |
| `confidence` | Độ tin cậy cố định theo cách khớp: `100` synonym/exact, `95` salt_stripped, `90` spelling_variant, `85` alternate_name. Rỗng nếu không khớp | `95` |
| `needs_review` | `True` nếu dòng cần người kiểm tra lại (xem mục dưới), ngược lại `False` | `False` |
| `suggested_ddinter_id` | `DDInterID` **gợi ý** bằng so khớp gần đúng (rapidfuzz). Chỉ có khi `match_method = fuzzy_suggestion`. **Không** được tự động chấp nhận | `DDInter707` |
| `suggested_ddinter_drug` | Tên DDInter gợi ý tương ứng | `Ezetimibe` (minh họa) |
| `suggested_score` | Điểm giống nhau của gợi ý (thang 0–100, chỉ giữ gợi ý ≥ 88) | `94.1` (minh họa) |

## Giá trị `match_method`

Thứ tự thử từ trên xuống, gặp kết quả đầu tiên thì dừng:

| Giá trị | Ý nghĩa | Ví dụ |
|---|---|---|
| `synonym` | Khớp qua từ điển đồng nghĩa sửa tay `data/mapping/vietnamese-ingredient-ddinter-synonyms.csv` (INN↔USAN, vitamin, dược liệu có trong DDInter) | `Paracetamol` → Acetaminophen, `Vitamin B6` → Pyridoxine, `Cam thảo` → Licorice |
| `exact` | Trùng tên sau khi chuẩn hóa (chữ thường, bỏ dấu, bỏ tiền tố `L-`/`DL-`, bỏ tiền tố cao chiết "Cao khô…") | `Ibuprofen` → Ibuprofen |
| `salt_stripped` | Khớp sau khi bỏ muối, hydrat, ester | `Atorvastatin calci` → Atorvastatin, `Metformin.HCl` → Metformin |
| `spelling_variant` | Khớp sau khi đổi chính tả Việt→Anh (`cilin→cillin`, `clo→chlo`, `-in→-ine`, `acid X→X acid`, `natri→sodium`…) | `Amoxicilin` → Amoxicillin, `Natri clorid` → Sodium chloride |
| `alternate_name` | Tên chính không khớp, nhưng tên trong ngoặc "(dưới dạng/tương đương …)" khớp. Chỉ dùng tên phụ cùng chất (chứa từ đầu của tên chính) hoặc khi ngoặc chỉ có đúng 1 tên | `Calci (dưới dạng Calci carbonat)` → Calcium carbonate |
| `fuzzy_suggestion` | Không khớp chắc chắn; có gợi ý gần đúng ở các cột `suggested_*`. Luôn `needs_review = True`. Tên có dấu tiếng Việt (thường là dược liệu) không được gợi ý | Tên gõ sai chính tả gần giống một tên DDInter |
| `no_match` | Không khớp, không có gợi ý. Phần lớn là chất không có trong DDInter (dược liệu Việt, Piracetam, Candesartan, Tenofovir, Thiamine…) | `Đương quy`, `Piracetam` |
| `no_ingredient` | Ô thành phần trống hoặc không tách được tên hoạt chất nào (chỉ ghi liều, mô tả chung) | `500mg` |

## Khi nào `needs_review = True`

1. `match_method = fuzzy_suggestion`, tức chỉ có gợi ý.
2. DDInter có nhiều biến thể cho chất này mà không có tên gốc không hậu tố, nên phải chọn đại một biến thể.
3. Biến thể được chọn có đường dùng khác với `inferred_route`, hoặc `inferred_route` rỗng mà DDInter chỉ có biến thể theo đường dùng.
   - Ví dụ: thuốc nhỏ mũi khớp `Sulfacetamide (ophthalmic)`.
   - Ví dụ: Rohto (không đoán được đường dùng) khớp `Naphazoline (nasal)`.

## Thống kê lần chạy gần nhất (30/10/2026)

| Chỉ số | Giá trị |
|---|---|
| Số dòng | 86.884 |
| Số thuốc có hoạt chất | 54.086 |
| Thuốc khớp đủ mọi hoạt chất | 67,1% |
| Thuốc khớp ≥1 hoạt chất | 76,3% |
| Dòng `needs_review` | 765 |

Phân bố `match_method`:

| Cách khớp | Số dòng |
|---|---|
| `no_match` | 35.293 |
| `exact` | 20.405 |
| `spelling_variant` | 16.121 |
| `synonym` | 6.979 |
| `salt_stripped` | 6.834 |
| `fuzzy_suggestion` | 471 |
| `no_ingredient` | 454 |
| `alternate_name` | 327 |

## Cách dùng thường gặp

Lấy danh sách hoạt chất DDInter của mỗi thuốc, chỉ tính các dòng khớp chắc chắn:

```python
import pandas as pd

m = pd.read_csv("data/mapping/national-drug-ddinter-mapping.csv", dtype=str, encoding="utf-8-sig")
matched = m[m["ddinter_id"].notna() & (m["ddinter_id"] != "")]
drug_to_ddinter = matched.groupby("registration_number")["ddinter_id"].apply(lambda s: sorted(set(s)))
```

Lọc các dòng cần rà soát tay:

```python
review = m[m["needs_review"] == "True"]
```

## Lưu ý

- Một thuốc có thể có 2 dòng cùng `ddinter_id`, ví dụ `Ampicilin` và `Ampicilin natri` trong cùng ô. Nên dùng `set()` khi gom theo thuốc.
- Cao dược liệu hỗn hợp được tách thành từng vị thuốc trong ngoặc. Ví dụ `Cao đặc hỗn hợp (… Hoàng kỳ, Cam thảo…)` cho ra các dòng `Hoàng kỳ` và `Cam thảo`.
- `inferred_route` chỉ là heuristic từ từ khóa, có thể sai với tên thương mại không chứa từ khóa đường dùng.
- Muốn tăng độ phủ: thêm dòng `source_name,ddinter_drug,note` vào file từ điển đồng nghĩa rồi chạy lại script.
  - `ddinter_drug` phải trùng chính xác tên trong `ddinter_drug_list.csv`, nếu không script sẽ in `WARNING`.
