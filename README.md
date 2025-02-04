
# 🎥 YTGrid - Hybrid CLI + API for Scalable YT Video Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)

🚀 **YTGrid** is a **powerful, scalable, and flexible YT automation tool** that enables **looped playback, remote control, and real-time tracking** using a hybrid **CLI + API architecture**.  
It integrates **FastAPI for REST API control**, **Selenium for browser automation**, and **Python multiprocessing for concurrent tasks**.

---

## 📌 **Table of Contents**
- [✨ Features](#-features)
- [📂 Project Structure](#-project-structure)
- [⚡ Installation](#-installation)
- [🖥️ CLI Usage](#-cli-usage)
- [🖥️ API Usage](#-api-usage)
- [🧪 Running Tests](#-running-tests)
- [🐳 Docker Deployment](#-docker-deployment)
- [📜 License](#-license)

---

## ✨ **Features**
### ✅ **New & Improved Features**
🔹 **Hybrid CLI + API** – Use both a **command-line interface** and a **FastAPI-powered REST API**.  
🔹 **YT Automation** – Automatically **search, play, and loop videos** using **Selenium**.  
🔹 **Session Tracking** – Monitor active sessions **in real time** using WebSockets.  
🔹 **Parallel Execution** – Run **multiple YT automation sessions** simultaneously.  
🔹 **Configurable Playback Speed** – Adjust video playback speed dynamically.  
🔹 **WebSocket Real-Time Updates** – Get live session updates.  
🔹 **Optimized Browser Management** – Uses **headless Chrome** for better performance.  
🔹 **Session Persistence** – Track running and completed sessions efficiently.  
🔹 **Comprehensive Logging** – Logs all activity for debugging and monitoring.  

---

## 📂 **Project Structure**
```
YTGrid/
 ├── ytgrid/                 → Core Python package (installable via pip)
 │   ├── cli.py              → CLI for managing sessions
 │   ├── backend/            → FastAPI API for remote control
 │   │   ├── main.py         → API entry point
 │   │   ├── routes.py       → API endpoints
 │   │   ├── task_manager.py → Manages multiprocessing tasks
 │   │   ├── session_store.py → In-memory session tracking
 │   ├── automation/         → YT playback automation
 │   │   ├── player.py       → Automates search & playback
 │   │   ├── browser.py      → Manages Selenium WebDriver
 │   ├── utils/              → Helper functions
 │   │   ├── logger.py       → Logging system
 │   │   ├── config.py       → Configuration settings
 │
 ├── examples/               → Example scripts
 │   ├── example_cli.py      → CLI example usage
 │   ├── example_api.py      → API example usage
 │
 ├── tests/                  → Unit tests
 │   ├── test_cli.py         → CLI tests
 │   ├── test_api.py         → API tests
 │   ├── test_automation.py  → Automation tests
 │
 ├── setup.py                → Python package setup script
 ├── requirements.txt        → Dependencies
 ├── README.md               → Documentation
 ├── .gitignore              → Ignore unnecessary files
 ├── docker-compose.yml      → Docker deployment
 ├── Dockerfile              → Docker build file
```
---

## ⚡ **Installation**
**Step 1: Clone the Repository**
```sh
git clone https://github.com/sandy-sp/ytgrid.git
cd ytgrid
```

**Step 2: Create a Virtual Environment**
```sh
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Step 3: Install YTGrid Locally**
```sh
pip install -e .
```

**Step 4: Verify Installation**
```sh
ytgrid --help
```
✅ If you see CLI options, installation was successful.

---

## 🖥️ **CLI Usage**
### **Start a YT Automation Session**
```sh
ytgrid start --url "https://www.youtube.com/watch?v=OaOK76hiW8I" --speed 1.5 --loops 3
```

### **Check Active Sessions**
```sh
ytgrid status
```

### **Stop a Session**
```sh
ytgrid stop --session_id <num>
```

---

## 🖥️ **API Usage**
### **Start API Server**
```sh
uvicorn ytgrid.backend.main:app --reload
```

### **Start a YT Session**
```sh
curl -X POST "http://127.0.0.1:8000/sessions/start" -H "Content-Type: application/json" -d '{
  "url": "https://www.youtube.com/watch?v=OaOK76hiW8I",
  "speed": 1.5,
  "loop_count": 3
}'
```

### **Check Session Status**
```sh
curl -X GET "http://127.0.0.1:8000/status"
```

### **Stop a Session**
```sh
curl -X POST "http://127.0.0.1:8000/sessions/stop" -H "Content-Type: application/json" -d '{"session_id": 1}'
```

---

## 🧪 **Running Tests**
### **Run All Tests**
```sh
pytest tests/
```

### **Run a Specific Test**
```sh
pytest tests/test_api.py
```
✅ If all tests pass, YTGrid is working correctly.

---

## 🐳 **Docker Deployment**
### **Build and Run in Docker**
```sh
docker-compose up --build
```

### **Stop Containers**
```sh
docker-compose down
```
✅ YTGrid will now run **in a containerized environment.**

---

## 📜 **License**
YTGrid is released under the **MIT License**.

---
