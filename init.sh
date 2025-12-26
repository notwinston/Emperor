#!/bin/bash

# Emperor AI Assistant - Development Environment Setup
# For agents and developers to bootstrap the project

set -e

echo "========================================"
echo "  Emperor AI Assistant - Dev Setup"
echo "========================================"

# Colors
GOLD='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${GOLD}Checking prerequisites...${NC}"

if ! command -v node &> /dev/null; then
    echo "Node.js is required but not installed."
    exit 1
fi

if ! command -v pnpm &> /dev/null; then
    echo "pnpm is required but not installed. Installing..."
    npm install -g pnpm
fi

if ! command -v rustc &> /dev/null; then
    echo "Rust is required but not installed. Visit https://rustup.rs"
    exit 1
fi

echo -e "${GREEN}Prerequisites OK${NC}"

# Install frontend dependencies
echo -e "${GOLD}Installing frontend dependencies...${NC}"
pnpm install

# Check Tauri CLI
echo -e "${GOLD}Checking Tauri CLI...${NC}"
if ! pnpm tauri --version &> /dev/null; then
    echo "Installing Tauri CLI..."
    pnpm add -D @tauri-apps/cli
fi

echo -e "${GREEN}Dependencies installed${NC}"

# Print development instructions
echo ""
echo "========================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================"
echo ""
echo "To start development:"
echo "  pnpm tauri dev"
echo ""
echo "To build for production:"
echo "  pnpm tauri build"
echo ""
echo "Frontend dev server: http://localhost:1420"
echo ""
echo "Project Structure:"
echo "  src/           - React frontend"
echo "  src-tauri/     - Tauri/Rust backend"
echo "  backend/       - Python backend (future)"
echo ""
