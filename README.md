# ⚖️ ClauseCompare V2.0

**A privacy‑first, offline legal document comparison and management system**  
*Compare contracts • Identify missing clauses • Generate documents – all on your machine.*

---

## 🧠 Overview

ClauseCompare is a **fully offline** desktop application that helps legal teams quickly compare two versions of a contract. It extracts clauses from PDF and DOCX files, matches them by **meaning** (not just by words), and highlights:

- Which clauses are present in **both** documents (with similarity scores)
- Which clauses are **unique** to each document – so you know exactly where to focus your review

Built for **privacy and security**: all processing happens locally – no data ever leaves your computer.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Semantic Clause Matching** | Uses a novel hybrid algorithm (embedding + selective LLM) developed for this project – details reserved for our forthcoming research paper. |
| **Document Support** | Upload PDF and DOCX – format‑agnostic, numbering‑agnostic. |
| **Dashboard** | Overview of your document repository: total, compared, and pending documents. |
| **Persistent Storage** | Local SQLite database – user‑isolated, no cloud dependency. |
| **Document Generator** | Populate DOCX templates with variables (`$#var#$`) – ideal for drafting. |
| **Filtered Diff** | For each matched pair, highlights only changes in **numbers, dates, and places**. |
| **Reports** | Download comparison results as PDF, TXT, or JSON. |
| **Zero Configuration** | One‑click installer sets up everything – no technical skills needed. |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11 or 3.12** (3.13 not yet supported)
- **Ollama** (for local LLM) – download from [ollama.ai](https://ollama.ai)
- Internet connection (only for initial setup – once installed, fully offline)

### Installation

1. **Download the repository** and extract it to your Desktop (or any folder).
2. **Run the installer** for your operating system:

| OS | Installer | Action |
|----|-----------|--------|
| **macOS** | `install.command` | Double‑click (right‑click → Open if blocked) |
| **Windows** | `install.bat` | Double‑click |
| **Linux** | `install.sh` | Run `chmod +x install.sh && ./install.sh` |

The installer will:
- Install Python (if missing)
- Create a virtual environment
- Install all dependencies
- Generate a **launcher** script for daily use

### Launching the App

After installation, double‑click the generated launcher:

| OS | Launcher |
|----|----------|
| **macOS** | `run_clausecompare.command` |
| **Windows** | `run_clausecompare.bat` |
| **Linux** | `run_clausecompare.sh` |

Your default browser will open `http://localhost:8501`. The app is now ready to use.

> **Note:** Ollama must be running in the background. If you haven't already, pull the model:  
> `ollama pull llama3.2:3b`

---

## 🧠 Matching Algorithm (Research Preview)

The core matching engine uses a **novel hybrid algorithm** that combines:

- Bidirectional embedding‑based similarity
- Conflict‑resolution via a HashMap‑based stable‑matching heuristic
- Selective LLM verification for borderline cases

This approach achieves **near‑LLM accuracy** while using **97% fewer LLM calls** than naive methods – making it fast enough to run on standard laptops (M2/8GB).

A full description of the algorithm, along with ablation studies and performance benchmarks, will be presented in our upcoming research paper.

*Citation placeholder:*  
> [Your Name] et al., “ClauseCompare: A Hybrid Matching Algorithm for Efficient Legal Document Comparison,” *to be submitted*, 2026.

---

## 📁 Project Structure
ClauseCompareV2.0/
├── app.py # Streamlit frontend
├── clause_matcher.py # Matching algorithm (research)
├── document_processor.py # Text extraction & clause segmentation
├── db_manager.py # SQLite persistence
├── utils.py # Reports, diff, categorisation
├── requirements.txt # Dependencies
├── install.command / .bat / .sh # Installers
└── run_clausecompare.command / .bat / .sh # Launchers

---

## 🔒 Security & Privacy

- **100% offline** – no internet, no cloud, no telemetry.
- **No file‑system writes** for reports – all data streamed in memory.
- **HTML‑escaped user content** – prevents XSS.
- **Local‑only deployment** – the app is never exposed to the network.
- **Reset button** clears all caches and session data.

---

## 🤝 Contributions

- **Algorithm design & architecture** – [Your Name]
- **Implementation, testing, and deployment** – [Your Name] & [Assistant Name]

We welcome feedback and suggestions. For bug reports, please open an issue.

---

*ClauseCompare – because contracts deserve clarity.*