FROM pytorch/pytorch:2.1.2-cuda12.1-cudnn8-devel as dev

USER root

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && rm requirements.txt

# Copy source code
WORKDIR /app
COPY ./app /app
COPY ./models /models


FROM python:3.10-slim-buster as prod

USER root

# Install firefox
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    firefox-esr \
 && rm -rf /var/lib/apt/lists/*
ENV FIREFOX_BIN="/usr/bin/firefox-esr"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && rm requirements.txt

# Copy source code
COPY ./app /app
COPY ./models /models
ENV MODEL_PATH="/models/2023-12-23-15-54-30.onnx"

# Run the app
CMD ["python", "/app/main.py"]
