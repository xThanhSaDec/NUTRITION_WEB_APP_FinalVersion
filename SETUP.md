docker compose up --build

# ⚙️ NutriDish Setup (Flask + PyTorch)

## 1. Requirements

- Python 3.10+ (recommended)
- Git, pip
- ≥ 4 GB RAM (first model load)

## 2. Virtual Environment & Install

```bash
python -m venv .venv
./.venv/Scripts/activate  # Windows PowerShell
pip install -r flask_backend/requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

## 3. Environment Configuration

Create `.env` at project root (or `flask_backend/.env`):

```
SUPABASE_URL=<your-project-url>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_BUCKET=food-uploads
REQUIRE_JWT=true   # false for local dev fallback
```

Copy `web/config.example.js` → `web/config.js` and fill `SUPABASE_URL`, `SUPABASE_ANON_KEY`.
Run SQL in `supabase/schema.sql` using Supabase SQL Editor to create tables/policies.

## 4. Run Application

```bash
cd .\flask_backend\
.\.venv\Scripts\Activate.ps1
npm run dev
```

Open: http://localhost:8000

## 5. Health Check

```bash
curl http://localhost:8000/health
```

## 6. Model Weights

Place `best_food101_model.pth`, `best_vit_vn30food_model.pth` into `ml_models/`. Inference service auto-discovers.

## 8. Remove Unused Packages (if previously installed)

```bash
pip uninstall -y tensorflow keras httpx
```

## 9. Key Structure

```
flask_backend/app/
  flask_app.py        # App factory + SSR routes
  routes/             # API endpoints
  services/           # Inference, nutrition, Supabase, templating
web/templates/pages/  # Page templates (.hbs)
web/templates/partials/ # Partials (header, footer, widgets)
web/assets/           # Logo, favicon, images
ml_models/            # PyTorch weights
data/                 # nutrition_database.csv
```

## 10. Troubleshooting

| Issue               | Solution                                        |
| ------------------- | ----------------------------------------------- |
| Model 404           | Ensure correct `.pth` filename in `ml_models/`  |
| Supabase auth error | Verify URL, keys, machine time sync             |
| Image not showing   | Check path `/app/assets/...` served from `web/` |
| QUIC timeout        | Disable QUIC or test in Firefox                 |

## 11. Performance

First prediction loads model into RAM; subsequent requests use cache. You can preload by calling `get_inference_service()` at startup.

## 12. Future Enhancements

- Multi-food detection (YOLO / DETR)
- Historical target & recommendations
- Mobile offline capture & sync
- Recipe macro parsing

Setup complete! 🎉
