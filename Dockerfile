# Dockerfile

# Use official Python image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy dependencies file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Copy .env file into container
COPY .env .env

# Make wait-for-it.sh executable
RUN chmod +x /app/wait-for-it.sh

# Expose FastAPI port
EXPOSE 8000

# Start Uvicorn server with wait-for-it
CMD ["/app/wait-for-it.sh", "db:5432", "--", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
