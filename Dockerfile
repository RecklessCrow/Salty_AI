FROM python:3.10-slim-buster

# Install Firefox and Geckodriver
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl firefox-esr\
 && rm -fr /var/lib/apt/lists/* \
 && curl -L https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz | tar xz -C /usr/local/bin \
 && apt-get purge -y ca-certificates curl

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && rm requirements.txt

# Copy source code
COPY ./app /app
COPY ./models /models

# Run the app
CMD ["python", "/app/main.py"]
