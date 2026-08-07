#!/usr/bin/env bash
# =============================================================================
# DevAgency Setup Script
# One-command installation for Kali Linux environments.
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "  ╔═══════════════════════════════════════════════════════════════╗"
echo "  ║           DevAgency — Vibe Coding Orchestrator              ║"
echo "  ║              Setup & Installation Script                      ║"
echo "  ╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Check Python version ─────────────────────────────────────────────────────
PYTHON_VERSION=$(python3 --version 2>/dev/null | awk '{print $2}' | cut -d. -f1,2)
REQUIRED="3.10"
if [ "$(printf '%s\n' "$REQUIRED" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED" ]; then
    echo -e "${RED}[ERROR] Python 3.10+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Python $PYTHON_VERSION detected"

# ── Check Ollama ────────────────────────────────────────────────────────────
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}[WARN] Ollama not found.${NC}"
    echo "       Install: curl -fsSL https://ollama.com/install.sh | sh"
else
    echo -e "${GREEN}[OK]${NC} Ollama detected"
fi

# ── Check mpv ───────────────────────────────────────────────────────────────
if ! command -v mpv &> /dev/null; then
    echo -e "${YELLOW}[WARN] mpv not found.${NC} Install: sudo apt install mpv"
else
    echo -e "${GREEN}[OK]${NC} mpv detected"
fi

# ── Create virtual environment ────────────────────────────────────────────────
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}[INFO]${NC} Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# ── Install dependencies ────────────────────────────────────────────────────
echo -e "${BLUE}[INFO]${NC} Installing Python dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -r requirements.txt -q

# ── Create .env if not exists ───────────────────────────────────────────────
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[WARN]${NC} Creating .env from template..."
    cp .env.example .env
    echo -e "${YELLOW}[ACTION REQUIRED]${NC} Edit .env with your API keys before running!"
fi

# ── Initialize database directory ─────────────────────────────────────────────
mkdir -p "$HOME/.devagency"

# ── Pull recommended Ollama models ──────────────────────────────────────────
echo -e "${BLUE}[INFO]${NC} Checking Ollama models..."
MODELS=(
    "llama3:8b"
    "granite-code:8b"
    "deepseek-coder-v2:lite"
    "hermes3:latest"
    "target-analyst:latest"
    "auditor-8b:latest"
    "mxbai-embed-large:latest"
)

for model in "${MODELS[@]}"; do
    if ollama list 2>/dev/null | grep -q "$model"; then
        echo -e "  ${GREEN}[OK]${NC} $model"
    else
        echo -e "  ${BLUE}[PULL]${NC} $model..."
        ollama pull "$model" 2>/dev/null || echo -e "  ${YELLOW}[SKIP]${NC} $model (will retry on first use)"
    fi
done

# ── Done ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Activate:  source venv/bin/activate"
echo "  Task:      python -m hermes.main task 'Build a FastAPI app #vibe'"
echo "  List:      python -m hermes.main list"
echo "  Vibes:     python -m hermes.main vibes on"
echo ""
