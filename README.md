# drug-interaction-ddinter

Cảnh báo tương tác thuốc cho nhà thuốc Việt Nam, dựa trên dữ liệu [DDInter 2.0](https://ddinter2.scbdd.com/).

| Thư mục | Nội dung |
|---|---|
| [`crawler/`](crawler/README.md) | (Python) Tải và crawl dữ liệu tương tác thuốc – thuốc của DDInter: mức độ, cơ chế, xử trí |
| [`ingredient-mapping/`](ingredient-mapping/README.md) | (Python) Map hoạt chất trong danh mục thuốc quốc gia sang DDInter |
| `backend/` | (NestJS + SQLite) API tìm thuốc, kiểm tra tương tác, lưu ý bệnh lý / thức ăn |
| `frontend/` | (React + Vite) Trang POS bán hàng demo cho dược sĩ |
| [`data/`](data/README.md) | Dữ liệu đầu vào, **tải từ Google Drive** (file quá lớn để đưa vào git) |

## Demo POS: cảnh báo tương tác khi thêm thuốc vào giỏ

Đây là trang bán hàng một màn hình, giao diện giống KiotViet. Khi dược sĩ thêm thuốc vào hóa đơn, hệ thống hiện ngay cảnh báo về:

- tương tác với các thuốc đã có trong giỏ;
- lưu ý bệnh lý của thuốc;
- lưu ý thức ăn của thuốc.

| Mức độ tương tác | Hiển thị |
|---|---|
| Major / Moderate / Minor | Hộp thoại chặn, phải bấm **"Đã hiểu"** mới đóng được. Nhãn màu: Nghiêm trọng (đỏ), Trung bình (cam), Nhẹ (vàng) |
| Unknown | Không bật hộp thoại, chỉ hiện nhãn xám **"Chưa rõ mức độ"** trong giỏ |
| Thuốc có hoạt chất chưa map được sang DDInter | Nhãn **"Chưa có dữ liệu tương tác"**. Không có cảnh báo **không** có nghĩa là an toàn |

Bấm vào từng cặp tương tác trong hộp thoại để xem **Cơ chế** và **Xử trí** (văn bản gốc tiếng Anh của DDInter). Mỗi dòng trong giỏ có nút "Lưu ý: N bệnh lý · M thức ăn" để mở lại các cảnh báo.

Thanh toán, khách hàng, tồn kho, hóa đơn đều nằm ngoài phạm vi demo.

### Yêu cầu

- **Node.js 24** trở lên. Backend dùng module `node:sqlite` có sẵn trong Node, không cần cài SQLite.
- Python 3.9+ (chỉ cần khi chạy `crawler/` hoặc `ingredient-mapping/`).

### Cài đặt

```bash
git clone https://github.com/blueT52Hz/drug-interaction-ddinter.git
cd drug-interaction-ddinter
```

1. Tải dữ liệu từ Google Drive vào `data/`, theo bảng **"File bắt buộc để chạy demo POS"** trong [data/README.md](data/README.md).
2. Cài backend và tạo DB:

   ```bash
   cd backend
   npm install
   npm run import-data      # tạo backend/data/pos-demo.sqlite (~40 giây)
   ```

   - Lệnh in dòng `ExperimentalWarning: SQLite is an experimental feature`. Đây là cảnh báo của Node, không phải lỗi.
   - Cuối output có số dòng của 5 bảng, kèm danh sách cặp thuốc gợi ý để demo.
   - **Phải tắt backend trước khi import lại.** Backend đang chạy sẽ giữ file DB, nên import báo lỗi `EPERM`.

3. Cài frontend:

   ```bash
   cd ../frontend
   npm install
   ```

### Chạy

Mở 2 terminal:

```bash
# Terminal 1 – backend NestJS, cổng 3001
cd backend
npm run start:dev

# Terminal 2 – frontend React (Vite), proxy /api sang cổng 3001
cd frontend
npm run dev
```

Mở địa chỉ Vite in ra (mặc định http://localhost:5173).

### Kịch bản demo

**Trước mỗi kịch bản, xóa hết thuốc trong giỏ**, vì thuốc của các kịch bản khác có thể tương tác thêm với nhau.

Các thuốc dưới đây được xếp ở đầu trang 1 của "Danh mục thuốc" (danh sách trong `backend/src/drugs/featured-demo-drugs.ts`). Bấm vào thẻ thuốc là thêm vào hóa đơn. Muốn tìm thuốc khác thì gõ tên hoặc số đăng ký vào ô tìm kiếm (F3).

| # | Thêm lần lượt | Kết quả mong đợi |
|---|---|---|
| 1 | `Verzenio` (001110334425, Abemaciclib) rồi `Humira` (400410038523, Adalimumab) | Hộp thoại chặn, nhãn **đỏ "Nghiêm trọng"**, có sẵn đoạn cơ chế và xử trí |
| 2 | `Abacavir Tablets USP 300mg` (890110007300) rồi `Methotrexate-Belmed` (481114088523) | Hộp thoại chặn, nhãn **cam "Trung bình"** |
| 3 | `Abacavir Tablets USP 300mg` (890110007300) rồi `Acyclovir STADA` (400100354725) | **Không** có hộp thoại. Hai dòng trong giỏ có nhãn **xám "Chưa rõ mức độ"** |

Mẹo khi demo:

- Thêm lại một thuốc đã có trong giỏ chỉ tăng số lượng, không cảnh báo lại.
- Tắt backend rồi thêm thuốc: giỏ hiện **"Chưa kiểm tra được tương tác"** và nút **"Thử lại"**. Hệ thống không bao giờ coi trường hợp này là "không có tương tác".

## Luồng dữ liệu

```
crawler/            -> data/ddinter/ddinter_interactions_final.csv
ingredient-mapping/ -> data/mapping/national-drug-ddinter-mapping.csv
backend: npm run import-data
    đọc data/national_drug.xlsx + 2 file trên + drug_disease / drug_food
    -> backend/data/pos-demo.sqlite
```

Không cần chạy lại crawler hay ingredient-mapping nếu đã tải đủ file từ Drive.
