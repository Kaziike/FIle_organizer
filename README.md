# Công cụ tự động dọn dẹp thư mục (File Organizer) trên Linux

<<<<<<< HEAD

##  Tính năng nổi bật
- **Tự động di chuyển**: Vd: Chuyển ngay các định dạng ảnh vào `~/Pictures` và tài liệu vào `~/Documents`.
- **Bỏ qua file tải dở**: Tự động bỏ qua các file tạm (`.crdownload`, `.part`, `.tmp`).
- **An toàn dữ liệu (Chống ghi đè)**: Nếu file trùng tên đã tồn tại ở thư mục đích, công cụ tự đổi tên thành `file_1.ext`, `file_2.ext`.
- **Hai chế độ chạy**:
  - Chạy thủ công 1 lần (`python3 file_organizer.py`)
  - Chạy ngầm liên tục theo dõi (`--watch`) hoặc tích hợp vào Systemd User Service.
- **Chế độ xem trước (`--dry-run`)**: Kiểm tra xem file nào sẽ bị di chuyển mà không làm thay đổi thư mục thật.
=======
Công cụ tự động quét nhiều thư mục nguồn được cấu hình (ví dụ: `~/Downloads`, `~/data`, `~/Desktop`) và phân loại file tự động.
>>>>>>> 4cfa0fa (automatically categorize multiple folders)

---

## 🛠️ Quản lý Thư mục nguồn & Danh mục phân loại

### 1. Quản lý Thư mục nguồn (Source Directories)

Bạn có thể cấu hình cho công cụ theo dõi cùng lúc nhiều thư mục khác nhau thay vì chỉ mỗi `~/Downloads`.

#### 🔹 Qua Menu tương tác:
Chạy lệnh mở menu:
```bash
python3 file_organizer.py -i
```
Chọn **[1] Quản lý Thư mục nguồn** để Thêm / Xóa thư mục nguồn cần quét (ví dụ: `~/data`, `~/Desktop`).

#### 🔹 Qua lệnh CLI trực tiếp:
- **Thêm thư mục nguồn cần phân loại (`--add-source`)**:
  ```bash
  python3 file_organizer.py --add-source ~/data
  ```
- **Xóa thư mục nguồn (`--delete-source`)**:
  ```bash
  python3 file_organizer.py --delete-source ~/data
  ```

#### 🔹 Qua file cấu hình [config.json](`~/config.json`):
Chỉnh sửa danh sách `source_dirs`:
```json
{
    "source_dirs": [
        "~/Downloads",
        "~/data",
        "~/Desktop"
    ],
    "categories": { ... }
}
```

---

### 2. Quản lý Danh mục phân loại (File Categories)

#### 🟢 Thêm danh mục mới (`--add-category`):
```bash
python3 file_organizer.py --add-category Ebooks ~/Books .epub .mobi
```

#### 🟡 Sửa danh mục hiện có (`--edit-category`):
```bash
# Đổi thư mục đích
python3 file_organizer.py --edit-category Videos --target-dir ~/Movies

# Thêm đuôi file
python3 file_organizer.py --edit-category AppApp --add-ext .iso .img
```

#### 🔴 Xóa danh mục (`--delete-category`):
```bash
python3 file_organizer.py --delete-category Archives
```

---

## 🚀 Các lệnh cơ bản

```bash
# Xem toàn bộ cấu hình hiện tại (Thư mục nguồn & Danh mục phân loại)
python3 file_organizer.py --list-rules

# Xem trước di chuyển file không làm thay đổi thư mục thật (Dry-run)
python3 file_organizer.py --dry-run

# Chạy quét 1 lần tất cả thư mục nguồn
python3 file_organizer.py
```

---

## ⚙️ Cài đặt chạy ngầm (Systemd Service)

Systemd Service sẽ tự động chạy ngầm và quét toàn bộ các thư mục trong `source_dirs` (ví dụ: `~/Downloads`, `~/data`):
```bash
./install.sh
```
<<<<<<< HEAD

### Kiểm tra trạng thái service:
```bash
systemctl --user status file-organizer.service
```

### Xem log hoạt động theo thời gian thực:
```bash
journalctl --user -u file-organizer.service -f
```

### Tắt / Gỡ bỏ service:
```bash
./install.sh --uninstall
```

---

## 🛠️ Tùy chỉnh danh mục mở rộng

Bạn có thể mở rộng danh sách loại file bằng cách chỉnh sửa từ điển `CATEGORIES` trong file [config.json](`~/config.json`):

```python
{
    "Pictures": {
        "extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
        "target_dir": Path.home() / "Pictures"
    },
    "Documents": {
        "extensions": [".pdf", ".docx", ".doc", ".xlsx", ".pptx", ".txt"],
        "target_dir": Path.home() / "Documents"
    }
}
```
=======
>>>>>>> 4cfa0fa (automatically categorize multiple folders)
