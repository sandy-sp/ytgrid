from setuptools import setup, find_packages

setup(
    name="ytgrid",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "selenium",
        "webdriver-manager",
        "requests",
        "rich"  # For CLI live tracking
    ],
    entry_points={
        "console_scripts": [
            "ytgrid=ytgrid.cli:main"
        ]
    },
    description="Hybrid CLI + API for scalable YouTube automation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
