from setuptools import setup, find_packages

setup(
    name="ytgrid",
    version="1.0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "selenium",
        "webdriver-manager",
        "requests",
        "rich",
        "python-dotenv",
        "websocket-client",
        "bs4",
        "celery>=5.2",    # Added for Celery integration
        "redis>=4.2"      # Added for Celery's broker and backend support
    ],
    entry_points={
        "console_scripts": [
            "ytgrid=ytgrid.cli:main"
        ]
    },
    description=(
        "YTGrid is a powerful, scalable, and flexible YT automation tool that enables looped playback, "
        "remote control, and real-time tracking using a hybrid CLI + API architecture. It integrates FastAPI "
        "for REST API control, Selenium for browser automation, and Python multiprocessing/Celery for concurrent tasks."
    ),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Sandeep Paidipati",
    author_email="sandeep.paidipati@gmail.com",
    url="https://github.com/sandy-sp/ytgrid",
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
