FROM python:3.10-bullseye

WORKDIR /app

# Set platform explicitly to AMD64 for TensorFlow
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore

# Install system dependencies required by TensorFlow and other packages
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
    wget \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install TensorFlow first
RUN pip install --upgrade pip
RUN pip install tensorflow==2.15.0

COPY requirements.txt .

# Install other Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make scripts executable
RUN chmod +x /app/wait-for-it.sh
RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
