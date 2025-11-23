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

# 🍽️ NutriDish – Food Recognition & Nutrition Tracker

NutriDish identifies dishes from images (PyTorch ResNet / ViT) and provides nutrition breakdown plus personalized daily targets. A Flask backend serves REST APIs and server‑side rendered Handlebars templates. Supabase handles authentication (JWT), persistence (users, profiles, food logs, daily summaries) and image storage.

## Overview

NutriDish combines image inference, nutrition lookup, goal evaluation, and historical analytics. Frontend pages are rendered server‑side (fast first paint) while selective client JavaScript enhances interactivity. Models and nutrition data are pluggable for future extension.

## Architecture Summary

Backend (Flask) exposes API blueprints for prediction, meals, user profile, health. Services encapsulate model loading, nutrition source access (CSV or Supabase), Supabase storage/API calls, templating, and goal calculations. Frontend Handlebars templates form pages; partials provide reusable header/footer/components.

## Directory Structure (Key Paths)

```
flask_backend/app/
  flask_app.py              # App factory + SSR page routes
  routes/                   # API endpoints (predict, meals, user, health)
  controllers/              # Orchestrates services + request flow
  middlewares/auth.py       # Supabase JWT or dev fallback auth
  services/
    inference_service.py    # PyTorch model load & predict (caching)
    nutrition_service.py    # Nutrition lookup (CSV or Supabase table)
    nutrition_goal_service.py# Target calculations & daily evaluation
    supabase_service.py     # Wraps supabase-py (auth, storage, DB)
    templating.py           # Handlebars server-side rendering
web/
  templates/pages/*.hbs     # Page templates (login, today, upload, etc.)
  templates/partials/*.hbs  # Header, footer, stats blocks
  js/                       # Page enhancement scripts
  assets/                   # Static images, icons, logo
  config.js                 # Client Supabase + backend config
ml_models/                  # PyTorch weight files (.pth)
data/nutrition_database.csv # Local nutrition fallback dataset
supabase/schema.sql         # Tables & policies
```

## Setup

```bash
python -m venv .venv
./.venv/Scripts/activate   # Windows PowerShell
pip install -r flask_backend/requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Environment (.env)

```
SUPABASE_URL=<project-url>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_BUCKET=food-uploads
REQUIRE_JWT=true            # false for dev fallback
```

Client config (`web/config.js`):

```js
window.APP_CONFIG = {
  BACKEND_URL: window.location.origin,
  SUPABASE_URL: "<project-url>",
  SUPABASE_ANON_KEY: "<anon-key>",
};
```

Apply SQL: open `supabase/schema.sql` in Supabase SQL editor.

## Running

```bash
cd .\flask_backend\
.\.venv\Scripts\Activate.ps1
npm run dev    
```

Open http://localhost:8000

## Docker (Optional)

```bash
docker compose up --build
```

## Models

Place weight files: `best_food101_model.pth`, `best_vit_vn30food_model.pth` in `ml_models/`. The inference service auto-detects by configured keys (e.g. `resnet_food101`, `vn30`). First request loads into memory; subsequent predictions use cached instance.

## Core APIs (Selected)

Prediction:

- `GET /api/predict/models` – list available models
- `POST /api/predict` – multipart form: `file`, optional `model`

Meals & Nutrition:

- `POST /api/meals/log` – save meal (image + servings + meal_type)
- `GET /api/meals/today` – today logs + totals + goal evaluation
- `GET /api/meals/history` – date range aggregated logs
- `GET /api/stats/series` – bucketed historical series (day/week/month/year)

User:

- `GET /api/user/profile`
- `POST /api/user/profile`
- `POST /api/user/avatar`

Health:

- `GET /health`

## Authentication

Supabase JWT is expected when `REQUIRE_JWT=true`. In dev (`REQUIRE_JWT=false`) fallback header `X-User-Id` (or `DEMO_USER_ID` in `.env`) can be used. Middleware attempts admin validation; if unavailable, a safe JWT payload decode fallback extracts `sub` for user id.

## Nutrition & Goals

`nutrition_service.py` obtains per-serving macros (calories, protein, fat, carbs, fiber). `nutrition_goal_service.py` computes targets from profile (age, weight, height, gender, activity) and evaluates daily completeness plus macro deficits/excesses. Recommendations retrieved from nutrition dataset when deficits exist.

## Client Functionality

- Upload: image preview, model selection, prediction, top-5 alternatives, macro progress bars.
- Today: detect & save meal inline; totals, missing macros, mini charts, pie chart.
- Statistics: historical macro trends, bucket selection, dynamic targets, advice.
- Profile: set demographics for personalized targets; avatar upload.

## Testing (Manual Quick Checks)

```bash
curl http://localhost:8000/health
curl -F "file=@dish.jpg" http://localhost:8000/api/predict
```

Functional user-level test cases (examples): login, upload & predict, save meal (nutrition scaled by servings), view daily totals, edit profile, fetch historical series, delete meal log.

## Dependencies (Minimal)

`flask_backend/requirements.txt` contains:

```
Flask
flask-cors
python-dotenv
supabase
pybars3
pandas
pillow
```

Install PyTorch separately (see setup). Removed: tensorflow, keras, httpx, unused extras.

## Troubleshooting

| Issue              | Resolution                                                  |
| ------------------ | ----------------------------------------------------------- |
| Missing model      | Verify filename in `ml_models/` matches expected key        |
| Auth 401           | Check Supabase keys, JWT enabled, session exists, time sync |
| Images not shown   | Confirm `/app/assets/...` path & served from `web/`         |
| Slow first predict | Normal (model load); consider preload on startup            |
| Timezone mismatch  | Code normalizes UTC then filters local date                 |

## Performance Notes

Model caching avoids repeat loads. Aggregations compute per bucket using Python filtering + Supabase queries. Optional enhancements: background inference service, CDN for static assets, macro-level caching of nutrition rows.

## Roadmap

- Multi-food detection (YOLO / DETR)
- Target evolution & smarter recommendations
- Mobile offline capture & sync
- Recipe parsing & barcode scanning
- Voice command input

## Team

Tran Dinh Khuong – ML / Backend  
Nguyen Nhat Phat – API / Database  
Tran Huynh Xuan Thanh – Frontend / UI  
Supervisor: Assoc. Prof. Dr. Hoang Van Dung

## License

Academic project (15‑week course). For internal educational use.

## Contributing

Internal project; for suggestions or issues, contact the team directly.

---

Enjoy exploring AI‑powered food recognition and nutrition analysis!
