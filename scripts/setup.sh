#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Setting up .agents..."

# 1. Install Homebrew if it isn't installed
if ! command -v brew &> /dev/null; then
    echo "🍺 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 2. Install dependencies from the Brewfile
echo "📦 Installing from Brewfile..."
# Use absolute path to Brewfile to ensure it works regardless of CWD
BREWFILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/Brewfile"
NONINTERACTIVE=1 brew bundle --verbose --file="$BREWFILE"

echo "✅ .agents setup complete!"
