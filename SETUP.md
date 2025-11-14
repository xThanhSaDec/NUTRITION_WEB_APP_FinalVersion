# 🚀 Quick Setup Guide

## Prerequisites

- Python 3.8 or higher
- pip package manager
- At least 4GB RAM for ML model

## 📥 Installation Steps

### Step 1: Install Backend Dependencies

```bash
cd backend
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 python-multipart==0.0.6 pydantic==2.5.0 tensorflow==2.13.0 pillow==10.1.0 numpy==1.24.3 pandas==2.1.4
```

### Step 2: Install Frontend Dependencies

```bash
cd frontend
pip install streamlit>=1.28.0 requests>=2.31.0 pillow>=10.1.0 pandas>=2.1.4
```

## ▶️ Running the Application

### Option 1: Use Batch Files (Windows)

1. Double-click `start_backend.bat` to start the backend server
2. Double-click `start_frontend.bat` to start the frontend application

### Option 2: Manual Start

**Terminal 1 - Backend:**

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**

```bash
cd frontend
streamlit run streamlit_app.py --server.port 8501
```

## 🌐 Access Points

- **Frontend Application**: http://localhost:8501
- **Backend API**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs
- **API Health Check**: http://127.0.0.1:8000/health

## 🧪 Testing the Application

### 1. Test Backend API

```bash
curl http://127.0.0.1:8000/health
```

### 2. Test Nutrition Endpoint

```bash
curl http://127.0.0.1:8000/api/nutrition/pho_bo
```

### 3. Test Frontend

1. Open http://localhost:8501
2. Navigate to "Predict" page
3. Upload a food image
4. Check results

## 🐳 Docker Deployment (Alternative)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access applications:
# Frontend: http://localhost:8501
# Backend: http://localhost:8000
```

## 📝 Usage Instructions

1. **Start Backend**: Ensure backend server is running on port 8000
2. **Start Frontend**: Launch Streamlit app on port 8501
3. **Upload Image**: Go to Predict page and upload food image
4. **View Results**: Get food identification and nutrition information
5. **Explore**: Check About Us page for team information

## ⚠️ Troubleshooting

### Common Issues:

- **Port conflicts**: Make sure ports 8000 and 8501 are available
- **Model loading**: First prediction may take time for model loading
- **Dependencies**: Install all requirements exactly as specified
- **Python version**: Use Python 3.8+ for compatibility

### Performance Notes:

- First prediction: ~10-15 seconds (model loading)
- Subsequent predictions: ~2-3 seconds
- Memory usage: ~2-4GB during operation
