# Use an official Python 3.12 slim image.
FROM python:3.12-slim AS base

# Install system dependencies needed for Chrome, Selenium, and Poetry.
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    unzip \
    curl \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome.
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry.
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH.
ENV PATH="/root/.local/bin:${PATH}"

# Disable Poetry's virtual environment creation.
RUN poetry config virtualenvs.create false

# Set the working directory.
WORKDIR /app

# Copy Poetry configuration files first (for caching).
COPY pyproject.toml poetry.lock* ./

# Install dependencies first (to optimize caching).
RUN poetry install --no-root --only main

# Copy the rest of the application.
COPY . .

# Set entrypoint to YTGrid CLI
ENTRYPOINT ["ytgrid"]
