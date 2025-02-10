# 🎥 YTGrid - Hybrid CLI + API for Scalable YouTube Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)

**YTGrid** is a powerful, scalable, and flexible YouTube automation tool designed to enable looped playback, remote control, and real-time tracking using a hybrid **CLI + API architecture**. It leverages modern Python frameworks and tools to provide:

- A RESTful API built with **FastAPI**
- Browser automation using **Selenium** (with headless Chrome)
- Concurrent and asynchronous task execution via **Celery** (or Python multiprocessing)
- Real-time session updates using **Server-Sent Events (SSE)**
- A user-friendly **CLI** built with **Typer**

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
  - [Using Poetry (Recommended)](#using-poetry-recommended)
  - [Using pip](#using-pip)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
  - [Locally (Without Docker)](#running-locally-without-docker)
  - [With Docker Compose](#docker-deployment)
- [CLI Usage](#cli-usage)
- [API Usage](#api-usage)
- [Running Tests](#running-tests)
- [CI/CD Pipeline](#ci-cd-pipeline)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Features

- **Hybrid Interface:**  
  Manage automation sessions via both a command-line interface and a RESTful API.
  
- **YT Automation:**  
  Automate YT video playback, searching, and looping using Selenium.
  
- **Concurrent Execution:**  
  Execute multiple sessions in parallel using either multiprocessing or Celery for asynchronous processing.
  
- **Real-Time Monitoring:**  
  Get live updates on active sessions through WebSockets and an SSE endpoint.
  
- **Configurable Parameters:**  
  Adjust playback speed, loop count, and other settings easily via environment variables.
  
- **Containerized Deployment:**  
  Deploy the complete stack (FastAPI, Celery worker, Redis, Flower, and load test) using Docker Compose.
  
- **Modern CLI:**  
  Manage sessions using a user-friendly CLI built with Typer.

---

## Project Structure

```plaintext
YTGrid/
├── ytgrid/                 # Core Python package (installable)
│   ├── __init__.py
│   ├── cli.py              # Command-line interface for managing sessions/tasks
│   ├── automation/         # YT automation functionality
│   │   ├── __init__.py
│   │   ├── base_player.py  # Abstract automation player interface
│   │   ├── browser.py      # Selenium WebDriver management (with incognito & retry logic)
│   │   └── player.py       # Concrete automation (VideoPlayer implementation)
│   ├── backend/            # API and task management
│   │   ├── __init__.py
│   │   ├── celery_app.py   # Celery application configuration
│   │   ├── dependencies.py # Dependency injection (e.g., session store)
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── routes.py       # Aggregated API routes (combines session and task endpoints)
│   │   ├── session_store.py# In-memory session management
│   │   ├── task_manager.py # Manages tasks using multiprocessing or Celery
│   │   └── tasks.py        # Celery task definitions
│   └── utils/              # Utility functions and configuration
│       ├── __init__.py
│       ├── config.py     # Application configuration and environment variables
│       └── logger.py     # Logging setup
├── examples/               # Example scripts for CLI and API usage
│   ├── example_api.py
│   └── example_cli.py
├── tests/                  # Unit and integration tests
│   ├── test_api.py
│   ├── test_automation.py
│   └── test_cli.py
├── Dockerfile              # Docker build file (using Poetry)
├── docker-compose.yml      # Docker Compose configuration for deployment
├── pyproject.toml          # Poetry project configuration (dependency management)
├── poetry.lock             # Poetry lock file (generated automatically)
├── README.md               # This file
└── .gitignore              # Git ignore file for unnecessary files
```

*Note:* The **examples/** and **tests/** folders are included for development and documentation purposes. 

---

## Installation

### Using Poetry (Recommended)

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/sandy-sp/ytgrid.git
   cd ytgrid
   ```

2. **Install Poetry (if not already installed):**

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   export PATH="$HOME/.local/bin:$PATH"
   ```

3. **Disable Poetry's Virtual Environment Creation (for Docker compatibility):**

   ```bash
   poetry config virtualenvs.create false
   ```

4. **Install Dependencies:**

   ```bash
   poetry install --no-root --only main
   ```

### Using pip

If you prefer pip, you can install dependencies from an exported requirements file (if provided). However, for the best experience, we recommend using Poetry.

---

## Configuration

YTGrid is configured via environment variables. Create a `.env` file in the project root (optional) with the following sample configuration:

```dotenv
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
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

*Note:* In your Docker Compose file, these variables are also set as environment variables.

---

## Running the Application

### Running Locally (Without Docker)

1. **Start the FastAPI Server:**

   ```bash
   uvicorn ytgrid.backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start the Celery Worker (if using Celery):**

   ```bash
   celery -A ytgrid.backend.celery_app.celery_app worker --loglevel=info --uid=1000
   ```

3. **(Optional) Start Flower for Monitoring:**

   ```bash
   celery -A ytgrid.backend.celery_app.celery_app flower --port=5555
   ```

### Docker Deployment

1. **Ensure Docker Desktop Is Configured:**  
   Make sure your project directory is shared in Docker settings.

2. **Build and Start Containers:**

   ```bash
   docker-compose up --build
   ```

   This will start the following services:
   - **web:** FastAPI server (with Uvicorn)
   - **celery_worker:** Celery worker for asynchronous tasks
   - **redis:** Redis server (broker and result backend)
   - **flower:** (Optional) Flower dashboard for monitoring Celery tasks
   - **load_test:** A service to run load tests (executes `run_load_test.py`)

3. **Stop Containers:**

   ```bash
   docker-compose down
   ```

---

## CLI Usage

YTGrid installs a CLI tool for managing automation sessions.

### Examples:

- **Start a Session:**

  ```bash
  ytgrid start --session_id <unique_id> --url "https://www.youtube.com/watch?v=OaOK76hiW8I" --speed 1.5 --loops 3
  ```

- **Check Active Sessions:**

  ```bash
  ytgrid status
  ```

- **Stop a Session:**

  ```bash
  ytgrid stop --session_id <unique_id>
  ```

*Replace `<unique_id>` with a unique session identifier (e.g., a UUID).*

---

## API Usage

### Key Endpoints

- **Start a Session:**  
  `POST /sessions/start`
  
  ```bash
  curl -X POST "http://127.0.0.1:8000/sessions/start" \
       -H "Content-Type: application/json" \
       -d '{"url": "https://www.youtube.com/watch?v=OaOK76hiW8I", "speed": 1.5, "loop_count": 3}'
  ```

- **Check Session Status:**  
  `GET /status`
  
  ```bash
  curl -X GET "http://127.0.0.1:8000/status"
  ```

- **Stop a Session:**  
  `POST /sessions/stop`
  
  ```bash
  curl -X POST "http://127.0.0.1:8000/sessions/stop" \
       -H "Content-Type: application/json" \
       -d '{"session_id": 1}'
  ```

- **Task Endpoints:**  
  - **Start Task:** `POST /tasks/`
  - **Stop Task:** `POST /tasks/stop`
  - **Get Active Tasks:** `GET /tasks/`
  - **SSE Streaming:** `GET /tasks/stream`

---

## Running Tests

All unit and integration tests reside in the **tests/** directory.

- **Run All Tests:**

  ```bash
  pytest --maxfail=1 --disable-warnings -q
  ```

- **Run a Specific Test:**

  ```bash
  pytest tests/test_api.py
  ```

---

## CI/CD Pipeline

A sample GitHub Actions workflow is provided in **.github/workflows/ci.yml**. This workflow:

- Checks out the repository.
- Sets up Python and Poetry.
- Installs dependencies.
- Runs the test suite.
- Optionally builds Docker images.

Refer to the workflow file for details.

---

## Contributing

Contributions are welcome! To contribute:

1. **Fork the Repository.**
2. **Create a Feature Branch:**

   ```bash
   git checkout -b feature/my-feature
   ```

3. **Commit Your Changes:**  
   Follow the existing code style and add tests for new features.
4. **Push to Your Fork and Open a Pull Request.**

Please adhere to the [MIT License](LICENSE) and follow best practices for code quality and documentation.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🔗 Links & Resources
📖 Documentation: API Reference

🐍 PyPI Package: metadata-cleaner

🚀 GitHub Repository: metadata-cleaner

## ❤️ Support
If you found this tool useful, give it a ⭐ on GitHub!
For issues or questions, open an issue.



