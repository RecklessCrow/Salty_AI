FROM python:3.10

ARG SALTYBET_USERNAME
ARG SALTYBET_PASSWORD
ARG PG_DSN
ARG MODEL_PATH="./app/models/model.onnx"

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

COPY ./app ./app

CMD python ./app/main.py