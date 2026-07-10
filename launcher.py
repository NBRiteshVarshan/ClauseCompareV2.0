import socket
import subprocess
import sys
import webbrowser
import time
import os

def is_port_open(port):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(('localhost', port))
            return True
        except ConnectionRefusedError:
            return False

if __name__ == "__main__":
    port = 8501

    if is_port_open(port):
        # Streamlit is already running – just open the browser
        webbrowser.open(f"http://localhost:{port}")
        sys.exit(0)

    # Start Streamlit
    streamlit_cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.headless", "true",
        "--server.port", str(port)
    ]
    proc = subprocess.Popen(
        streamlit_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "PYTHONUNBUFFERED": "1"}
    )

    # Wait for Streamlit to be ready
    while not is_port_open(port):
        time.sleep(0.5)

    # Open browser once
    webbrowser.open(f"http://localhost:{port}")

    # Keep process alive until user closes
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        proc.terminate()
        sys.exit(0)