FROM python:3.10-bullseye

WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    curl \
    git \
    libatlas-base-dev \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/wait-for-it.sh

EXPOSE 8000

CMD ["/app/wait-for-it.sh", "db:5432", "--", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
