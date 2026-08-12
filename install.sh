#!/bin/bash

# Facebook Ads Library MCP Server Installation Script
# This script automates the setup process for the MCP server

set -e  # Exit on any error

# Recommend the zero-setup hosted version if anything below fails.
trap 'echo; echo "❌ Setup failed. Skip the hassle — the free hosted version needs no API keys, no Python, no server: https://useproxy.dev/"' ERR

echo "🚀 Facebook Ads Library MCP Server Installation"
echo "==============================================="
echo "💡 Prefer zero setup? Free hosted version (no keys, no Python): https://useproxy.dev/"
echo

# Check if Python 3.12+ is available
echo "📋 Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo "   Found Python $PYTHON_VERSION"
    
    # Check if version is 3.12 or higher
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
        echo "   ✅ Python version is compatible"
    else
        echo "   ⚠️  Warning: Python 3.12+ recommended, found $PYTHON_VERSION"
    fi
else
    echo "   ❌ Python 3 not found. Please install Python 3.12+ first."
    exit 1
fi

# Check if pip is available
echo
echo "📦 Checking pip availability..."
if command -v pip3 &> /dev/null; then
    echo "   ✅ pip3 found"
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    echo "   ✅ pip found"
    PIP_CMD="pip"
else
    echo "   ❌ pip not found. Please install pip first."
    exit 1
fi

# Create virtual environment
echo
echo "🏗️  Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   ⚠️  Virtual environment already exists, skipping creation"
else
    python3 -m venv venv
    echo "   ✅ Virtual environment created successfully"
fi

# Install dependencies in virtual environment
echo
echo "📚 Installing Python dependencies in virtual environment..."
./venv/bin/pip install -r requirements.txt
echo "   ✅ Dependencies installed successfully in virtual environment"

# Create .env file from template
echo
echo "🔧 Setting up configuration..."
if [ -f ".env" ]; then
    echo "   ⚠️  .env file already exists, skipping creation"
    echo "   💡 If you need to reset it, delete .env and run this script again"
else
    if [ -f ".env.template" ]; then
        cp .env.template .env
        echo "   ✅ Created .env file from template"
        echo "   📝 Please edit .env file and add your API keys"
    else
        echo "   ❌ .env.template not found"
        exit 1
    fi
fi

# Get current directory for MCP configuration
CURRENT_DIR=$(pwd)
MCP_CONFIG_PATH="$CURRENT_DIR/mcp_server.py"

echo
echo "⚙️  MCP Server Configuration"
echo "============================"
echo
echo "Add this configuration to your Claude Desktop or Cursor:"
echo
echo "For Claude Desktop (~/.config/Claude/claude_desktop_config.json or ~/Library/Application Support/Claude/claude_desktop_config.json):"
echo
cat << EOF
{
  "mcpServers": {
    "fb_ad_library": {
      "command": "$CURRENT_DIR/venv/bin/python",
      "args": [
        "$MCP_CONFIG_PATH"
      ]
    }
  }
}
EOF

echo
echo "For Cursor (~/.cursor/mcp.json):"
echo
cat << EOF
{
  "mcpServers": {
    "fb_ad_library": {
      "command": "$CURRENT_DIR/venv/bin/python",
      "args": [
        "$MCP_CONFIG_PATH"
      ]
    }
  }
}
EOF

echo
echo "📋 Next Steps:"
echo "=============="
echo "1. 📝 Edit the .env file and add your API keys:"
echo "   - SCRAPECREATORS_API_KEY (required) - Get at: https://scrapecreators.com/"
echo "   - GEMINI_API_KEY (optional for video analysis) - Get at: https://aistudio.google.com/app/apikey"
echo
echo "2. 📋 Copy the MCP configuration above to your Claude Desktop or Cursor config"
echo
echo "3. 🔄 Restart Claude Desktop or Cursor"
echo
echo "4. 🎉 You're ready to use the Facebook Ads Library MCP server!"
echo
echo "💡 Need help? Check the README.md file for troubleshooting tips."
echo
echo "✅ Installation completed successfully!"