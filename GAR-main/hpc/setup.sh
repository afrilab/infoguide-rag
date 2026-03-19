#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"

module load python 2>/dev/null || true
if ! command -v python3 &>/dev/null; then
    echo "python3 not found. Run: module load python"
    exit 1
fi

if [ -d "venv" ]; then
    echo "venv exists, skipping creation"
else
    echo "Creating venv..."
    python3 -m venv venv
fi
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo "Done. Activate: source venv/bin/activate"
