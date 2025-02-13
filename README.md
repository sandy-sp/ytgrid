
# 🎥 YTGrid - Hybrid CLI + API for Scalable YT Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)

YTGrid is a powerful, scalable, and flexible YT automation tool that enables looped playback, remote control, and real-time tracking using a hybrid **CLI + API architecture**. It integrates FastAPI for REST API control, Selenium for browser automation, and supports concurrent task execution via Python multiprocessing or Celery.

---

## **📌 Features**

- **Hybrid Interface** – Manage automation via **CLI + API**
- **Scalable Execution** – Run multiple browser instances in parallel
- **Configurable Automation** – Set playback speed, loop count, and more
- **Celery Integration** – Supports both **multiprocessing & Celery** for task execution (Celery is disabled by default in the PyPI release)
- **Real-time Updates** – Monitor active sessions via Server-Sent Events (SSE)
- **Lightweight Installation** – Available as a **PyPI package**

---

## **📦 Installation (PyPI)**

YTGrid is available on PyPI. Install it using:

```bash
pip install ytgrid
```

**Requirements:**

- **Python 3.8+**
- **Google Chrome:** *For the PyPI version, you must have Google Chrome installed on your system. ChromeDriver is automatically managed by `webdriver-manager`, but the Chrome browser itself is not bundled with YTGrid.*
- **ChromeDriver:** Automatically managed by `webdriver-manager`
- **Redis:** Only required if you choose to enable Celery (Celery is off by default)

---


## **🚀 CLI Usage**

YTGrid provides a **command-line interface (CLI)** to manage automation sessions.

### **Start a Session**

```bash
ytgrid start --session-id test123 --url "https://www.youtube.com/watch?v=UXFBUZEpnrc" --speed 1.5 --loops 3 
```

- **session_id:** Unique identifier for the session (e.g., 'test123').
- **url:** The YT video URL to automate.
- **speed:** Playback speed multiplier (1.0 for normal speed).
- **loops:** Number of times to loop the video.
- **task_type:** Type of automation task (default is 'video').

### **Check Active Sessions**

```bash
ytgrid status
```

This command displays all active sessions along with their current loop progress.

### **Stop a Session**

```bash
ytgrid stop --session-id test123
```

Stop a running session by specifying its unique session_id.

### **Batch Process Sessions**

```bash
ytgrid batch tasks.csv --delimiter ","
```

- The CSV file (`tasks.csv`) should have a header row with columns: `session_id, url, speed, loops, task_type`.
- This command starts multiple sessions concurrently based on the CSV content.

### **Toggle Celery Mode**

```bash
ytgrid toggle-celery
```

Toggle the `YTGRID_USE_CELERY` setting in your `.env` file (switching Celery on or off) without manually editing the file.

---

## 🐳 Running YTGrid via Docker

YTGrid can be deployed using Docker, which allows you to run the application along with its dependencies in a containerized environment. We offer two primary ways to obtain the Docker image:

### 1. Building the Image Locally

Use the provided Dockerfile to build a lean, production-ready image that installs YTGrid from PyPI and includes all necessary dependencies (including Google Chrome).

```bash
docker build -t ytgrid .
```

Then, run the container:

```bash
docker run -p 8000:8000 ytgrid
```

Or, for an orchestrated setup with Redis (for optional Celery support), use docker-compose:

```bash
docker-compose up --build
```

### 2. Pulling Prebuilt Images

You can also pull the latest prebuilt Docker image directly from our registries:

#### Docker Hub

Pull the image from Docker Hub:

```bash
docker pull sandy1sp/ytgrid:latest
```

Then run the container:

```bash
docker run -p 8000:8000 sandy1sp/ytgrid:latest
```

#### GitHub Container Registry (GHCR)

Alternatively, pull the image from GHCR:

```bash
docker pull ghcr.io/sandy-sp/ytgrid:latest
```

Then run the container:

```bash
docker run -p 8000:8000 ghcr.io/sandy-sp/ytgrid:latest
```

---

## 🔄 Using Redis for Celery Implementation

YTGrid supports distributed task processing using Celery. Although Celery is disabled by default in the PyPI release, you can enable it in a Docker environment for advanced use cases. When Celery is enabled, a Redis server is required as the message broker and result backend.

### Enabling Celery in Docker

In the `docker-compose.yml` file, Redis is defined as a service. To enable Celery:

1. **Set Environment Variables:**  
   Ensure that the following environment variables are set (as shown in the `docker-compose.yml`):

   ```yaml
   - YTGRID_USE_CELERY=True
   - CELERY_BROKER_URL=redis://redis:6379/0
   - CELERY_RESULT_BACKEND=redis://redis:6379/0
   ```

2. **Run docker-compose:**  
   Start the services with:

   ```bash
   docker-compose up --build
   ```

   This will start both the YTGrid container and the Redis container. The YTGrid application will then use Celery with Redis for task management.

3. **Verify Celery Operation:**  
   You can run a Celery worker by executing:

   ```bash
   docker exec -it ytgrid_api celery -A ytgrid.backend.celery_app worker --loglevel=info
   ```

   This worker will connect to the Redis server and process tasks. You can also use monitoring tools like Flower to visualize task processing.

### For PyPI Users

For those who install YTGrid via pip, Celery is disabled by default to keep the package lean. If you want to enable Celery locally, you must:

- Manually install and run Redis on your machine (e.g., using your system's package manager or running a Redis Docker container).
- Toggle the `YTGRID_USE_CELERY` setting (using the CLI command `ytgrid toggle-celery` or by editing your `.env` file).

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

## **🛠️ Configuration**

YTGrid is configurable via environment variables. Create a `.env` file in the project root with the following content:

```ini
# General settings
YTGRID_HEADLESS_MODE=True
YTGRID_DEFAULT_SPEED=1.0
YTGRID_DEFAULT_LOOP_COUNT=1
YTGRID_MAX_SESSIONS=5

# Real-time updates
YTGRID_REALTIME_UPDATES=False
YTGRID_WEBSOCKET_SERVER_URL=ws://web:8000/ws

# Browser settings
YTGRID_USE_TEMP_USER_DATA=True
YTGRID_BROWSER_TIMEOUT=20

# Celery configuration (Celery is off by default in the PyPI release)
YTGRID_USE_CELERY=False
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Session storage: Options include in-memory (default) or persistent storage (e.g., sqlite)
YTGRID_SESSION_STORAGE=sqlite
```

*Note: For local PyPI usage, ensure Google Chrome is installed. For Docker deployments, the image includes Chrome installation.*

---

## 🔮  Future Releases

We have an exciting roadmap ahead for YTGrid. Some of the planned enhancements include:

- **Advanced Dynamic Scheduling:**  
  Implement adaptive scheduling algorithms that dynamically adjust the number of parallel sessions based on real-time system metrics (e.g., CPU and memory usage). This will help optimize resource utilization without the need for complex predictive models.

- **Expanded Automation Capabilities:**  
  In addition to the current "video" task type, we plan to add support for:
  - **Playlist:** Accept a YT playlist URL and play the entire playlist in a loop.
  - **Channel:** Accept a YT channel URL, automatically gather all available video links from the channel, and play them all in loops.
  
  These enhancements will broaden the automation options available to users.

- **Decoupled Microservices Architecture:**  
  Separate the API gateway from the automation workers into distinct services, allowing for independent scaling and improved fault tolerance. We plan to explore container orchestration using Kubernetes for enhanced scalability in cloud environments.

- **User Interface Enhancements:**  
  Develop a web-based dashboard for real-time monitoring and control of automation sessions, making it easier for users to manage tasks without relying solely on the CLI.

- **Extended Batch Processing Options:**  
  Support additional input formats such as JSON and Excel for batch job submissions, along with interactive CLI prompts to simplify the process.

These planned features aim to make YTGrid more robust, scalable, and user-friendly, ensuring that it evolves to meet the diverse needs of automation tasks.


---
## **📜 License**

This project is licensed under the [MIT License](LICENSE).

---

## **🌍 Contributing**

Contributions are welcome!  
To contribute:
1. **Fork the repository.**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```
3. **Commit your changes.**
4. **Push to your fork and create a pull request.**

---

## **📖 Additional Resources**

- [Documentation](https://github.com/sandy-sp/ytgrid/README.md)
- [PyPI Package](https://pypi.org/project/ytgrid/)
- [Docker Hub Package](https://hub.docker.com/r/sandy1sp/ytgrid)
- [GitHub Repository](https://github.com/sandy-sp/ytgrid/)

---