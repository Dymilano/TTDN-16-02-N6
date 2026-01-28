---
![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)
![GitLab](https://img.shields.io/badge/gitlab-%23181717.svg?style=for-the-badge&logo=gitlab&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)


# 1. Tổng quan hệ thống (System Overview)

Hệ thống ERP quản lý doanh nghiệp (Enterprise Resource Planning) được xây dựng nhằm mục đích tối ưu hóa quy trình quản lý nội bộ, tập trung vào ba mảng cốt lõi: **Quản lý Nhân sự**, **Quản lý Tài sản** và **Quản lý Phòng họp**.

Dự án cung cấp giải pháp toàn diện giúp doanh nghiệp theo dõi tài sản, điều phối nhân sự và quản lý cơ sở vật chất một cách khoa học, hiệu quả và minh bạch.

---

# 2. Các phân hệ chính (Core Modules)

## 2.1. Module Quản lý Nhân sự (`nhansu`)
Module cung cấp công cụ quản lý toàn diện vòng đời của nhân viên trong doanh nghiệp, từ thông tin cơ bản đến chi tiết công/lương.

**Các tính năng chính:**

### Quản lý cơ cấu tổ chức
*   **Quản lý Phòng ban (`phong_ban`):** Cấu trúc phòng ban phân cấp, định biên nhân sự, quản lý cây tổ chức.
*   **Quản lý Chức vụ (`chuc_vu`):** Định nghĩa chức danh, cấp bậc và mô tả công việc.

### Hồ sơ nhân viên
*   **Quản lý Nhân viên (`nhan_vien`):** Lưu trữ thông tin cá nhân, liên hệ, tài khoản ngân hàng, phòng ban, chức vụ.

### Quản lý hồ sơ năng lực
*   **Chứng chỉ & Bằng cấp (`chung_chi_bang_cap`):** Danh mục các loại chứng chỉ, bằng cấp.
*   **Danh sách chứng chỉ, bằng cấp:** Gán chứng chỉ cho nhân viên, theo dõi thời hạn hiệu lực.
*   **Lịch sử công tác (`lich_su_cong_tac`):** Ghi nhận quá trình thăng tiến, thuyên chuyển công tác, thay đổi chức vụ/phòng ban.

### Quản lý chấm công & tiền lương
*   **Chấm công (`cham_cong`):** Ghi nhận giờ vào/ra, tự động tính giờ làm việc, trạng thái (đúng giờ, muộn, về sớm).
*   **Vi phạm chấm công (`vi_pham_cham_cong`):** Tự động phát hiện và ghi nhận:
    *   Đi muộn
    *   Về sớm
    *   Thiếu giờ làm
    *   Quên checkout
*   **Tăng ca (`tang_ca`):** Quản lý đăng ký và phê duyệt làm thêm giờ, phân loại ngày làm việc.
*   **Kỳ lương (`ky_luong`):** Quản lý các kỳ lương theo tháng.
*   **Bảng lương tháng (`bang_luong_thang`):** Tính lương tự động theo ngày công hoặc giờ làm việc, tích hợp các khoản khấu trừ và phụ cấp.

### Tính năng khác
*   **Tracking:** Theo dõi lịch sử tạo và chỉnh sửa bản ghi hệ thống.
*   **Tích hợp:** Module được sử dụng làm nền tảng cho các module khác (`quan_ly_tai_san`, `quan_ly_phong_hop`).

## 2.2. Module Quản lý Tài sản (`quan_ly_tai_san`)
Module tập trung vào việc giám sát, định giá và tối ưu hóa hiệu suất sử dụng tài sản của doanh nghiệp.

**Các tính năng chính:**

### Dashboard & Báo cáo
*   **Dashboard Tổng quan:** Hiển thị KPI về tài sản (tổng số, đang sử dụng, chưa sử dụng, đã thanh lý), giá trị tài sản, biểu đồ phân bổ theo phòng ban và loại tài sản.
*   **Dashboard Mượn trả:** Thống kê đơn mượn đang chờ duyệt, tài sản đang được mượn, top tài sản được mượn nhiều nhất, danh sách tài sản quá hạn chưa trả.

### Quản lý danh mục & Tài sản
*   **Loại tài sản (`danh_muc_tai_san`):** Phân loại tài sản (ví dụ: Thiết bị điện tử, Nội thất, Phương tiện đi lại).
*   **Quản lý tài sản cụ thể (`tai_san`):** Theo dõi thông tin chi tiết từng tài sản:
    *   Thông tin cơ bản: mã, tên, ngày mua, giá trị ban đầu, giá trị hiện tại
    *   Thông tin kỹ thuật: nhà sản xuất, model, serial number
    *   Vị trí & Trách nhiệm: địa điểm (`location`), người chịu trách nhiệm, phòng ban quản lý
    *   Trạng thái: mới, đang sử dụng, bảo trì, hư hỏng, mất, thanh lý, đã bán, đã hủy
    *   Khấu hao: phương pháp khấu hao (tuyến tính, giảm dần, không), thời gian sử dụng
    *   Tài sản dùng chung: đánh dấu tài sản có thể dùng chung (cho phòng họp)

### Vận hành & Khai thác
*   **Phân bổ tài sản (`phan_bo_tai_san`):** Cấp phát tài sản cho nhân viên hoặc phòng ban cụ thể, theo dõi lịch sử phân bổ.
*   **Đơn mượn tài sản (`don_muon_tai_san`):** Quy trình đăng ký mượn với workflow: Nháp -> Chờ duyệt -> Đã duyệt / Từ chối.
*   **Quản lý mượn trả (`muon_tra_tai_san`):** Quản lý chi tiết quá trình mượn và hoàn trả tài sản, theo dõi thời hạn trả.
*   **Phiếu sử dụng (`phieu_su_dung`):** Ghi nhận việc sử dụng tài sản, tự động cập nhật phân bổ.
*   **Luân chuyển tài sản (`luan_chuyen_tai_san`):** Điều chuyển tài sản giữa các bộ phận/chi nhánh.

### Tài chính & Kế toán
*   **Khấu hao tài sản (`lich_su_khau_hao`):** Tính toán và lưu lịch sử khấu hao tài sản theo thời gian (tuyến tính, giảm dần).
*   **Kiểm kê tài sản (`kiem_ke_tai_san`):** So khớp số lượng thực tế và sổ sách, phát hiện thiếu/thừa.
*   **Thanh lý tài sản (`thanh_ly_tai_san`):** Quy trình thanh lý tài sản hết hạn mức sử dụng hoặc hư hỏng.

### Bảo trì & Mua sắm
*   **Bảo trì tài sản (`bao_tri_tai_san`):** Quản lý lịch sử sửa chữa, bảo dưỡng định kỳ:
    *   Loại bảo trì: bảo trì định kỳ, sửa chữa, bảo hành, nâng cấp
    *   Chi phí: nhân công, vật tư, thuê ngoài
    *   Nhà cung cấp/sửa chữa
    *   Thời gian dừng máy
*   **Phiếu mua sắm (`mua_sam_tai_san`):** Đề xuất và theo dõi mua mới tài sản, tự động tạo tài sản khi nhận hàng.
*   **Đặt phòng (`dat_phong`):** Đặt phòng liên quan đến tài sản (tích hợp với `quan_ly_phong_hop`).

### Cấu hình
*   **Địa điểm (`tai_san.location`):** Cấu hình địa điểm phân cấp (site/building/floor/room) để quản lý vị trí tài sản.
*   **Nhà cung cấp:** Quản lý thông tin nhà cung cấp (tích hợp với `res.partner`).

### Tích hợp
*   Tích hợp với module `nhansu`: Sử dụng thông tin nhân viên, phòng ban, chức vụ.
*   Tích hợp với module `quan_ly_phong_hop`: Cung cấp tài sản cho phòng họp, quản lý tài sản trong phòng.

## 2.3. Module Quản lý Phòng họp (`quan_ly_phong_hop`)
Giải pháp tối ưu hóa việc sử dụng không gian chung, tích hợp chặt chẽ với quản lý tài sản và nhân sự.

**Các tính năng chính:**

### Dashboard nâng cao
*   **Dashboard Tổng quan:** Trung tâm điều hành phòng họp với các KPI chiến lược:
    *   Tổng số phòng, cuộc họp hôm nay/tuần, tổng giờ sử dụng
    *   Tỷ lệ sử dụng phòng, tỷ lệ lãng phí, tỷ lệ hủy, tỷ lệ no-show
    *   Heatmap sử dụng phòng (Giờ x Phòng)
    *   Hiệu suất theo phòng ban/người dùng
    *   Phân tích chất lượng cuộc họp
    *   Tình trạng tài sản & phòng (Asset Health)
    *   Hoạt động gần đây (Activity Feed)
    *   Bộ lọc nâng cao: theo địa điểm, phòng ban, khoảng thời gian

### Quản lý danh sách phòng họp
*   **Phòng họp (`phong_hop`):** Quản lý thông tin chi tiết phòng:
    *   Thông tin cơ bản: mã phòng, tên phòng, sức chứa, loại phòng (nhỏ/vừa/lớn/training/board/conference)
    *   Địa điểm: tích hợp với `tai_san.location` (site/building/floor/room)
    *   Tiện ích: máy chiếu, TV, VC device, bảng trắng, micro, camera, WiFi, điều hòa
    *   Khung giờ hoạt động: giờ bắt đầu/kết thúc hoặc hoạt động cả ngày
    *   Quy định đặt phòng: thời lượng tối thiểu/tối đa, lead time, buffer time
    *   Trạng thái: sẵn sàng, bảo trì, ngừng hoạt động
    *   Thống kê: tỷ lệ sử dụng, số lượng booking, số lượng no-show
*   **Phòng đã đặt:** Danh sách các phòng đã có booking, filter để xem nhanh.

### Đặt phòng & Điều phối
*   **Lịch đặt phòng (`dat_phong_hop`):** Quản lý đặt phòng với workflow đầy đủ:
    *   Workflow: Nháp -> Chờ duyệt -> Đã duyệt / Từ chối -> Đã xác nhận -> Đã check-in -> Đang diễn ra -> Hoàn thành / No-show / Đã hủy
    *   Thông tin đặt phòng: tiêu đề, thời gian bắt đầu/kết thúc, người chủ trì, mục đích
    *   Tích hợp HR: Chọn tham dự theo chức vụ (`chuc_vu`) và phòng ban (`phong_ban`)
    *   Người tham dự: danh sách nhân viên tham dự
    *   Tự động phát hiện xung đột lịch họp
    *   Calendar view: xem theo ngày/tuần/tháng
    *   Check-in/No-show: Quản lý check-in, tự động giải phóng phòng nếu không check-in
*   **Wizard từ chối/Hủy booking:** Quy trình phê duyệt/từ chối với lý do.

### Dịch vụ đi kèm
*   **Dịch vụ phòng họp (`dich_vu_phong_hop`):** Đặt kèm các dịch vụ:
    *   Setup: layout (U-shape/class/theater), số ghế, backdrop
    *   Tea-break/catering: số lượng, menu, thời điểm
    *   IT support: cấu hình họp online, test mic/cam
    *   Vệ sinh/housekeeping: dọn trước/sau
    *   Tài sản/thiết bị mượn kèm: micro, loa, webcam, clicker

### Tài sản phòng họp
*   **Tài sản phòng họp (`tai_san_phong_hop`):** Quản lý tài sản gắn với phòng:
    *   Gắn tài sản từ module `quan_ly_tai_san` vào phòng
    *   Thông tin kỹ thuật: nhà sản xuất, model, serial number
    *   Trạng thái trong phòng: sẵn sàng, đang sử dụng, bảo trì, hư hỏng
    *   Trách nhiệm: người chịu trách nhiệm, phòng ban quản lý
    *   **Các tab chi tiết:**
        *   Tài sản phòng: Thông tin tài sản và trạng thái
        *   Lịch sử bảo trì: Tất cả lịch sử bảo trì của tài sản
        *   Phiếu bảo trì: Chi tiết các phiếu bảo trì với form view
        *   Lịch sử sử dụng: Các phiếu sử dụng tài sản
        *   Phiếu mua sắm: Các phiếu mua sắm liên quan
    *   Tích hợp: Các button để xem chi tiết tài sản, tạo phiếu bảo trì, xem lịch sử trong module `quan_ly_tai_san`

### Bảo trì phòng họp
*   **Bảo trì phòng họp (`bao_tri_phong_hop`):** Quản lý bảo trì phòng với workflow:
    *   Workflow: Nháp -> Đã lên lịch -> Đang thực hiện -> Hoàn thành / Đã hủy
    *   Loại bảo trì: bảo trì định kỳ, sửa chữa, nâng cấp, vệ sinh sâu, kiểm tra thiết bị
    *   Tài sản cần bảo trì: Chọn các tài sản trong phòng cần bảo trì
    *   Chi phí: nhân công, vật tư, thuê ngoài, tổng chi phí
    *   Nhà cung cấp/sửa chữa
    *   Tự động chuyển phòng sang trạng thái bảo trì và hủy các booking trong thời gian bảo trì
    *   **Các tab chi tiết:**
        *   Thông tin bảo trì: Thông tin cơ bản và mô tả
        *   Tài sản bảo trì: Danh sách tài sản cần bảo trì
        *   Chi phí chi tiết: Các khoản chi phí
        *   Kết quả & Ghi chú: Kết quả và ghi chú bổ sung
        *   Lịch sử bảo trì phòng: Tất cả các phiếu bảo trì của phòng

### Tích hợp
*   **Tích hợp với `nhansu`:**
    *   Sử dụng thông tin nhân viên, phòng ban, chức vụ
    *   Chọn tham dự theo chức vụ và phòng ban khi đặt phòng
    *   Khi nhân viên nghỉ việc: tự động hủy booking tương lai
*   **Tích hợp với `quan_ly_tai_san`:**
    *   Gắn tài sản từ module quản lý tài sản vào phòng họp
    *   Xem và quản lý lịch sử bảo trì, sử dụng, mua sắm của tài sản
    *   Tạo phiếu bảo trì cho tài sản từ phòng họp
    *   Đồng bộ trạng thái maintenance của phòng với khả năng đặt phòng

---

# 3. Kiến trúc & Tích hợp Module

## 3.1. Mối quan hệ giữa các module

```
nhansu (Base Module)
    ├── quan_ly_tai_san (Depends on nhansu)
    │   ├── Sử dụng: nhan_vien, phong_ban, chuc_vu
    │   └── Cung cấp: tai_san, location, bao_tri_tai_san, mua_sam_tai_san
    │
    └── quan_ly_phong_hop (Depends on nhansu, quan_ly_tai_san)
        ├── Sử dụng: nhan_vien, phong_ban, chuc_vu (từ nhansu)
        ├── Sử dụng: tai_san, location, bao_tri_tai_san (từ quan_ly_tai_san)
        └── Tích hợp: Gắn tài sản vào phòng, quản lý bảo trì, sử dụng
```

## 3.2. Workflow tích hợp

### Workflow Nhân viên nghỉ việc
1. HR set trạng thái nhân viên = "terminated"
2. Tự động tạo tasks:
   - Thu hồi tài sản đang giữ (`quan_ly_tai_san`)
   - Hủy/Chuyển booking tương lai (`quan_ly_phong_hop`)

### Workflow Đặt phòng họp
1. Nhân viên đặt phòng (`quan_ly_phong_hop`)
2. Chọn tham dự theo chức vụ/phòng ban (`nhansu`)
3. Tự động kiểm tra xung đột lịch
4. Manager duyệt (nếu cần)
5. Facilities chuẩn bị dịch vụ
6. Check-in phòng
7. Kết thúc/Release phòng

### Workflow Bảo trì phòng
1. Tạo phiếu bảo trì (`quan_ly_phong_hop`)
2. Chọn tài sản cần bảo trì (`quan_ly_tai_san`)
3. Tự động chuyển phòng sang trạng thái "maintenance"
4. Hủy các booking trong thời gian bảo trì
5. Tạo phiếu bảo trì tài sản (`quan_ly_tai_san`)
6. Hoàn thành → Khôi phục phòng về "available"

### Workflow Cấp phát tài sản
1. Nhân viên tạo yêu cầu (`quan_ly_tai_san`)
2. Manager duyệt
3. Asset Admin cấp phát
4. Nhân viên ký nhận
5. Tự động cập nhật phân bổ

---

# 4. Hướng dẫn Cài đặt & Triển khai

## 4.1. Yêu cầu hệ thống (Prerequisites)
*   **Hệ điều hành:** Ubuntu 20.04/22.04 (Khuyến nghị) hoặc các bản phân phối Linux tương đương.
*   **Python:** v3.8 trở lên.
*   **Database:** PostgreSQL 12+.

## 4.2. Cài đặt chi tiết

### Bước 1: Clone dự án
Tải mã nguồn về máy local:
```bash
git clone https://github.com/nguyenngocdantruong/TTDN-15-04-N6.git
cd TTDN-15-04-N6
# Checkout branch nếu cần
# git checkout <branch_name>
```

### Bước 2: Cài đặt thư viện hệ thống
Cài đặt các gói phụ thuộc cần thiết cho Odoo và thư viện Python:
```bash
sudo apt-get update
sudo apt-get install -y libxml2-dev libxslt-dev libldap2-dev libsasl2-dev libssl-dev \
    python3.10-distutils python3.10-dev build-essential libffi-dev zlib1g-dev \
    python3.10-venv libpq-dev docker-compose
```

### Bước 3: Thiết lập môi trường ảo (Virtual Environment)
Khuyến nghị sử dụng `venv` để cô lập môi trường chạy:
```bash
# Tạo môi trường ảo
python3.10 -m venv ./venv

# Kích hoạt môi trường
source venv/bin/activate

# Cài đặt các thư viện Python
pip3 install -r requirements.txt
```

### Bước 4: Khởi tạo Database (PostgreSQL)
Sử dụng Docker để khởi tạo container PostgreSQL nhanh chóng:
```bash
# Khởi chạy container database ở chế độ background
sudo docker-compose up -d
```
*Lưu ý: Kiểm tra file `docker-compose.yml` để đảm bảo cổng 5434 chưa được sử dụng.*

### Bước 5: Cấu hình Odoo
Tạo file cấu hình `odoo.conf` tại thư mục gốc của dự án:

```ini
[options]
addons_path = addons
db_host = localhost
db_password = odoo
db_user = odoo
db_port = 5434
xmlrpc_port = 8069
```

### Bước 6: Khởi chạy hệ thống
Kích hoạt hệ thống và cập nhật danh sách module:

```bash
# Upgrade tất cả modules
python3 odoo-bin.py -c odoo.conf -u all

# Hoặc upgrade từng module cụ thể
python3 odoo-bin.py -c odoo.conf -d <database_name> -u nhansu,quan_ly_tai_san,quan_ly_phong_hop --stop-after-init
```

**Truy cập hệ thống:**
*   Mở trình duyệt và truy cập: `http://localhost:8069/`
*   Đăng nhập với tài khoản quản trị viên mặc định (nếu có) hoặc tạo cơ sở dữ liệu mới.

## 4.3. Cài đặt Module

### Thứ tự cài đặt khuyến nghị:
1. **nhansu** - Module cơ sở, cần cài trước
2. **quan_ly_tai_san** - Phụ thuộc vào `nhansu`
3. **quan_ly_phong_hop** - Phụ thuộc vào cả `nhansu` và `quan_ly_tai_san`

### Cài đặt trong Odoo UI:
1. Vào **Apps** → Tìm kiếm module
2. Click **Install** cho từng module theo thứ tự trên
3. Hoặc sử dụng command line như ở Bước 6

### Xử lý lỗi "Internal Server Error" (localhost:8069)

Lỗi **Internal Server Error** khi mở `http://localhost:8069` thường do **không kết nối được PostgreSQL** hoặc cấu hình sai cổng.

**Cách xử lý:**

1. **Kiểm tra PostgreSQL đang chạy**
   - Nếu dùng **Docker**: `docker-compose up -d` (container chạy, port **5434**).
   - Nếu cài PostgreSQL trên máy: `sudo systemctl status postgresql` (port mặc định **5432**).

2. **Khớp cổng trong `odoo.conf`**
   - Dùng **Docker** (như `docker-compose.yml`): đặt `db_port = 5434`, `db_host = localhost`.
   - Dùng PostgreSQL local: đặt `db_port = 5432`, `db_host = localhost`.
   - Đảm bảo `db_user` và `db_password` trùng với PostgreSQL (Docker: user `odoo`, password `odoo`).

3. **Xem log chi tiết**
   - Chạy Odoo với: `python3 odoo-bin.py -c odoo.conf --log-level=debug`
   - Mở lại `http://localhost:8069` và xem traceback trong terminal để biết lỗi cụ thể.

4. **Tạo database nếu chưa có**
   - Vào `http://localhost:8069/web/database/selector` (nếu không bị lỗi kết nối) và tạo database mới, sau đó cài đặt module.

---

# 5. Cấu trúc Module

## 5.1. Module `nhansu`
```
nhansu/
├── models/
│   ├── phong_ban.py          # Phòng ban
│   ├── chuc_vu.py            # Chức vụ
│   ├── nhan_vien.py          # Nhân viên
│   ├── cham_cong.py          # Chấm công
│   ├── vi_pham_cham_cong.py  # Vi phạm chấm công
│   ├── tang_ca.py            # Tăng ca
│   ├── ky_luong.py           # Kỳ lương
│   ├── bang_luong_thang.py   # Bảng lương tháng
│   ├── chung_chi_bang_cap.py # Chứng chỉ, bằng cấp
│   └── lich_su_cong_tac.py   # Lịch sử công tác
├── views/                    # XML views
├── security/                 # Access rights
└── __manifest__.py
```

## 5.2. Module `quan_ly_tai_san`
```
quan_ly_tai_san/
├── models/
│   ├── danh_muc_tai_san.py   # Loại tài sản
│   ├── tai_san.py            # Tài sản cụ thể
│   ├── phan_bo_tai_san.py    # Phân bổ tài sản
│   ├── don_muon_tai_san.py   # Đơn mượn tài sản
│   ├── muon_tra_tai_san.py   # Mượn trả tài sản
│   ├── luan_chuyen_tai_san.py # Luân chuyển
│   ├── thanh_ly_tai_san.py   # Thanh lý
│   ├── lich_su_khau_hao.py   # Khấu hao
│   ├── kiem_ke_tai_san.py    # Kiểm kê
│   ├── bao_tri_tai_san.py    # Bảo trì
│   ├── mua_sam_tai_san.py    # Mua sắm
│   ├── phieu_su_dung.py      # Phiếu sử dụng
│   ├── location.py           # Địa điểm
│   ├── dat_phong.py          # Đặt phòng (tài sản)
│   └── dashboard.py         # Dashboard model
├── views/
│   ├── dashboard_overview.xml    # Dashboard tổng quan
│   ├── dashboard_borrowing.xml   # Dashboard mượn trả
│   └── ...
├── static/
│   ├── src/js/              # JavaScript cho dashboard
│   └── src/css/             # CSS styling
├── security/
└── __manifest__.py
```

## 5.3. Module `quan_ly_phong_hop`
```
quan_ly_phong_hop/
├── models/
│   ├── phong_hop.py          # Phòng họp
│   ├── dat_phong_hop.py      # Đặt phòng
│   ├── dich_vu_phong_hop.py  # Dịch vụ
│   ├── bao_tri_phong_hop.py  # Bảo trì phòng
│   ├── tai_san_phong_hop.py  # Tài sản phòng họp
│   ├── dashboard_phong_hop.py # Dashboard model
│   └── wizard/               # Wizards
│       ├── wizard_reject_booking.py
│       ├── wizard_cancel_booking.py
│       └── wizard_add_assets.py
├── views/
│   ├── dashboard_phong_hop.xml  # Dashboard view
│   └── ...
├── static/
│   ├── src/js/dashboard_phong_hop.js  # Dashboard JavaScript
│   └── src/css/dashboard.css          # Dashboard CSS
├── data/
│   ├── ir_sequence_data.xml   # Sequences
│   └── ir_cron_data.xml       # Cron jobs
├── security/
└── __manifest__.py
```

---

# 6. Tính năng nổi bật

## 6.1. Dashboard nâng cao
*   **Dashboard Quản lý Tài sản:** Tổng quan tài sản, phân bổ, mượn trả với biểu đồ trực quan (Chart.js)
*   **Dashboard Quản lý Phòng họp:** Trung tâm điều hành với heatmap, KPI chiến lược, phân tích hiệu suất, bộ lọc nâng cao

## 6.2. Tích hợp liền mạch
*   Tích hợp chặt chẽ giữa 3 module: Nhân sự ↔ Tài sản ↔ Phòng họp
*   Workflow tự động: Offboarding → Thu hồi tài sản + Hủy booking
*   Đồng bộ trạng thái: Bảo trì phòng → Hủy booking tự động

## 6.3. Quy trình phê duyệt
*   Đơn mượn tài sản: Workflow phê duyệt đầy đủ
*   Đặt phòng họp: Phê duyệt theo quy tắc (thời lượng, ngoài giờ, số người)
*   Bảo trì: Quy trình từ lên lịch đến hoàn thành

## 6.4. Quản lý chi tiết
*   **Tài sản phòng họp:** Các tab chi tiết về lịch sử bảo trì, sử dụng, mua sắm
*   **Bảo trì phòng:** Quản lý chi tiết từ thông tin, tài sản, chi phí đến lịch sử
*   **Đặt phòng:** Tích hợp HR để chọn tham dự theo chức vụ và phòng ban

---

© 2024 Nhóm TTDN-16-02-N6. All rights reserved.
