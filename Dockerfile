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


FROM selenium/standalone-firefox:latest as prod

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && rm requirements.txt

# Copy source code
COPY ./app /app
RUN rm -r /app/models
COPY ./models /models

# Run the app
CMD ["python", "/app/main.py"]
