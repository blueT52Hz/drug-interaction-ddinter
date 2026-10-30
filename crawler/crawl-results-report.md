# Báo cáo kết quả crawl tương tác thuốc DDInter 2.0

- Ngày crawl: 30–31/10/2026
- Nguồn: `https://ddinter2.scbdd.com/server/interact/<interaction_id>/`
- Trạng thái: **Hoàn thành**. Đã quét hết dải ID, không còn ID lỗi.

## 1. Mục tiêu

Bổ sung cho mỗi cặp thuốc trong file DDInter đã gộp (`data/ddinter_interactions_merged.csv`) 3 cột lấy từ trang chi tiết tương tác:

- `InteractionID`
- `Interaction`: mô tả cơ chế/hậu quả
- `Management`: khuyến cáo xử trí

File kết quả `data/ddinter_interactions_final.csv` gồm các cột:
`InteractionID,DDInterID_A,Drug_A,DDInterID_B,Drug_B,Level,Interaction,Management`

## 2. Dữ liệu đầu vào

| Thành phần | Giá trị |
|---|---|
| File tải về | 14 nhóm ATC: A,B,C,D,G,H,J,L,M,N,P,R,S,V, tổng 507.655 dòng (`download-ddinter-csv.py`) |
| Nhóm ẩn | C,G,J,M,N,S không hiện trên trang download nhưng tải được theo cùng mẫu URL |
| File merged | 234.981 cặp không trùng, đã bỏ 272.674 dòng trùng (`merge-ddinter-interactions.py`) |
| Level | Moderate 143.748 · Unknown 42.415 · Major 39.082 · Minor 9.736 |
| Thuốc trong file tải về | 1.971 hoạt chất, mã DDInter1–DDInter1972 (thiếu 1 mã) |
| Dải ID crawl | 1–302.665. Mã lớn nhất tìm bằng chia đôi; ID lớn hơn trả HTTP 500 `DoesNotExist` |

## 3. Kiến trúc crawler

| Module | Vai trò |
|---|---|
| `crawl-ddinter-interactions.py` | Điểm chạy chính: nạp config, proxy, bảng final; chia ID cho worker; luồng chính ghi kết quả, lưu định kỳ, in tiến độ |
| `ddinter_crawler_config.py` | Đọc và kiểm tra `config.json` (dải ID, số luồng, delay, retry, đường dẫn) |
| `ddinter_proxy_pool.py` | Nạp toàn bộ proxy; mỗi luồng giữ riêng 1 proxy; proxy bị chặn thì lấy proxy chưa dùng; che thông tin đăng nhập trong log |
| `ddinter_crawl_worker.py` | Worker: lấy ID từ hàng đợi, retry, đổi proxy khi bị chặn, trả ID về hàng đợi nếu hết proxy |
| `ddinter_interaction_fetcher.py` | Gửi HTTP request, phân loại kết quả: ok / missing (500 DoesNotExist) / blocked (403, 407, 429, ProxyError) / error |
| `ddinter_interaction_page_parser.py` | Đọc bảng `td.key`/`td.value`: lấy 2 mã DDInter từ dòng ID, cùng Interaction và Management |
| `ddinter_crawl_output_store.py` | Ghi log thô (từng dòng, flush ngay), ID không tồn tại, ID lỗi |
| `ddinter_final_interactions_table.py` | Khớp kết quả với file final theo cặp không thứ tự; cặp trùng giữ ID nhỏ nhất; ghi file unmatched; ghi file nguyên tử (tmp + replace) |

Cơ chế chính:

- **Chạy tiếp được:** ID đã crawl hoặc đã biết không tồn tại sẽ bị bỏ qua. Khi khởi động, crawler nạp lại log thô vào bảng final.
- **Chặn proxy:**
  - `ProxyError`: chặn vĩnh viễn, ghi vào `blocked_proxies.txt`.
  - 403/429 hoặc 5 lỗi liên tiếp: chỉ bỏ proxy trong lần chạy hiện tại.
- **Mã thoát:** 0 = xong; 1 = lỗi khởi động; 2 = còn ID chưa crawl do hết proxy.
- **Dừng an toàn:** Ctrl+C để worker làm xong ID đang xử lý rồi mới thoát.

## 4. Quá trình chạy

| Lần chạy | Cấu hình | Ghi chú |
|---|---|---|
| 1 | 10 luồng, 6 rồi 20 proxy | ~12 id/s (ước tính); dừng thủ công để thêm file unmatched |
| 2 | 25 luồng, 32 proxy | ~32,7 id/s; 5 proxy bị chặn |
| 3 | 20 luồng, 43 proxy dùng được (7 đã chặn) | ~31 id/s; crawl 21.347 ID cuối |
| 4–5 | Như lần 3 | Thử lại các ID lỗi `ConnectionError`; lần cuối báo `0 to crawl` |

- Tốc độ ổn định 28–32 id/s với 20–25 luồng, delay 0,2 giây.
- Proxy: tổng 50, trong đó 7 bị chặn vĩnh viễn do `ProxyError`.
- 2 ID (181487, 281454) lỗi `ConnectionError` lặp lại qua proxy, dù mở trực tiếp trên trình duyệt vẫn trả HTTP 200. Hai ID này đã lấy được ở lần chạy lại cuối.

## 5. Kết quả

### 5.1. Phủ dải ID

| Hạng mục | Số ID |
|---|---|
| Crawl thành công (`data/crawled/ddinter_interactions_detail.csv`) | 302.515 |
| Không tồn tại (HTTP 500 `DoesNotExist`) | 150 |
| Lỗi còn lại | **0** |
| **Tổng** | **302.665** (phủ kín dải, không trùng ID) |

### 5.2. Phân bổ bản ghi crawl

| Đích | Số bản ghi |
|---|---|
| Điền vào file final | **234.981** (100% cặp của merged) |
| `pair_not_in_merged`: cặp không có trong file tải về | 60.589 |
| `duplicate_pair`: cặp đã có ID nhỏ hơn | 6.945 |
| **Tổng** | 302.515 |

### 5.3. Kiểm định chất lượng (đối chiếu bằng script độc lập)

Merged so với 14 file tải về:
- Không thiếu, không thừa cặp nào.
- Không có cặp trùng; mọi dòng đều có mã A < B.
- Level luôn là mức nặng nhất của cặp.
- Tên thuốc khớp hoàn toàn với danh sách thuốc.

Final so với merged:
- Cùng tập cặp; Drug_A, Drug_B, Level không lệch.
- Không có InteractionID trùng.

Final so với log thô:
- Mọi InteractionID đều có trong log thô.
- Cặp thuốc và nội dung Interaction/Management khớp 100%.
- Mỗi cặp giữ ID nhỏ nhất.

File unmatched:
- Số dòng theo từng lý do khớp với số tính lại từ log thô.
- `KeptInteractionID` trỏ đúng sang ID có trong final.

Placeholder lấy từ trang gốc, không phải lỗi crawl:
- 42.415 dòng có `Interaction = "None"`, đúng bằng số cặp Level Unknown.
- 51.974 dòng có `Management = "-"`.

## 6. Phát hiện: trang web có nhiều tương tác hơn file tải về

60.589 bản ghi không khớp file merged chia làm 2 nhóm:

- **≈48.000 bản ghi chứa thuốc mới.** Có 312 mã DDInter không có trong file tải về, trong khoảng DDInter1433–DDInter2283. Ví dụ DDInter2013 là mirvetuximab soravtansine.
  - Mã xuất hiện nhiều nhất: DDInter2089, 2007, 1981, 2038, 2037.
- **≈12.500 bản ghi (≈12.300 cặp) giữa các thuốc đã có** nhưng file tải về không có cặp đó. Ví dụ: Abametapir (topical) với Avapritinib, Capmatinib, Benzphetamine.

Kết luận: file tải về của DDInter là tập con của dữ liệu trên trang web DDInter 2.0. Các bản ghi ngoài file tải về nằm trong `data/ddinter_interactions_unmatched.csv`.

## 7. File đầu ra

| File | Kích thước | Nội dung |
|---|---|---|
| `data/ddinter_interactions_final.csv` | 179 MB | 234.981 cặp, đủ 8 cột |
| `data/ddinter_interactions_unmatched.csv` | 76 MB | 67.534 bản ghi ngoài final, kèm lý do |
| `data/ddinter_interactions_merged.csv` | 14 MB | 234.981 cặp từ file tải về |
| `data/crawled/ddinter_interactions_detail.csv` | 246 MB | Log thô 302.515 bản ghi |
| `data/crawled/missing_interaction_ids.txt` | | 150 ID không tồn tại |
| `data/crawled/failed_interaction_ids.csv` | | Rỗng |
| `data/crawled/blocked_proxies.txt` | | 7 proxy bị chặn vĩnh viễn (không commit) |

## 8. Hạn chế

- Bản ghi ngoài merged chưa có tên thuốc mới và chưa có `Level`; parser hiện chỉ lấy ID, Interaction, Management.
- Trang còn các trường References và Alternative for … nhưng chưa được lấy.
- Log chỉ ghi tiến độ mỗi 500 ID, không ghi theo từng ID.
- Chưa có unit test tự động. Các kịch bản (chạy tiếp, đổi proxy, hết proxy, lỗi config) mới được kiểm thử thủ công.

## 9. Đề xuất

1. Nếu cần bộ dữ liệu đầy đủ:
   - Crawl `/server/drug-detail/DDInterXXXX/` để lấy tên 312 thuốc mới.
   - Kiểm tra trang tương tác có hiển thị Level không, rồi mở rộng parser.
   - Tạo file final mở rộng gồm cả 60.589 bản ghi ngoài merged.
2. Ghi phiên bản và ngày crawl khi dùng dữ liệu, vì DDInter có thể cập nhật thêm ID.
3. Không commit `proxy.txt` và `data/crawled/blocked_proxies.txt`: các file này chứa thông tin đăng nhập proxy.
