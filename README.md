# 🎥 YTGrid - Hybrid CLI + API for Scalable YouTube Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)

**YTGrid** is a powerful, scalable, and flexible YouTube automation tool designed to enable looped playback, remote control, and real-time tracking using a hybrid **CLI + API architecture**. It leverages:

- **FastAPI** for building a RESTful API
- **Selenium** for browser automation (with headless Chrome)
- **Celery** (or Python multiprocessing) for concurrent and asynchronous task execution
- **Server-Sent Events (SSE)** for real-time session updates
- A modern **CLI** built with Typer

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
  - [Using Poetry (Recommended)](#using-poetry-recommended)
  - [Using pip](#using-pip)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
  - [Locally (without Docker)](#running-locally-without-docker)
  - [With Docker Compose](#docker-deployment)
- [CLI Usage](#cli-usage)
- [API Usage](#api-usage)
- [Testing](#running-tests)
- [CI/CD](#ci-cd)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Features

- **Hybrid Interface:**  
  Use both a command-line interface and a RESTful API to manage YouTube automation sessions.

- **YouTube Video Automation:**  
  Automate the process of searching, playing, and looping YouTube videos using Selenium.

- **Concurrent Execution:**  
  Run multiple automation sessions in parallel, using either multiprocessing or Celery for asynchronous background tasks.

- **Real-Time Monitoring:**  
  Receive live updates about active sessions via WebSockets and an SSE endpoint.

- **Configurable Parameters:**  
  Easily adjust playback speed, loop count, and other settings through configuration.

- **Containerized Deployment:**  
  Run the entire application stack (FastAPI, Celery worker, Redis, Flower, and load test) using Docker Compose.

- **Modern CLI:**  
  Manage sessions and tasks using an intuitive CLI built with Typer.

---

## Project Structure

```plaintext
YTGrid/
├── ytgrid/                 # Core Python package (installable)
│   ├── __init__.py
│   ├── cli.py              # CLI interface
│   ├── automation/         # YouTube automation layer
│   │   ├── __init__.py
│   │   ├── base_player.py  # Abstract automation player interface
│   │   ├── browser.py      # Selenium WebDriver manager
│   │   └── player.py       # Concrete automation (VideoPlayer)
│   ├── backend/            # API and task management
│   │   ├── __init__.py
│   │   ├── celery_app.py   # Celery application configuration
│   │   ├── dependencies.py # Dependency injections (e.g., session store)
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── routes.py       # Aggregated API routes
│   │   ├── session_store.py# In-memory session management
│   │   └── task_manager.py # Task management (multiprocessing/Celery)
│   │       └── routes/     # Submodules for API endpoints
│   │           ├── __init__.py
│   │           ├── session.py
│   │           └── task.py
│   └── utils/              # Utility functions and configuration
│       ├── __init__.py
│       ├── config.py     # Application configuration
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
├── pyproject.toml          # Poetry project file (dependency management)
├── poetry.lock             # Poetry lock file
├── README.md               # This file
└── .gitignore              # Files to ignore in Git
```

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

3. **Disable Virtual Environment Creation (for Docker compatibility):**

   ```bash
   poetry config virtualenvs.create false
   ```

4. **Install Dependencies:**

   ```bash
   poetry install --no-root --only main
   ```

### Using pip

If you prefer to use pip, you can install dependencies from the provided **requirements.txt**:

```bash
pip install -r requirements.txt
```

---

## Configuration

YTGrid uses environment variables for configuration. Create a `.env` file in the project root (if desired) with settings such as:

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

# Celery configuration
YTGRID_USE_CELERY=True
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

*Note:* In Docker, the Compose file also sets these environment variables.

---

## Running the Application

### Running Locally (Without Docker)

1. **Start the API Server:**

   ```bash
   uvicorn ytgrid.backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start the Celery Worker:**

   ```bash
   celery -A ytgrid.backend.celery_app.celery_app worker --loglevel=info --uid=1000
   ```

3. **(Optional) Start Flower for Monitoring:**

   ```bash
   celery -A ytgrid.backend.celery_app.celery_app flower --port=5555
   ```

### Docker Deployment

Ensure Docker Desktop is configured to share your project directory.

1. **Build and Start Containers:**

   ```bash
   docker-compose up --build
   ```

   This command starts the following services:
   - **web:** FastAPI server (with Uvicorn)
   - **celery_worker:** Celery worker for background tasks
   - **redis:** Redis server (broker/backend)
   - **flower:** (Optional) Flower dashboard for Celery monitoring
   - **load_test:** Load test service (runs `run_load_test.py`)

2. **Stopping Containers:**

   ```bash
   docker-compose down
   ```

---

## CLI Usage

YTGrid installs a CLI tool that lets you manage sessions from the command line.

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

*Note:* Replace `<unique_id>` with a session identifier (e.g., a UUID).

---

## API Usage

### Key Endpoints:

- **Start Session:**
  
  ```bash
  curl -X POST "http://127.0.0.1:8000/sessions/start" \
       -H "Content-Type: application/json" \
       -d '{"url": "https://www.youtube.com/watch?v=OaOK76hiW8I", "speed": 1.5, "loop_count": 3}'
  ```

- **Check Status:**

  ```bash
  curl -X GET "http://127.0.0.1:8000/status"
  ```

- **Stop Session:**

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

YTGrid includes unit and integration tests in the `tests/` directory.

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

A sample GitHub Actions workflow is provided in `.github/workflows/ci.yml` which:

- Checks out your code.
- Sets up Python and Poetry.
- Installs dependencies.
- Runs your test suite.
- (Optionally) Builds your Docker images.

Refer to the workflow file for details.

---

## Contributing

Contributions are welcome! To contribute:

1. **Fork the Repository.**
2. **Create a Feature Branch:**
   ```bash
   git checkout -b feature/my-feature
   ```
3. **Commit Your Changes.**
4. **Push to Your Fork.**
5. **Open a Pull Request.**

Please follow the code style and write tests for new features.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Contact

For questions or suggestions, please contact [Sandeep Paidipati](mailto:sandeep.paidipati@gmail.com).

---

*Happy automating!*
```

---

### **Summary:**

- The new **README.md** covers all key aspects of the project.
- It provides clear sections on features, project structure, installation (both with Poetry and pip), configuration, running the application locally and via Docker, CLI & API usage, testing, CI/CD, contributing, and licensing.
- This version adheres to industry best practices for open source Python projects, helping both new contributors and users quickly understand and work with YTGrid.

Feel free to modify or extend sections as needed for your project's evolving requirements. Let me know if you need any further adjustments or additional sections!