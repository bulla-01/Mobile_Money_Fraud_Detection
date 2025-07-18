# Dockerfile

FROM python:3.10.13

WORKDIR /app

# Optionally install system dependencies
# RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY .env .env

RUN chmod +x /app/wait-for-it.sh

EXPOSE 8000

CMD ["/app/wait-for-it.sh", "db:5432", "--", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

