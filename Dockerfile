# Stage 1: Build Stage
FROM python:3.12-slim AS builder

# Set working directory in the builder stage
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Copy project metadata files
COPY pyproject.toml poetry.lock* ./

# Install project dependencies and package the project in editable mode (if desired)
# This step installs the project into the builder environment.
RUN pip install .

# Stage 2: Final Image
FROM python:3.12-slim

# Set working directory in the final image
WORKDIR /app

# Install runtime dependencies (for Chrome/Selenium and general OS support)
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

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local /usr/local

# Copy the rest of the application code
COPY . .

# Expose the API port
EXPOSE 8000

# Set environment variables for Python and logging
ENV PYTHONUNBUFFERED=1

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "ytgrid.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
