# DDInter 2.0 interaction crawler

Tạo bảng tương tác thuốc–thuốc từ [DDInter 2.0](https://ddinter2.scbdd.com/). Mỗi cặp thuốc gồm mức độ (Level), cơ chế (Interaction) và khuyến cáo xử trí (Management).

Kết quả: `data/ddinter_interactions_final.csv` (170 MB, không có trong git, tải từ Google Drive theo [../data/README.md](../data/README.md)), gồm 234.981 cặp, crawl ngày 31/10/2026. Chi tiết quá trình và kiểm định dữ liệu xem trong [crawl-results-report.md](crawl-results-report.md).

| Cột | Ý nghĩa |
|---|---|
| `InteractionID` | ID trang `https://ddinter2.scbdd.com/server/interact/<id>/` |
| `DDInterID_A`, `Drug_A`, `DDInterID_B`, `Drug_B` | Cặp thuốc, chuẩn hoá A < B |
| `Level` | Major / Moderate / Minor / Unknown |
| `Interaction`, `Management` | Nội dung từ trang chi tiết. Trang gốc ghi `None` / `-` khi không có dữ liệu |

## Cài đặt

Cần Python 3.9 trở lên.

```bash
pip install -r requirements.txt
```

## Chạy

Mọi lệnh chạy được từ bất kỳ thư mục nào. Đường dẫn trong `config.json` tính tương đối từ thư mục repo này.

```bash
python download-ddinter-csv.py          # 1. Tải 14 file CSV theo nhóm ATC -> data/downloads/
python merge-ddinter-interactions.py    # 2. Gộp và lọc trùng -> data/ddinter_interactions_merged.csv
python crawl-ddinter-interactions.py    # 3. Crawl Interaction/Management -> data/ddinter_interactions_final.csv
```

- Bước 1 và 2 chỉ cần chạy một lần.
- Bước 3 chạy tiếp được: ID đã crawl sẽ được bỏ qua. Dừng bằng `Ctrl+C`, chạy lại sẽ làm tiếp từ chỗ dừng.
- File final tải từ Drive đã điền đầy đủ. Nếu chạy lại bước 3 mà không có `data/crawled/`, crawler sẽ crawl lại toàn bộ dải ID và ghi đè nội dung bằng dữ liệu mới.
- Muốn crawl lại từ đầu: xoá `data/ddinter_interactions_final.csv` và thư mục `data/crawled/`.

Lưu log ra file:

```bash
# bash
python -u crawl-ddinter-interactions.py | tee data/crawled/crawl.log
# PowerShell
python -u crawl-ddinter-interactions.py | Tee-Object -FilePath data\crawled\crawl.log
```

Mã thoát:

| Mã | Ý nghĩa |
|---|---|
| `0` | Xong |
| `1` | Lỗi khởi động (config, proxy, thiếu file) |
| `2` | Còn ID chưa crawl vì mọi proxy đều bị chặn |

## Proxy

Không có proxy thì đặt `"use_proxy": false` và giảm `workers` (ví dụ 2–4) để tránh bị chặn IP.

Có proxy:

```bash
cp proxy.example.txt proxy.txt   # rồi điền proxy, mỗi dòng một proxy
```

- Mỗi luồng giữ riêng một proxy. Proxy bị chặn thì luồng lấy một proxy chưa dùng. Hết proxy thì luồng đó dừng.
- `ProxyError` (proxy chết): ghi vào `data/crawled/blocked_proxies.txt` và bị bỏ qua ở các lần chạy sau. Xoá dòng tương ứng để dùng lại.
- HTTP 403/429, hoặc `max_consecutive_errors` lỗi liên tiếp: chỉ bỏ proxy trong lần chạy hiện tại.
- Số luồng thực tế = min(`workers`, số proxy dùng được).

`proxy.txt` chứa thông tin đăng nhập nên đã nằm trong `.gitignore`. **Không commit file này.**

## Cấu hình `config.json`

| Khoá | Mặc định | Ý nghĩa |
|---|---|---|
| `start_id`, `end_id` | 1, 302665 | Dải InteractionID cần crawl (gồm cả 2 đầu) |
| `workers` | 20 | Số luồng song song |
| `delay_seconds` | 0.2 | Thời gian nghỉ của mỗi luồng sau mỗi ID |
| `timeout_seconds`, `retries`, `backoff_seconds` | 30, 3, 2.0 | Timeout và chính sách retry của mỗi request |
| `max_consecutive_errors` | 5 | Số lỗi liên tiếp thì coi proxy bị chặn |
| `progress_every`, `save_every` | 500, 2000 | In tiến độ / ghi file final sau mỗi N ID |
| `use_proxy`, `proxy_file` | true, `proxy.txt` | Bật/tắt proxy |
| `downloads_dir` | `data/downloads` | Thư mục chứa CSV tải về |
| `merged_file`, `final_file`, `unmatched_file` | `data/...csv` | File gộp / file kết quả / bản ghi không vào được final |
| `crawl_output_dir` | `data/crawled` | Log thô, ID không tồn tại, ID lỗi, proxy bị chặn |

## Dữ liệu đầu ra

| File | Nội dung |
|---|---|
| `data/ddinter_interactions_final.csv` | Bảng kết quả, một dòng cho mỗi cặp trong file merged (tải từ Drive) |
| `data/ddinter_interactions_unmatched.csv` | Bản ghi crawl được nhưng không vào final: `pair_not_in_merged` (cặp không có trong file tải về) hoặc `duplicate_pair` (cặp đã có ID nhỏ hơn) |
| `data/crawled/ddinter_interactions_detail.csv` | Log thô, mỗi ID một dòng, ghi ngay khi crawl. Dùng để chạy tiếp |
| `data/crawled/missing_interaction_ids.txt` | ID không tồn tại (HTTP 500 `DoesNotExist`) |
| `data/crawled/failed_interaction_ids.csv` | ID lỗi; chạy lại để thử lại |

## Lưu ý về dữ liệu

- Trang download DDInter chỉ hiện 8 nhóm ATC. Nhóm C, G, J, M, N, S vẫn tải được theo cùng mẫu URL; `download-ddinter-csv.py` tải đủ 14 nhóm.
- Trang web có nhiều tương tác hơn file tải về. Khoảng 60 nghìn bản ghi `pair_not_in_merged` thuộc về 312 thuốc mới (mã DDInter cao hơn danh sách tải về) hoặc là cặp không có trong file tải về. Các bản ghi này nằm trong file unmatched, chưa có tên thuốc và Level.
