#!/bin/bash

# Emperor AI Assistant - Development Script
# Starts both Python backend and Tauri frontend

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}Starting Emperor AI Assistant...${NC}"

# Track background process
BACKEND_PID=""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"

    if [ -n "$BACKEND_PID" ]; then
        echo -e "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
        wait $BACKEND_PID 2>/dev/null || true
    fi

    echo -e "${GREEN}Goodbye!${NC}"
    exit 0
}

# Set trap for cleanup on Ctrl+C and termination
trap cleanup SIGINT SIGTERM

# Start Python backend
start_backend() {
    echo -e "${YELLOW}Starting Python backend...${NC}"

    cd "$PROJECT_ROOT/backend"

    # Check if venv exists
    if [ ! -d "venv" ]; then
        echo -e "${RED}Error: Virtual environment not found!${NC}"
        echo "Create it with: cd backend && python3 -m venv venv"
        exit 1
    fi

    # Activate venv and start server
    source venv/bin/activate
    python -m api.main &
    BACKEND_PID=$!

    cd "$PROJECT_ROOT"

    # Wait for backend to be ready with health check
    echo -e "Waiting for backend to start..."

    MAX_WAIT=30
    WAITED=0

    while [ $WAITED -lt $MAX_WAIT ]; do
        # Check if process is still running
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            echo -e "${RED}Error: Backend process died!${NC}"
            exit 1
        fi

        # Try health check
        if curl -s http://127.0.0.1:8765/health > /dev/null 2>&1; then
            echo -e "${GREEN}Backend running on http://127.0.0.1:8765${NC}"
            break
        fi

        sleep 1
        WAITED=$((WAITED + 1))
        echo -e "  Waiting... ($WAITED/$MAX_WAIT)"
    done

    if [ $WAITED -ge $MAX_WAIT ]; then
        echo -e "${RED}Error: Backend failed to start within ${MAX_WAIT}s!${NC}"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
}

# Start Tauri frontend
start_frontend() {
    echo -e "${YELLOW}Starting Tauri frontend...${NC}"

    cd "$PROJECT_ROOT"
    pnpm tauri dev
}

# Main
start_backend
start_frontend

# If frontend exits, cleanup
cleanup
