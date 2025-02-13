# Use an official Python 3.12 slim image as the base for the final production image.
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Install runtime dependencies needed for Chrome/Selenium and general OS support.
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg2 \
    unzip \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*
    
# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable

# Install the ytgrid package from PyPI.
RUN pip install --no-cache-dir ytgrid

# Expose the API port
EXPOSE 8000

# Start the FastAPI application using Uvicorn.
CMD ["uvicorn", "ytgrid.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
