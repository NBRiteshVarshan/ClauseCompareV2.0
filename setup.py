from setuptools import setup

APP = ['app.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['streamlit', 'sentence_transformers', 'torch', 'sklearn', 'plotly', 'pandas', 'numpy', 'ollama', 'docx2txt', 'fitz', 'reportlab', 'docx'],
    'includes': ['sqlite3', 'json', 're', 'html', 'pathlib', 'datetime'],
    'excludes': ['tkinter'],
    'plist': {
        'CFBundleName': 'ClauseCompareV2',
        'CFBundleDisplayName': 'ClauseCompare V2.0',
        'CFBundleIdentifier': 'com.yourcompany.clausecompare',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'NSHumanReadableCopyright': '© 2025 Your Name',
        'LSUIElement': True,  # Hides the Dock icon (optional)
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)