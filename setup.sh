#!/bin/bash
# Hermes Coder Assistant - Setup Script
# Quick install for local development

set -e

echo "🚀 Setting up Hermes Coder Assistant..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)

if [ "$PYTHON_MAJOR" -lt 3 ]; then
    echo "❌ Python 3.10+ required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version OK: $PYTHON_VERSION"

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if not exists
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file..."
    cat > .env << 'EOF'
# GitHub Token (optional in production, required for full features)
# GITHUB_TOKEN=your_github_token_here

# Hugging Face Token (for model downloads)
# HF_TOKEN=your_hf_token_here
EOF
    echo "✅ Created .env file"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the app:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "Then open http://localhost:7860 in your browser"
