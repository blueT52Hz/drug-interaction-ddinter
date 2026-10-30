# Dữ liệu (tải từ Google Drive)

Các file CSV/XLSX lớn không nằm trong git. Tải từ Google Drive rồi đặt **đúng đường dẫn** bên dưới, tính từ gốc repo.

**Link Drive:** https://drive.google.com/drive/folders/1pXrXzcoGTWpXKMLBSYKHqcZCEJaQpAAk?usp=drive_link

Thư mục trên Drive có cùng cấu trúc với thư mục `data/` này. Có thể tải cả thư mục rồi chép đè vào `data/`.

## File bắt buộc để chạy demo POS

| Đường dẫn | Dung lượng | Nội dung |
|---|---|---|
| `data/national_drug.xlsx` | 6,4 MB | Danh mục thuốc quốc gia (sheet `DanhSach`) |
| `data/mapping/national-drug-ddinter-mapping.csv` | 16 MB | Hoạt chất của từng thuốc đã map sang DDInter. Có thể tự sinh lại, xem [../ingredient-mapping/README.md](../ingredient-mapping/README.md) |
| `data/ddinter/ddinter_interactions_final.csv` | 171 MB | Cặp tương tác thuốc – thuốc, mức độ, cơ chế, xử trí. Đây là kết quả của `crawler/` |
| `data/ddinter/drug_disease_interactions.csv` | 13 MB | Lưu ý thuốc – bệnh lý |
| `data/ddinter/drug_food_interactions.csv` | 1,2 MB | Lưu ý thuốc – thức ăn |

## File đã có sẵn trong git

| Đường dẫn | Nội dung |
|---|---|
| `data/ddinter/ddinter_drug_list.csv` | Danh sách 1.971 hoạt chất DDInter (`DDInterID, Drug`), đầu vào của bước map hoạt chất |
| `data/mapping/vietnamese-ingredient-ddinter-synonyms.csv` | Từ điển tên hoạt chất tiếng Việt → DDInter, soạn tay |

## Dữ liệu của crawler (không bắt buộc)

Chỉ cần khi muốn chạy lại `crawler/`. Crawler dùng thư mục riêng `crawler/data/`, mô tả trong [../crawler/data/README.md](../crawler/data/README.md):

- `crawler/data/downloads/ddinter_downloads_code_*.csv`: 14 file tải từ DDInter.
- `crawler/data/ddinter_interactions_merged.csv`, `ddinter_interactions_final.csv`, `ddinter_interactions_unmatched.csv`.
- `crawler/data/crawled/`: log thô để crawl tiếp. **Không chia sẻ `blocked_proxies.txt`** vì file này chứa tên đăng nhập proxy.

`crawler/data/ddinter_interactions_final.csv` và `data/ddinter/ddinter_interactions_final.csv` là cùng một file.
