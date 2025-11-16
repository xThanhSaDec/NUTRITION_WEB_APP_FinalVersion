docker-compose up --build

# ⚙️ NutriDish Setup (Flask + PyTorch)

## 1. Yêu cầu

- Python 3.10+ (khuyến nghị)
- 4GB RAM (tải model lần đầu)
- Git, pip

## 2. Tạo virtual environment & cài đặt

```bash
python -m venv .venv
./.venv/Scripts/activate  # Windows PowerShell
pip install -r flask_backend/requirements.txt
```

## 3. Cấu hình môi trường

Tạo file `.env` ở root hoặc `flask_backend/.env`:

```
SUPABASE_URL=your-project-url
SUPABASE_SERVICE_ROLE_KEY=service-role-key
SUPABASE_BUCKET=food-uploads
REQUIRE_JWT=true
```

Sao chép `web/config.example.js` thành `web/config.js` và điền `SUPABASE_URL`, `SUPABASE_ANON_KEY`.

Chạy SQL trong `supabase/schema.sql` (Supabase SQL Editor) để tạo bảng/policy.

## 4. Chạy ứng dụng

```bash
python -m flask_backend.app.flask_app
```

Truy cập http://localhost:8000

## 5. Kiểm tra nhanh

```bash
curl http://localhost:8000/health
```

## 6. Tải model

Đặt file trọng số (`best_food101_model.pth`, `best_vit_vn30food_model.pth`) vào `ml_models/` ở root. Service tự động tìm.

## 7. Docker (tuỳ chọn)

```bash
docker compose up --build
```

## 8. Gỡ bỏ gói thừa (nếu đã cài trước đó)

```bash
pip uninstall -y tensorflow keras httpx
```

## 9. Cấu trúc quan trọng

```
flask_backend/app/
	flask_app.py          # App factory
	routes/               # API endpoints
	services/             # Inference, nutrition, Supabase, templating
web/templates/pages/    # Trang .hbs
web/templates/partials/ # Header, footer...
web/assets/             # Logo, favicon, hình
ml_models/              # Trọng số PyTorch
```

## 10. Troubleshooting

| Vấn đề            | Giải pháp                                                          |
| ----------------- | ------------------------------------------------------------------ |
| 404 model         | Kiểm tra tên file `.pth` chính xác đặt trong `ml_models/`          |
| Supabase Auth lỗi | Kiểm tra URL, key; đồng bộ thời gian hệ thống                      |
| Ảnh không hiện    | Đảm bảo đường dẫn `/app/assets/...` (Flask phục vụ thư mục `web/`) |
| QUIC timeout      | Tạm tắt QUIC trong trình duyệt hoặc thử Firefox                    |

## 11. Hiệu năng

- Lần đầu dự đoán: model load vào RAM.
- Dự đoán sau: sử dụng cache `_model_cache`.
- Có thể preload bằng cách gọi `get_inference_service()` khi khởi động.

## 12. Nâng cấp sau

- Multi-food detection YOLO/DETR.
- Lưu lịch sử target & khuyến nghị.
- Mobile offline capture.
- Recipe macro parsing.

Hoàn tất cài đặt! 🎉
