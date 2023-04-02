FROM python:3.10

ENV SALTYBET_USERNAME=None
ENV SALTYBET_PASSWORD=None
ENV PG_DSN=None

WORKDIR ./workspace

# Install firefox driver
RUN apt-get update                             \
 && apt-get install -y --no-install-recommends ca-certificates curl firefox-esr \
 && rm -fr /var/lib/apt/lists/*                \
 && curl -L https://github.com/mozilla/geckodriver/releases/download/v0.32.1/geckodriver-v0.32.1-linux64.tar.gz | tar xz -C /usr/local/bin \
 && apt-get purge -y ca-certificates curl

# Install python requirements
COPY requirements/deploy.txt .
RUN pip install --upgrade pip \
 && pip install -r ./deploy.txt

# Move over files
COPY ./app ./app
COPY ./models ./models
ENV MODEL_PATH="./models/2023.04.02-07.20.onnx"


CMD python ./app/main.py