#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

if [ ! -d "$BACKEND_DIR" ] || [ ! -d "$FRONTEND_DIR" ]; then
  echo "未找到 backend 或 frontend 目录。"
  exit 1
fi

cleanup() {
  local exit_code=$?
  trap - INT TERM EXIT

  if [ -n "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  if [ -n "${FRONTEND_PID:-}" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi

  wait 2>/dev/null || true
  exit "$exit_code"
}

trap cleanup INT TERM EXIT

if [ -x "$BACKEND_DIR/.venv/Scripts/python.exe" ]; then
  BACKEND_PYTHON="$BACKEND_DIR/.venv/Scripts/python.exe"
elif command -v python >/dev/null 2>&1; then
  BACKEND_PYTHON="python"
elif command -v python3 >/dev/null 2>&1; then
  BACKEND_PYTHON="python3"
else
  echo "未找到 Python，请先安装 Python 3.10+。"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "未找到 npm，请先安装 Node.js 18+。"
  exit 1
fi

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo "frontend/node_modules 不存在，请先在 frontend 目录执行 npm install。"
  exit 1
fi

if [ ! -f "$BACKEND_DIR/.env" ] && [ -f "$BACKEND_DIR/env.example" ]; then
  echo "提示：backend/.env 不存在，可参考 backend/env.example 创建。"
fi

echo "启动后端开发服务..."
(
  cd "$BACKEND_DIR"
  exec "$BACKEND_PYTHON" -m uvicorn app.main:app --reload
) &
BACKEND_PID=$!

echo "启动前端开发服务..."
(
  cd "$FRONTEND_DIR"
  exec npm run dev
) &
FRONTEND_PID=$!

echo ""
echo "开发环境已启动："
echo "- 后端: http://127.0.0.1:8000"
echo "- 前端: http://127.0.0.1:5173"
echo "按 Ctrl+C 可同时停止前后端。"
echo ""

wait -n "$BACKEND_PID" "$FRONTEND_PID"
