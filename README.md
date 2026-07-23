# Công cụ tự động dọn dẹp thư mục (File Organizer) trên Linux


##  Tính năng nổi bật
- **Tự động di chuyển**: Vd: Chuyển ngay các định dạng ảnh vào `~/Pictures` và tài liệu vào `~/Documents`.
- **Bỏ qua file tải dở**: Tự động bỏ qua các file tạm (`.crdownload`, `.part`, `.tmp`).
- **An toàn dữ liệu (Chống ghi đè)**: Nếu file trùng tên đã tồn tại ở thư mục đích, công cụ tự đổi tên thành `file_1.ext`, `file_2.ext`.
- **Hai chế độ chạy**:
  - Chạy thủ công 1 lần (`python3 file_organizer.py`)
  - Chạy ngầm liên tục theo dõi (`--watch`) hoặc tích hợp vào Systemd User Service.
- **Chế độ xem trước (`--dry-run`)**: Kiểm tra xem file nào sẽ bị di chuyển mà không làm thay đổi thư mục thật.

---

## 🚀 Hướng dẫn sử dụng

### 1. Chạy quét 1 lần thủ công
```bash
python3 file_organizer.py
```

### 2. Chế độ xem trước (Dry-run)
```bash
python3 file_organizer.py --dry-run
```

### 3. Chạy theo dõi liên tục trong Terminal
```bash
python3 file_organizer.py --watch --interval 5
```

---

## ⚙️ Cài đặt chạy tự động ngầm khi bật máy (Systemd Service)

Để công cụ tự động chạy ngầm mỗi khi bạn đăng nhập vào Linux:

### Cài đặt:
```bash
./install.sh
```

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

Bạn có thể mở rộng danh sách loại file bằng cách chỉnh sửa từ điển `CATEGORIES` trong file [config.json](file:///home/kaz/ProjectLinux/config.json):

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
