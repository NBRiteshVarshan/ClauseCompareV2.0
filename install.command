#!/bin/bash
# ClauseCompare macOS Installer
# Double‑click this file to set up the app.

cd "$(dirname "$0")"
LOG_FILE="install.log"
exec > "$LOG_FILE" 2>&1

echo "🔍 Checking for Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "🍺 Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
    echo "✅ Homebrew installed."
else
    echo "✅ Homebrew already installed."
fi

echo "🐍 Installing Python 3.12..."
brew install python@3.12
brew link --overwrite python@3.12
echo "✅ Python 3.12 installed."

echo "🔧 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created."
else
    echo "✅ Virtual environment already exists."
fi

echo "📦 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies."
    exit 1
fi
echo "✅ Dependencies installed."

echo "📝 Creating launcher script..."
cat > run_clausecompare.command << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
LOG_FILE="clausecompare.log"
exec > "$LOG_FILE" 2>&1
PORT=8501
if lsof -i :$PORT > /dev/null 2>&1; then
    echo "✅ ClauseCompare is already running. Opening browser..."
    open "http://localhost:$PORT"
    exit 0
fi
source venv/bin/activate
echo "🚀 Starting ClauseCompare..."
streamlit run app.py --server.port $PORT --server.headless false &
sleep 3
open "http://localhost:$PORT"
wait
EOF

chmod +x run_clausecompare.command
echo "✅ Launcher created: run_clausecompare.command"

echo ""
echo "🎉 Setup complete!"
echo "👉 Double‑click 'run_clausecompare.command' to start the app."
echo "   (Ollama must be installed and running separately.)"