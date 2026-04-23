#!/usr/bin/env bash
set -euo pipefail

echo "=== Copilot Usage Agent — Local Setup ==="

# Backend
echo ""
echo "[1/3] Setting up Python backend..."
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    cp .env.example .env
    echo "  Created .env from .env.example — edit it with your credentials."
else
    echo "  .env already exists, skipping."
fi

cd backend
if [ ! -d .venv ]; then
    python3 -m venv .venv
    echo "  Created virtual environment at backend/.venv"
fi
source .venv/bin/activate
pip install -q -r ../requirements.txt
echo "  Python dependencies installed."

# Frontend
echo ""
echo "[2/3] Setting up React frontend..."
cd ../frontend
npm install --silent
echo "  Node dependencies installed."

echo ""
echo "[3/3] Done!"
echo ""
echo "To start:"
echo "  Terminal 1:  cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8000"
echo "  Terminal 2:  cd frontend && npm run dev"
echo ""
echo "Then open http://localhost:5173"
