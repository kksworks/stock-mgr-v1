#!/usr/bin/env bash
# Frontend + Backend 동시 실행 및 환경 관리 스크립트
set -e
cd "$(dirname "$0")"
cd .. # scripts/ -> root/
export PYTHONPATH=$PYTHONPATH:.

# --- Helper Functions ---
show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "A script to manage and run the development environment."
    echo ""
    echo "Commands:"
    echo "  start       (default) Starts the backend and frontend servers."
    echo "  install     Sets up the environment and installs all dependencies (Python & Node.js)."
    echo "  update      Updates all dependencies."
    echo "  reset-venv  Removes and recreates the Python virtual environment, then installs dependencies."
    echo "  update-docker Run start-docker.sh update"
    echo "  deploy      Run start-docker.sh deploy"
    echo "  help        Shows this help message."
    echo "  --debug     Enable DEBUG level logs and Flask debug mode."
    echo "  --force     Skip confirmation prompts (for CI/CD)."
    echo ""
    echo "Example:"
    echo "  ./scripts/start.sh --debug"
    echo ""
}

# --- Command Definitions ---
cmd_install() {
  echo ">>> 1. Setting up Python backend environment..."
  if [ ! -d "venv" ]; then
    echo "  -> Creating Python virtual environment 'venv'..."
    python3 -m venv venv
  else
    echo "  -> Python virtual environment 'venv' already exists."
  fi
  echo "  -> Installing/updating Python dependencies from requirements.txt..."
  ./venv/bin/pip install -r requirements.txt
  echo ">>> Backend setup complete."

  echo ""
  echo ">>> 2. Setting up Node.js frontend environment..."
  if [ -d "frontend" ]; then
    (
      cd frontend
      echo "  -> Installing Node.js dependencies (npm install)..."
      npm install
    )
    echo ">>> Frontend setup complete."
  else
    echo "!!! 'frontend' directory not found."
  fi
  echo ""
  echo ">>> Installation finished. You can now run './scripts/start.sh' to start the servers."
}

cmd_update() {
    echo ">>> 1. Updating Python backend dependencies..."
    if [ ! -f "venv/bin/pip" ]; then
        echo "!!! Python virtual environment not found. Please run './start.sh install' first."
        exit 1
    fi
    ./venv/bin/pip install --upgrade -r requirements.txt
    echo ">>> Backend dependencies updated."

    echo ""
    echo ">>> 2. Updating Node.js frontend dependencies..."
    if [ -d "frontend/node_modules" ]; then
        (
            cd frontend
            echo "  -> Updating Node.js dependencies (npm update)..."
            npm update
        )
        echo ">>> Frontend dependencies updated."
    else
        echo "!!! 'frontend/node_modules' not found. Please run './start.sh install' first."
    fi
    echo ""
    echo ">>> Update finished."
}

cmd_reset_venv() {
    echo ">>> Resetting Python virtual environment..."
    if [ -d "venv" ]; then
        if [ "${AUTO_YES:-0}" -eq 1 ]; then
            echo "  -> Force removing 'venv' directory..."
        else
            read -p "  -> Are you sure you want to remove the 'venv' directory? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "  -> Reset cancelled."
                exit 0
            fi
        fi
        rm -rf venv
        echo "  -> 'venv' directory removed."
    else
        echo "  -> 'venv' directory not found. It will be created."
    fi

    echo ">>> Creating new Python virtual environment and installing dependencies..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
    echo ">>> Backend environment has been reset and set up."
}

cmd_start() {
  # Check for dependencies before starting
  if [ ! -f "venv/bin/python3" ]; then
    echo "!!! Python virtual environment 'venv' not found."
    echo "!!! Please run './start.sh install' to set up the environment."
    exit 1
  fi
  if [ ! -d "frontend/node_modules" ]; then
    echo "!!! Frontend dependencies ('node_modules') not found."
    echo "!!! Please run './start.sh install' to set up the environment."
    exit 1
  fi

  BACKEND_PID=""
  cleanup() {
    echo -e "\n>>> Shutting down..."
    if [[ -n "$BACKEND_PID" ]]; then
      kill "$BACKEND_PID" 2>/dev/null || true
      echo ">>> Backend server stopped."
    fi
    exit 0
  }
  trap cleanup SIGINT SIGTERM

  echo ">>> Backend (Flask) starting in background on http://localhost:5000"
  export PORT=8080
  ./venv/bin/python3 backend/run_backend.py &
  BACKEND_PID=$!
  sleep 2

  echo ">>> Frontend (Vue) starting on http://localhost:8080"
  (cd frontend && npm run dev)

  cleanup
}

# --- Main script logic ---

COMMAND=""
export FLASK_DEBUG=0
export LOG_LEVEL=INFO

for arg in "$@"; do
  case $arg in
    --debug)
      export FLASK_DEBUG=1
      export LOG_LEVEL=DEBUG
      ;;
    --force)
      export AUTO_YES=1
      ;;
    *)
      if [ -z "$COMMAND" ]; then
        COMMAND=$arg
      fi
      ;;
  esac
done

# Default command
if [ -z "$COMMAND" ]; then
  COMMAND="start"
fi

if [ "$LOG_LEVEL" == "DEBUG" ]; then
  echo ">>> [DEBUG MODE] LogLevel=DEBUG, FlaskDebug=1"
fi

case "$COMMAND" in
  start)
    cmd_start
    ;;
  install)
    cmd_install
    ;;
  update)
    cmd_update
    ;;
  reset-venv)
    cmd_reset_venv
    ;;
  update-docker)
    ./scripts/start-docker.sh update
    ;;
  deploy)
    ./scripts/start-docker.sh deploy
    ;;
  help|--help|-h)
    show_help
    ;;
  *)
    echo "!!! Unknown command: '$COMMAND'"
    show_help
    exit 1
    ;;
esac
