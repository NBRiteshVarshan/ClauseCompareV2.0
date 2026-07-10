import subprocess
import sys
import webbrowser
import time
import os

if __name__ == "__main__":
    # Start Streamlit with no terminal output
    streamlit_cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.headless", "true",
        "--server.port", "8501"
    ]
    
    # Launch Streamlit in the background
    proc = subprocess.Popen(
        streamlit_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "PYTHONUNBUFFERED": "1"}
    )
    
    # Wait for Streamlit to start
    time.sleep(3)
    
    # Open the browser
    webbrowser.open("http://localhost:8501")
    
    # Keep the process alive until the user closes the app
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        proc.terminate()
        sys.exit(0)