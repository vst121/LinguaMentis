#!/usr/bin/env bash
set -euo pipefail

SKIP_SYNC=false
for arg in "$@"; do
  case "$arg" in
    --skip-sync|-s)
      SKIP_SYNC=true
      ;;
    --help|-h)
      echo "Usage: ./start.sh [--skip-sync]"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 1
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
ENV_FILE="$BACKEND_DIR/.env"
ENV_EXAMPLE_FILE="$BACKEND_DIR/.env.example"

# Ensure uv is discoverable if installed in the default user bin directory
if [ -d "$HOME/.local/bin" ] && [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
  export PATH="$HOME/.local/bin:$PATH"
fi

log_step() {
  printf "\n==> %s\n" "$1"
}

stop_process_tree() {
  local pid="$1"
  if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
    return
  fi
  if command -v pgrep >/dev/null 2>&1; then
    local children
    children="$(pgrep -P "$pid" 2>/dev/null || true)"
    for child in $children; do
      stop_process_tree "$child"
    done
  fi
  kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
}

wait_for_postgres() {
  echo "Waiting for PostgreSQL to accept connections..."
  for _ in $(seq 1 30); do
    if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U linguamentis -d linguamentis >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "Error: PostgreSQL did not become ready on port 5438 in time." >&2
  exit 1
}

log_step "Checking required tools..."
for tool in docker uv node; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Error: Required tool '$tool' was not found in PATH." >&2
    exit 1
  fi
done

if command -v pnpm >/dev/null 2>&1; then
  PKG_MANAGER="pnpm"
elif command -v npm >/dev/null 2>&1; then
  PKG_MANAGER="npm"
else
  echo "Error: Neither 'pnpm' nor 'npm' was found in PATH." >&2
  exit 1
fi

log_step "Checking backend environment configuration (.env)..."
if [ ! -f "$ENV_FILE" ]; then
  if [ -f "$ENV_EXAMPLE_FILE" ]; then
    cp "$ENV_EXAMPLE_FILE" "$ENV_FILE"
    echo "Warning: Created backend/.env from .env.example. Set GEMINI_API_KEY before using AI features."
  else
    echo "Error: Neither backend/.env nor backend/.env.example was found." >&2
    exit 1
  fi
fi

if ! grep -Eq '^\s*GEMINI_API_KEY=.+' "$ENV_FILE" || grep -Eq '^\s*GEMINI_API_KEY=your-gemini-api-key' "$ENV_FILE"; then
  echo "Warning: GEMINI_API_KEY does not appear to be configured in backend/.env."
fi

log_step "Checking Docker daemon..."
if ! docker info >/dev/null 2>&1; then
  echo "Error: Docker is not running. Start Docker and try again." >&2
  exit 1
fi

log_step "Starting PostgreSQL container..."
docker compose -f "$COMPOSE_FILE" up -d postgres
wait_for_postgres

if [ "$SKIP_SYNC" = false ]; then
  log_step "Syncing backend dependencies (uv sync --all-extras)..."
  (cd "$BACKEND_DIR" && uv sync --all-extras)
fi

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  log_step "Installing frontend dependencies ($PKG_MANAGER install)..."
  (cd "$FRONTEND_DIR" && "$PKG_MANAGER" install)
fi

BACKEND_PID=""
FRONTEND_PID=""

start_backend() {
  (cd "$BACKEND_DIR" && exec uv run python -m uvicorn linguamentis.main:app --reload --host 127.0.0.1 --port 8000) &
  BACKEND_PID=$!
}

start_frontend() {
  # Remove production build output if present so next dev does not mix manifests with vendor-chunks
  if [ -f "$FRONTEND_DIR/.next/BUILD_ID" ]; then
    rm -rf "$FRONTEND_DIR/.next"
  fi
  (cd "$FRONTEND_DIR" && exec "$PKG_MANAGER" run dev) &
  FRONTEND_PID=$!
}

print_help() {
  printf "\nAvailable runtime commands (type command + Enter):\n"
  printf "  r  | restart  - Restart both Backend and Frontend\n"
  printf "  rb | backend  - Restart Backend only\n"
  printf "  rf | frontend - Restart Frontend only\n"
  printf "  db            - Restart PostgreSQL container\n"
  printf "  s  | status   - Show process status and URLs\n"
  printf "  h  | help     - Show this help\n"
  printf "  q  | quit     - Stop Backend and Frontend and exit (or press Ctrl+C)\n\n"
}

print_status() {
  local b_state="STOPPED"
  local f_state="STOPPED"
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    b_state="RUNNING (PID $BACKEND_PID)"
  fi
  if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    f_state="RUNNING (PID $FRONTEND_PID)"
  fi
  printf "\nService status:\n"
  printf "  - Backend:  %s -> http://127.0.0.1:8000/health\n" "$b_state"
  printf "  - Frontend: %s -> http://localhost:3000\n" "$f_state"
  printf "  - API Docs: http://127.0.0.1:8000/docs\n\n"
}

cleanup() {
  printf "\nStopping Backend and Frontend...\n"
  stop_process_tree "${FRONTEND_PID:-}"
  stop_process_tree "${BACKEND_PID:-}"
  printf "Services stopped (PostgreSQL remains running in Docker).\n"
}

trap cleanup EXIT INT TERM

log_step "Starting Backend (FastAPI) and Frontend (Next.js)..."
start_backend
start_frontend

printf "\nLinguaMentis is running:\n"
printf "  - Frontend: http://localhost:3000\n"
printf "  - Backend:  http://127.0.0.1:8000/health\n"
printf "  - API Docs: http://127.0.0.1:8000/docs\n"
print_help

BACKEND_WARNED=false
FRONTEND_WARNED=false

while true; do
  if [ -n "$BACKEND_PID" ] && ! kill -0 "$BACKEND_PID" 2>/dev/null && [ "$BACKEND_WARNED" = false ]; then
    echo "Warning: Backend process exited unexpectedly. Type 'rb' or 'r' to restart, or 'q' to quit."
    BACKEND_WARNED=true
    if [ ! -t 0 ]; then
      break
    fi
  fi

  if [ -n "$FRONTEND_PID" ] && ! kill -0 "$FRONTEND_PID" 2>/dev/null && [ "$FRONTEND_WARNED" = false ]; then
    echo "Warning: Frontend process exited unexpectedly. Type 'rf' or 'r' to restart, or 'q' to quit."
    FRONTEND_WARNED=true
    if [ ! -t 0 ]; then
      break
    fi
  fi

  if [ -t 0 ]; then
    cmd=""
    if read -r -t 0.5 cmd; then
      cmd="$(echo "$cmd" | tr '[:upper:]' '[:lower:]' | xargs)"
      case "$cmd" in
        r|restart)
          log_step "Restarting Backend and Frontend..."
          stop_process_tree "$FRONTEND_PID"
          stop_process_tree "$BACKEND_PID"
          start_backend
          start_frontend
          BACKEND_WARNED=false
          FRONTEND_WARNED=false
          echo "Backend and Frontend restarted."
          ;;
        rb|backend)
          log_step "Restarting Backend..."
          stop_process_tree "$BACKEND_PID"
          start_backend
          BACKEND_WARNED=false
          echo "Backend restarted."
          ;;
        rf|frontend)
          log_step "Restarting Frontend..."
          stop_process_tree "$FRONTEND_PID"
          start_frontend
          FRONTEND_WARNED=false
          echo "Frontend restarted."
          ;;
        db)
          log_step "Restarting PostgreSQL container..."
          docker compose -f "$COMPOSE_FILE" restart postgres
          wait_for_postgres
          echo "PostgreSQL is ready."
          ;;
        s|status)
          print_status
          ;;
        h|help)
          print_help
          ;;
        q|quit|exit)
          break
          ;;
        "")
          ;;
        *)
          echo "Unknown command '$cmd'. Type 'h' for help."
          ;;
      esac
    fi
  else
    sleep 0.5
  fi
done
