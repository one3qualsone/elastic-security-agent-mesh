#!/bin/bash
# =============================================================================
# Elastic Security Agent Mesh — Setup Script (Bash)
#
# Thin wrapper that validates prerequisites and runs the Python setup script.
# For the full setup logic, see setup.py.
#
# Set required environment variables before running (see README.md):
#   export ELASTIC_CLOUD_URL=...
#   export KIBANA_URL=...
#   export ES_API_KEY=...
#   export KIBANA_API_KEY=...
#
# Usage:
#   ./scripts/setup.sh              # Full setup
#   ./scripts/setup.sh --validate   # Validate env vars only
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo ""
echo "Elastic Security Agent Mesh — Setup"
echo "===================================="
echo ""

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 is required but not found.${NC}"
    echo "Install Python 3.8+ and try again."
    exit 1
fi

if ! python3 -c "import requests" 2>/dev/null; then
    echo "Installing required Python package: requests"
    pip3 install requests
    echo ""
fi

echo -e "${GREEN}Running setup...${NC}"
echo ""

python3 "$SCRIPT_DIR/setup.py" "$@"
