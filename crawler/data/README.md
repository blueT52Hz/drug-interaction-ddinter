# Dữ liệu DDInter 2.0

Dữ liệu tương tác thuốc–thuốc lấy từ [DDInter 2.0](https://ddinter2.scbdd.com/), crawl ngày 30–31/10/2026. Cách tạo và kiểm định dữ liệu xem [../crawl-results-report.md](../crawl-results-report.md).

Định dạng chung của mọi file CSV:
- UTF-8, có dòng tiêu đề, ngăn cách bằng dấu phẩy.
- Ô có dấu phẩy hoặc xuống dòng được bao bằng `"`.
- Mã thuốc có dạng `DDInter<số>`, ví dụ `DDInter90`.
- Trang chi tiết tương tác: `https://ddinter2.scbdd.com/server/interact/<InteractionID>/`.

## Luồng tạo dữ liệu

```
downloads/*.csv ──merge──> ddinter_interactions_merged.csv ──crawl──> ddinter_interactions_final.csv
                                                               ├────> ddinter_interactions_unmatched.csv
                                                               └────> crawled/ddinter_interactions_detail.csv
```

## Nên dùng file nào?

| Nhu cầu | File |
|---|---|
| Bảng sạch, mỗi cặp một dòng, đủ tên thuốc, Level, nội dung | `ddinter_interactions_final.csv` |
| Chỉ cần cặp thuốc và Level | `ddinter_interactions_merged.csv` |
| Mọi tương tác có trên web, kể cả thuốc mới không có trong file tải về | `crawled/ddinter_interactions_detail.csv`. Thiếu tên thuốc và Level, một cặp có thể lặp ở nhiều dòng |

## `ddinter_interactions_final.csv`: kết quả chính

234.981 dòng, mỗi dòng là một cặp thuốc. Không có trong git (170 MB), tải từ Google Drive theo [../../data/README.md](../../data/README.md).

| Cột | Ý nghĩa |
|---|---|
| `InteractionID` | ID trang chi tiết. Cặp nào có nhiều ID thì giữ ID nhỏ nhất |
| `DDInterID_A`, `Drug_A` | Thuốc A, luôn có mã số nhỏ hơn B |
| `DDInterID_B`, `Drug_B` | Thuốc B |
| `Level` | Mức độ: `Major` 39.082 · `Moderate` 143.748 · `Minor` 9.736 · `Unknown` 42.415 |
| `Interaction` | Mô tả cơ chế/hậu quả. Trang gốc ghi `None` khi không có (42.415 dòng, đúng bằng số cặp `Unknown`) |
| `Management` | Khuyến cáo xử trí. Trang gốc ghi `-` khi không có (51.974 dòng) |

## `ddinter_interactions_merged.csv`: cặp thuốc từ file tải về

234.981 dòng, gồm các cột `DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level`.

Đây là file gộp 14 file trong `downloads/`:
- Bỏ dòng trùng; cặp A/B và B/A tính là một cặp.
- Chuẩn hoá để A < B.
- Cặp có Level khác nhau giữa các file thì giữ mức nặng nhất.

File final được tạo từ file này, sau đó điền thêm 3 cột crawl được.

## `downloads/ddinter_downloads_code_<X>.csv`: file gốc từ DDInter

- 14 file, mỗi file là một nhóm ATC `<X>`: A, B, C, D, G, H, J, L, M, N, P, R, S, V. Tổng 507.655 dòng.
- Cột: `DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level`.
- Một cặp có thể xuất hiện ở nhiều nhóm, đôi khi đảo A/B.
- Tải bằng `download-ddinter-csv.py`. Trang download của DDInter chỉ hiện 8 nhóm, nhưng 6 nhóm C, G, J, M, N, S vẫn tải được.

| Mã | Nhóm ATC |
|---|---|
| A | Đường tiêu hoá và chuyển hoá |
| B | Máu và cơ quan tạo máu |
| C | Tim mạch |
| D | Da liễu |
| G | Hệ sinh dục–tiết niệu và hormone sinh dục |
| H | Hormone toàn thân (trừ hormone sinh dục và insulin) |
| J | Kháng khuẩn toàn thân |
| L | Chống ung thư và điều hoà miễn dịch |
| M | Cơ–xương–khớp |
| N | Thần kinh |
| P | Kháng ký sinh trùng |
| R | Hô hấp |
| S | Giác quan |
| V | Khác |

## `ddinter_interactions_unmatched.csv`: bản ghi crawl được nhưng không vào final

67.534 dòng.

| Cột | Ý nghĩa |
|---|---|
| `InteractionID`, `DDInterID_A`, `DDInterID_B` | ID trang và cặp thuốc, thứ tự A/B giữ như trên trang |
| `Reason` | `pair_not_in_merged`: cặp không có trong file tải về (60.589 dòng). `duplicate_pair`: cặp đã có trong final với ID nhỏ hơn (6.945 dòng) |
| `KeptInteractionID` | Chỉ có với `duplicate_pair`: ID đang dùng trong final |
| `Interaction`, `Management` | Nội dung trang |

Nhóm `pair_not_in_merged` gồm 2 loại:
- **≈48.000 dòng chứa thuốc mới.** Có 312 mã thuốc không có trong file tải về, nằm trong khoảng DDInter1433–DDInter2283.
- **≈12.500 dòng giữa các thuốc đã có** nhưng file tải về thiếu cặp đó.

Các dòng này chưa có tên thuốc và Level.

## `crawled/`: dữ liệu thô của crawler

Crawler dùng thư mục này để chạy tiếp từ chỗ dừng. Không commit thư mục này.

| File | Nội dung |
|---|---|
| `ddinter_interactions_detail.csv` | Log thô, 302.515 dòng, mỗi InteractionID crawl được là một dòng. Cột: `InteractionID, DDInterID_A, DDInterID_B, Interaction, Management`. Bao trọn final, unmatched và duplicate. Không có tên thuốc và Level; A/B giữ như trên trang; một cặp có thể lặp ở nhiều dòng |
| `missing_interaction_ids.txt` | 150 ID không tồn tại trên trang (HTTP 500 `DoesNotExist`), mỗi dòng một ID |
| `failed_interaction_ids.csv` | ID crawl lỗi (`InteractionID, Error`). Hiện rỗng; chạy lại crawler để thử lại nếu có |
| `blocked_proxies.txt` | Proxy bị chặn vĩnh viễn (`user@host:port`, thời điểm, lý do). **Chứa tên đăng nhập proxy, không chia sẻ** |
| `*.log` | Log tiến độ các lần chạy |

Đối chiếu số lượng: dải ID 1–302.665 = 302.515 crawl được + 150 không tồn tại. 302.515 = 234.981 (final) + 60.589 (`pair_not_in_merged`) + 6.945 (`duplicate_pair`).
