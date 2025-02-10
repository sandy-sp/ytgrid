# Use an official Python runtime as a parent image.
FROM python:3.12-slim

# Set the working directory in the container.
WORKDIR /app

# Copy the requirements file and install dependencies.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the entire project into the container.
COPY . .

# Expose port 8000 for the FastAPI server.
EXPOSE 8000

# Define environment variables if needed (optional).
 ENV YTGRID_HEADLESS_MODE=True
 ENV YTGRID_USE_CELERY=True
# ... (other environment variables can be set here or via docker-compose)

# Run the FastAPI application with Uvicorn.
CMD ["uvicorn", "ytgrid.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
