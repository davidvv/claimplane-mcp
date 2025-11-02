#!/bin/bash

# EasyAirClaim Portal Setup Script
# This script helps you get started quickly

set -e

echo "🛫 EasyAirClaim Portal Setup"
echo "=============================="
echo ""

# Check Node.js version
echo "📦 Checking Node.js version..."
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Error: Node.js 18+ is required (you have $(node -v))"
    exit 1
fi
echo "✅ Node.js version OK"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm install
echo "✅ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API credentials:"
    echo "   - VITE_API_BASE_URL"
    echo "   - VITE_API_KEY"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Check if .env has been configured
if grep -q "your_api_key_here" .env; then
    echo "⚠️  WARNING: .env still has placeholder values"
    echo "   Please edit .env and add your real API credentials"
    echo ""
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API credentials"
echo "  2. Run: npm run dev"
echo "  3. Open: http://localhost:3000"
echo ""
echo "📚 Documentation:"
echo "  - QUICKSTART.md  - Quick start guide"
echo "  - README.md      - Full documentation"
echo "  - DEPLOYMENT.md  - Deployment guide"
echo ""
echo "🚀 Happy coding!"
