#!/bin/bash

# Emperor AI Assistant - User Setup Script
# Run this script to set up and launch the Emperor application

set -e

echo ""
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║                                           ║"
echo "  ║     👑  EMPEROR AI ASSISTANT  👑          ║"
echo "  ║                                           ║"
echo "  ║         Premium AI Experience             ║"
echo "  ║                                           ║"
echo "  ╚═══════════════════════════════════════════╝"
echo ""

# Colors
GOLD='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is required.${NC}"
    echo "Please install Node.js from https://nodejs.org"
    exit 1
fi

# Check for pnpm
if ! command -v pnpm &> /dev/null; then
    echo -e "${GOLD}Installing pnpm...${NC}"
    npm install -g pnpm
fi

# Check for Rust
if ! command -v rustc &> /dev/null; then
    echo -e "${RED}Error: Rust is required for Tauri.${NC}"
    echo "Please install Rust from https://rustup.rs"
    exit 1
fi

echo -e "${GOLD}Installing dependencies...${NC}"
pnpm install

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "To launch Emperor:"
echo -e "  ${GOLD}pnpm tauri dev${NC}     - Development mode"
echo -e "  ${GOLD}pnpm tauri build${NC}   - Build for production"
echo ""
echo "Enjoy your premium AI experience! 👑"
echo ""
