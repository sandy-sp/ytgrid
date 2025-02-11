# 🎥 YTGrid - Hybrid CLI + API for Scalable YT Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)


**YTGrid** is a powerful, scalable, and flexible YT automation tool designed to enable looped playback, remote control, and real-time tracking using a hybrid **CLI + API architecture**. It provides:

- A RESTful API built with **FastAPI**
- Browser automation using **Selenium** (with headless Chrome)
- Concurrent and asynchronous task execution via **Celery** (or Python multiprocessing)
- Real-time session updates using **Server-Sent Events (SSE)**
- A user-friendly **CLI** built with **Typer**

---

## **📌 Features**
✅ **Hybrid Interface** – Manage automation via **CLI + API**  
✅ **Scalable Execution** – Run multiple browser instances in parallel  
✅ **Configurable Automation** – Set playback speed, loop count, and more  
✅ **Celery Integration** – Supports both **multiprocessing & Celery** for task execution  
✅ **Lightweight Installation** – Available as a **PyPI package**  

---

## **📦 Installation (PyPI)**
YTGrid is available on PyPI. Install it using:
```bash
pip install ytgrid
```

**Requirements:**
- **Python 3.8+**
- **Google Chrome**
- **ChromeDriver** (Automatically managed by `webdriver-manager`)
- **Redis (if using Celery)**

---

## **🐳 Running YTGrid via Docker**

You can also run YTGrid inside a **Docker container**.

### **1️⃣ Build the Docker Image**

```bash
bashCopyEditdocker compose build
```

### **2️⃣ Start the Container**

```bash
bashCopyEditdocker compose up -d
```

✅ This will start:

- The **FastAPI backend** in the background.
- A **fully interactive shell** for running `ytgrid` CLI commands.

### **3️⃣ Open an Interactive Shell**

```bash
bashCopyEditdocker exec -it ytgrid_cli /bin/sh
```

Now, you can run:

```bash
bashCopyEditytgrid --help
```

---

## **🚀 CLI Usage**
YTGrid provides a **command-line interface (CLI)** to manage automation.

### **Start a Session**
```bash
ytgrid start --session-id test123 --url "https://www.youtube.com/watch?v=UXFBUZEpnrc" --speed 1.5 --loops 3
```

### **Check Active Sessions**
```bash
ytgrid status
```

### **Stop a Session**
```bash
ytgrid stop --session-id test123
```

### **Detailed Usage Instructions**
```bash
ytgrid --help
```

---

## **🖥️ API Usage**
YTGrid provides a **FastAPI-based REST API**.

### **1️⃣ Start a Session**
```bash
curl -X POST "http://127.0.0.1:8000/sessions/start" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=OaOK76hiW8I", "speed": 1.5, "loop_count": 3}'
```

### **2️⃣ Check Active Sessions**
```bash
curl -X GET "http://127.0.0.1:8000/sessions/status"
```

### **3️⃣ Stop a Session**
```bash
curl -X POST "http://127.0.0.1:8000/sessions/stop" \
     -H "Content-Type: application/json" \
     -d '{"session_id": 1}'
```

---
## **🛠️ Running External Scripts in Docker**

To execute external scripts like `test.py` inside the container:

```bash
bashCopyEditdocker exec -it ytgrid_cli python test.py
```

✅ This will start **external scripts automation sessions in parallel**.

---

## **🛠️ Configuration**
YTGrid is configurable via environment variables.  
Create a `.env` file in the project root:

```ini
YTGRID_HEADLESS_MODE=True
YTGRID_DEFAULT_SPEED=1.0
YTGRID_DEFAULT_LOOP_COUNT=1
YTGRID_MAX_SESSIONS=5
YTGRID_USE_TEMP_USER_DATA=True
YTGRID_BROWSER_TIMEOUT=20
YTGRID_USE_CELERY=False  # Set to True if using Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## **🧪 Running Tests**
Run unit tests using `pytest`:
```bash
pytest tests/
```

To run a specific test:
```bash
pytest tests/test_api.py
```

---

## **📜 License**
This project is licensed under the [MIT License](LICENSE).

---

## **🌍 Contributing**
Contributions are welcome!  
To contribute:
1. **Fork the repository**
2. **Create a feature branch**
```bash
git checkout -b feature/my-feature
```
3. **Commit your changes**  
4. **Push to your fork and create a PR**

---

## **📖 Additional Resources**
- 📄 [Documentation](https://github.com/sandy-sp/ytgrid/README.md)  
- 🐍 [PyPI Package](https://pypi.org/project/ytgrid/)  
- 🚀 [GitHub Repository](https://github.com/sandy-sp/ytgrid/)  

---