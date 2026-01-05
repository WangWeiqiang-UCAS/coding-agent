
# Docker 配置
## 1.  Dockerfile

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . . 

RUN pip install -e .

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app. api.main:app", "--host", "0.0.0.0", "--port", "8000"]