#!/bin/bash

echo "🔧 Setting up Job Bot on Linux Server"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script should be run as root or with sudo"
    echo "Run: sudo bash linux_setup.sh"
    exit 1
fi

echo "📦 Step 1: Installing Chrome/Chromium..."
echo ""

# Update package list
apt update

# Try to install chromium-browser (most common)
if apt install -y chromium-browser; then
    echo "✅ Chromium installed successfully"
elif apt install -y chromium; then
    echo "✅ Chromium installed successfully"
elif apt install -y google-chrome-stable; then
    echo "✅ Google Chrome installed successfully"
else
    echo "❌ Failed to install Chrome/Chromium automatically"
    echo ""
    echo "Please install manually:"
    echo "  Ubuntu/Debian: sudo apt install chromium-browser"
    echo "  Or download Chrome: wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
    echo "  Then: sudo dpkg -i google-chrome-stable_current_amd64.deb"
    exit 1
fi

echo ""
echo "🔍 Step 2: Verifying Chrome installation..."
echo ""

# Check if Chrome is installed
if command -v chromium-browser &> /dev/null; then
    CHROME_PATH=$(which chromium-browser)
    echo "✅ Found Chromium at: $CHROME_PATH"
    chromium-browser --version
elif command -v chromium &> /dev/null; then
    CHROME_PATH=$(which chromium)
    echo "✅ Found Chromium at: $CHROME_PATH"
    chromium --version
elif command -v google-chrome &> /dev/null; then
    CHROME_PATH=$(which google-chrome)
    echo "✅ Found Chrome at: $CHROME_PATH"
    google-chrome --version
else
    echo "❌ Chrome/Chromium not found in PATH"
    exit 1
fi

echo ""
echo "📚 Step 3: Installing Chrome dependencies..."
echo ""

# Install required libraries for Chrome
apt install -y \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libx11-xcb1

echo ""
echo "✅ Setup Complete!"
echo ""
echo "📋 Summary:"
echo "  ✅ Chrome/Chromium installed"
echo "  ✅ Dependencies installed"
echo "  ✅ Ready to run bot"
echo ""
echo "🚀 Next Steps:"
echo "  1. Activate your virtual environment"
echo "  2. Run: python main.py"
echo "  3. Bot will now be able to scrape jobs!"
echo ""
echo "📝 Test scraping with: python test_scraping.py"
echo ""
