# YTGrid: Hybrid CLI + API for Scalable YouTube Automation

YTGrid is a lightweight and scalable YouTube automation tool that provides:
- **CLI Interface**: Manage video automation tasks.
- **FastAPI Backend**: Remote control & session tracking.
- **Parallel Task Management**: Optimized video looping.
- **Selenium Automation**: Runs YouTube in headless mode.

## Installation
Clone the repository and install:
```sh
pip install -e .
Usage
Run the CLI:

sh
Copy
Edit
ytgrid --help
Start the API server:

sh
Copy
Edit
uvicorn ytgrid.backend.main:app --reload
yaml
Copy
Edit

---