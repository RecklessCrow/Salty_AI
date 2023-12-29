FROM pytorch/pytorch:2.1.2-cuda12.1-cudnn8-devel as dev

USER root

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && pip install torchbnn blitz-bayesian-pytorch \
 && rm requirements.txt \

# Copy source code
WORKDIR /app

# Set dummy environment variables
COPY ./models/dummy.onnx /models/dummy.onnx
ENV MODEL_PATH="/models/dummy.onnx"
ENV FIREFOX_BIN="/models/dummy.onnx"

CMD ["python", "/app/train_model.py"]

FROM python:3.10-slim-buster as prod

USER root

# Install firefox
RUN apt-get update \
 && apt-get install -y --no-install-recommends firefox-esr \
 && rm -rf /var/lib/apt/lists/*
ENV FIREFOX_BIN="/usr/bin/firefox-esr"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && rm requirements.txt

# Copy source code
COPY ./app /app

# Copy model file into container
ENV MODEL_PATH="/models/SimpleShared-2023-12-28-15-46-30.onnx"
COPY ./models/SimpleShared-2023-12-28-15-46-30.onnx /models/SimpleShared-2023-12-28-15-46-30.onnx

# Run the app
CMD ["python", "/app/main.py"]
