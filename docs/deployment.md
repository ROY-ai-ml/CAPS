# Deployment Guide

## 1. Local Development Mode (Zero Docker Dependency)

ReRun is designed to be runnable immediately on developer workstations:

### Prerequisites:
- Python 3.10+
- Node.js 18+

### Setup:
```bash
# 1. Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# 2. Run Backend
uvicorn backend.app.main:app --reload --port 8000

# 3. In another terminal, run Frontend
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 2. Production Deployment via Docker Compose

```bash
# Build sandbox image
docker build -t rerun-sandbox:latest ./sandbox

# Launch full stack (Postgres + Backend + Frontend)
docker-compose up --build -d
```

Frontend available at `http://localhost:3000`.
FastAPI documentation available at `http://localhost:8000/docs`.
PostgreSQL available at `localhost:5432`.
