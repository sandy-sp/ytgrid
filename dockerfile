# Use an official Python 3.12 slim image.
FROM python:3.12-slim

# Install system dependencies needed for Chrome and Poetry.
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    unzip \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Install Google Chrome.
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
 && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
 && apt-get update && apt-get install -y google-chrome-stable \
 && apt-get install -y --no-install-recommends \
         fonts-liberation \
         libappindicator3-1 \
         libasound2 \
         libatk-bridge2.0-0 \
         libatk1.0-0 \
         libcups2 \
         libdbus-1-3 \
         libgdk-pixbuf2.0-0 \
         libnspr4 \
         libnss3 \
         libx11-xcb1 \
         libxcomposite1 \
         libxdamage1 \
         libxfixes3 \
         libxrandr2 \
         xdg-utils \
 && rm -rf /var/lib/apt/lists/*

# Install Poetry.
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH.
ENV PATH="/root/.local/bin:${PATH}"

# Disable Poetry's virtual environment creation.
RUN poetry config virtualenvs.create false

# Set the working directory.
WORKDIR /app

# Copy Poetry configuration files.
COPY pyproject.toml poetry.lock* ./

# Install project dependencies using Poetry.
RUN poetry install --no-root --only main

# Copy the rest of the application.
COPY . .

# Expose port 8000 for FastAPI.
EXPOSE 8000

# Define the default command.
CMD ["uvicorn", "ytgrid.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
