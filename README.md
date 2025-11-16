# 🍽️ NutriDish – Food Recognition & Nutrition Tracker

NutriDish nhận diện món ăn từ ảnh (PyTorch ViT / ResNet) và cung cấp thông tin dinh dưỡng + mục tiêu hằng ngày. Backend Flask phục vụ API và render Handlebars SSR, Supabase dùng cho Auth, lưu trữ ảnh và dữ liệu người dùng.

## 📦 Thành phần chính

| Layer           | Công nghệ                    | Vai trò                                          |
| --------------- | ---------------------------- | ------------------------------------------------ |
| Backend         | Flask + flask-cors           | API REST + render template SSR                   |
| Auth/DB/Storage | Supabase                     | Auth JWT, bảng `users`/`food_logs`, bucket ảnh   |
| Templates       | Handlebars (pybars3)         | Layout + partials + pages `.hbs`                 |
| ML Inference    | PyTorch (torch, torchvision) | Load model ViT / ResNet (file `.pth`)            |
| Nutrition Data  | CSV (built-in csv)           | Fallback dinh dưỡng nếu không dùng bảng Supabase |

## 📁 Cấu trúc (rút gọn)

```
flask_backend/
  app/
    flask_app.py            # App factory + routes trang
    routes/                 # API endpoints (health, user, meals, predict, etc.)
    controllers/            # Logic kết hợp service + request
    middlewares/auth.py     # Xác thực Supabase token / chế độ dev
    services/
      inference_service.py  # PyTorch model load & predict
      nutrition_service.py  # Đọc CSV hoặc Supabase
      nutrition_goal_service.py  # Tính target dinh dưỡng
      supabase_service.py   # Wrapper supabase-py
      templating.py         # Render Handlebars layout + pages
web/
  assets/                   # Ảnh tĩnh, favicon, logo
  templates/partials/*.hbs  # header, footer, components
  templates/pages/*.hbs     # Các trang (login, today, upload, ...)
  config.js                 # Config Supabase phía client
ml_models/ *.pth            # Trained PyTorch weights
data/nutrition_database.csv # Dữ liệu dinh dưỡng cục bộ
```

## 🚀 Chạy nhanh (Local)

Yêu cầu: Python 3.10+, pip.

```bash
python -m venv .venv
./.venv/Scripts/activate  # Windows PowerShell
pip install -r flask_backend/requirements.txt
python -m flask_backend.app.flask_app
```

Truy cập: http://localhost:8000

## 🔐 Cấu hình Supabase

Tạo project Supabase rồi đặt biến môi trường (file `.env` ở thư mục gốc hoặc `flask_backend/.env`):

```
SUPABASE_URL=your-project-url
SUPABASE_SERVICE_ROLE_KEY=service-role-key
SUPABASE_BUCKET=food-uploads
REQUIRE_JWT=true
```

Chạy `supabase/schema.sql` trong SQL editor để tạo bảng/policy.

Phía client (`web/config.js`):

```js
window.APP_CONFIG = {
  BACKEND_URL: window.location.origin,
  SUPABASE_URL: "https://xxxx.supabase.co",
  SUPABASE_ANON_KEY: "anon-public-key",
};
```

## 🧠 Mô hình ML

- Hai cấu hình: `resnet_food101` (ResNet50) và `vn30` (ViT B/16 tùy biến).
- File trọng số đặt trong `ml_models/` (ví dụ `best_food101_model.pth`).
- Service `inference_service.py` tự dò path và cache model.

## 🔄 Dự đoán ảnh

Endpoint (ví dụ): `POST /api/predict` multipart form: `file`.
Kết quả: tên món ăn (top-1), danh sách top-5 và độ tự tin.

## 📊 Dinh dưỡng & Mục tiêu

- `nutrition_service.py`: đọc từ CSV hoặc bảng `nutrition` Supabase (qua biến `USE_SUPABASE_NUTRITION=true`).
- `nutrition_goal_service.py`: tính toán TDEE + macro target.
- Các API meals lưu log, tổng hợp ngày, streak.

## 🧾 Dependencies (đã tối giản)

`flask_backend/requirements.txt` (tối giản):

```
Flask
flask-cors
python-dotenv
supabase
pybars3
pillow
# PyTorch cài riêng: torch torchvision torchaudio (CPU wheels)
```

ĐÃ BỎ: tensorflow, keras, httpx, numpy, pandas (CSV parse bằng csv module, giảm RAM).

## 🧪 Kiểm tra nhanh

```bash
curl http://localhost:8000/health
```

## 🐳 Docker (tùy chọn)

```bash
docker compose up --build
```

Ứng dụng tại: http://localhost:8000

## ❌ Gỡ bỏ gói thừa (nếu đã cài trước đó)

```bash
pip uninstall -y tensorflow keras httpx
```

## 🔧 Troubleshooting rút gọn

- 404 model: kiểm tra tên file `.pth` trong `ml_models/`.
- Lỗi Supabase Auth: kiểm tra `SUPABASE_SERVICE_ROLE_KEY` và thời gian hệ thống.
- Ảnh không hiển thị: đảm bảo đường dẫn `/app/assets/...` (Flask phục vụ `web/`).

## 👥 Đội ngũ

Tran Dinh Khuong – ML / Backend  
Nguyen Nhat Phat – API / DB  
Tran Huynh Xuan Thanh – Frontend / UI  
Supervisor: Assoc. Prof. Dr. Hoang Van Dung

## 📌 Định hướng tương lai

- Multi-food detection
- Ứng dụng di động
- Recipe & barcode
- Voice commands

---

Enjoy NutriDish!

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- At least 4GB RAM (for ML model)

### 1. Clone Repository

```bash
git clone <repository-url>
cd foodapp
```

### 2. Configure Supabase (once)

1. Create a Supabase project, copy the Project URL and keys (Anon and Service Role).
2. In the Supabase SQL editor, run the SQL in `supabase/schema.sql` to create tables and policies.
3. Create a public Storage bucket named `food-uploads`.
4. Create a copy of `backend/.env.example` as `backend/.env` and fill in:

```
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_BUCKET=food-uploads
```

For the frontend, set `SUPABASE_URL` and `SUPABASE_ANON_KEY` via `.env` or Streamlit secrets.

### 3. Start Backend + Frontend (Docker Compose)

```bash
docker compose up --build
```

App available at http://localhost:8000 (frontend served at `/`), API at `/api/*`.

### 4. (Optional) Start Flask backend locally

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Start Flask server
python -m flask_backend.app.flask_app
```

Backend will be available at: http://127.0.0.1:8000

- API Documentation: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/health

### Frontend configuration

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
pip install -r requirements.txt

# Start Streamlit app
Copy `web/config.example.js` to `web/config.js` and set your URLs/keys.
#Start API routes
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

```

Frontend will be available at: http://localhost:8501

## 🔧 Features

### AI-Powered Food Recognition

- **131 Food Categories**: 101 international + 30 Vietnamese dishes
- **High Accuracy**: ResNet50 deep learning architecture
- **Confidence Scores**: Prediction confidence with visual indicators
- **Top-3 Predictions**: Alternative predictions with confidence levels

### Comprehensive Nutrition Database

- **Detailed Information**: Calories, protein, fat, carbohydrates, fiber
- **Per Serving Values**: All nutritional values calculated per typical serving
- **Health Suggestions**: AI-generated dietary recommendations
- **Search & Compare**: Search dishes and compare nutritional values

### Modern Web Interface

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Processing**: Fast image analysis and results
- **Interactive UI**: Streamlit-powered user interface
- **Multi-page Navigation**: Organized content across multiple pages

### Developer-Friendly API

- **RESTful Design**: Clean and intuitive API endpoints
- **Auto Documentation**: Swagger/OpenAPI documentation
- **CORS Enabled**: Ready for frontend integration
- **Error Handling**: Comprehensive error responses

## Technical Notes

- Flask render SSR: `templating.py` cung cấp biến script CDN (Supabase, Chart.js, Handlebars).
- Auth linh hoạt: chế độ dev có thể bỏ JWT (`REQUIRE_JWT=false`) và dùng header `X-User-Id`.
- Supabase Storage: upload file tạm rồi gọi API storage (xử lý trường hợp client yêu cầu path file).
- Timezone xử lý logs: chuẩn hóa UTC rồi lọc lại theo local timezone.

## Usage Instructions

### For Users

1. **Start both servers** (backend and frontend)
2. **Navigate to frontend** at http://localhost:8501
3. **Go to Predict page** using sidebar navigation
4. **Upload food image** (JPG, PNG, JPEG - max 10MB)
5. **Click "Analyze Food"** to get results
6. **View results**: Food name, confidence, nutrition info, alternatives

### For Developers

1. **API Testing**: Use http://127.0.0.1:8000/docs for interactive testing
2. **Custom Integration**: Make HTTP requests to API endpoints
3. **Model Updates**: Replace `.keras` model file and class mapping
4. **Database Updates**: Modify `nutrition_database.csv` for new dishes

### Supported Formats

- **JPG/JPEG**: Recommended for photos
- **PNG**: Good for graphics and screenshots
- **Maximum size**: 10MB per image
- **Minimum resolution**: 64×64 pixels

## API Endpoints

### Prediction

- `POST /api/predict` - Upload image for food recognition
- `GET /api/predict/status` - Get prediction service status
- `GET /api/predict/test` - Test prediction endpoint

### Nutrition

- `GET /api/nutrition/{dish_name}` - Get nutrition info
- `GET /api/nutrition/search/dishes?query={term}` - Search dishes
- `GET /api/nutrition/database/summary` - Database statistics
- `GET /api/nutrition/compare?dishes={dish1,dish2}` - Compare nutrition

### Information

- `GET /api/aboutus` - HTML about page
- `GET /api/aboutus/json` - JSON project info
- `GET /api/aboutus/team` - Team member details

### User, Meals & Progress

- `POST /api/user/profile` - Save profile and calculated targets
- `GET /api/user/profile?user_id=...` - Get profile by user id
- `POST /api/meals/log` - Multipart form: file + user_id + meal_type + servings
- `GET /api/meals/today?user_id=...` - Today logs + totals + evaluation
- `GET /api/streak?user_id=...` - Current streak of completed days

## Testing

### Manual Testing

1. **Health Check**: `curl http://127.0.0.1:8000/health`
2. **Image Upload**: Use frontend or API docs at `/docs`
3. **Nutrition Query**: `curl http://127.0.0.1:8000/api/nutrition/pho_bo`

### Automated Testing

```bash
# Backend tests (if implemented)
cd backend
python -m pytest

# Frontend testing through manual interaction
cd frontend
streamlit run streamlit_app.py
```

## 🔧 Troubleshooting

### Common Issues

**Backend won't start:**

- Check Python version (3.8+)
- Install requirements: `pip install -r requirements.txt`
- Check port 8000 availability

**Model loading fails:**

- Ensure `best_model_phase2.keras` exists in `backend/app/ml_models/`
- Check available memory (>4GB recommended)
- Verify TensorFlow installation

**Frontend can't connect:**

- Ensure backend is running on port 8000
- Check CORS settings in backend
- Verify network connectivity

**Prediction errors:**

- Check image format (JPG, PNG, JPEG)
- Verify image size (<10MB)
- Ensure image is not corrupted

### Hiệu năng

- Lần dự đoán đầu: tải model (~vài giây CPU).
- Cache model trong `_model_cache` giảm độ trễ các request sau.
- Tối ưu thêm: preload model khi app khởi động nếu cần.

## Development Team

- **Tran Dinh Khuong** (23110035) - Lead Developer & ML Engineer
- **Nguyen Nhat Phat** (23110053) - Backend Developer & API Engineer
- **Tran Huynh Xuan Thanh** (23110060) - Frontend Developer & UI/UX Designer

**Supervisor**: Assoc. Prof. Dr. Hoang Van Dung

## Project Statistics

- **Development Time**: 15 weeks
- **Food Categories**: 131 (101 international + 30 Vietnamese)
- **Model Parameters**: 23M+ parameters
- **API Endpoints**: 12 endpoints
- **Technologies Used**: 8+ frameworks and libraries

## Future Enhancements (detail)

- Multi-item detection (YOLO / DETR).
- Personal goals history & recommendations ML.
- Recipe parsing & ingredient macro aggregation.
- Offline mobile capture + sync.

## License

This project is developed for academic purposes as part of a 15-week IT project course.

## Contributing

This is an academic project. For suggestions or issues, please contact the development team.

---

**Enjoy exploring the world of AI-powered food recognition and nutrition analysis!**
