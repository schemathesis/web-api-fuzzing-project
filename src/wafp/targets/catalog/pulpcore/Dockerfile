FROM python:3.8.6-slim

ARG repository=https://github.com/pulp/pulpcore.git
ARG revision=af6689103fc5a6f3fad0422332ad24a1ac0fa05e

LABEL name="pulpcore"

RUN apt-get update \
    && groupadd test \
    && useradd --gid test --create-home --home-dir /home/test test \
    && apt-get install -y git libpq-dev gcc \
    && git config --global --add safe.directory /app \
    && git clone $repository /app \
    && cd /app \
    && chown test -R /app \
    && git checkout $revision \
    && apt remove -y git \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install .

# Sentry integration
RUN pip install --upgrade 'sentry-sdk'
ENV SENTRY_DSN $SENTRY_DSN
ENV WAFP_RUN_ID $WAFP_RUN_ID
ENV WAFP_FUZZER_ID $WAFP_FUZZER_ID
ENV PYTHONPATH /app
COPY sitecustomize.py /app

RUN mkdir -p /var/lib/pulp/tmp && mkdir -p /var/lib/pulp/assets/ && chown -R test /var/lib/pulp

USER test

COPY settings.py /etc/pulp/settings.py
ENV PULP_SETTINGS /etc/pulp/settings.py

ENTRYPOINT ["pulpcore-manager", "runserver"]
