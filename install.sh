#!/bin/bash
# ClauseCompare Linux Installer
# Run with: chmod +x install.sh && ./install.sh

cd "$(dirname "$0")"
LOG_FILE="install.log"
exec > "$LOG_FILE" 2>&1

echo "🔍 Detecting package manager..."
if command -v apt &> /dev/null; then
    echo "📦 Using apt (Debian/Ubuntu)..."
    sudo apt update >> "$LOG_FILE" 2>&1
    sudo apt install -y python3 python3-venv python3-pip >> "$LOG_FILE" 2>&1
elif command -v dnf &> /dev/null; then
    echo "📦 Using dnf (Fedora/RHEL)..."
    sudo dnf install -y python3 python3-virtualenv python3-pip >> "$LOG_FILE" 2>&1
elif command -v yum &> /dev/null; then
    echo "📦 Using yum (CentOS/Older)..."
    sudo yum install -y python3 python3-virtualenv python3-pip >> "$LOG_FILE" 2>&1
else
    echo "❌ Unsupported package manager. Please install Python 3.11+ manually."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 still not available. Please install manually."
    exit 1
fi
echo "✅ Python3 installed."

echo "🔧 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv >> "$LOG_FILE" 2>&1
    echo "✅ Virtual environment created."
else
    echo "✅ Virtual environment already exists."
fi

echo "📦 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip >> "$LOG_FILE" 2>&1
pip install -r requirements.txt >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies."
    exit 1
fi
echo "✅ Dependencies installed."

echo "📝 Creating launcher script..."
cat > run_clausecompare.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
LOG_FILE="clausecompare.log"
exec > "$LOG_FILE" 2>&1
PORT=8501
if ss -tuln | grep -q ":$PORT "; then
    echo "✅ ClauseCompare is already running. Opening browser..."
    xdg-open "http://localhost:$PORT"
    exit 0
fi
source venv/bin/activate
echo "🚀 Starting ClauseCompare..."
streamlit run app.py --server.port $PORT --server.headless false &
sleep 3
xdg-open "http://localhost:$PORT"
wait
EOF

chmod +x run_clausecompare.sh
echo "✅ Launcher created: run_clausecompare.sh"

echo ""
echo "🎉 Setup complete!"
echo "👉 Run './run_clausecompare.sh' to start the app."
echo "   (Ollama must be installed and running separately.)"