FROM python:3.8.6-slim

ARG repository=https://github.com/olipratt/swagger-conformance.git
ARG revision=8b6fdf99fd6a1db4eb69071c1e8d8a383ebcf76f

LABEL name="swagger-conformance"

RUN apt-get update \
    && apt-get install -y git \
    && git config --global --add safe.directory /app \
    && git clone $repository /app \
    && cd /app \
    && git checkout $revision \
    && apt remove -y git \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install .

ENTRYPOINT ["python", "-m", "swaggerconformance"]
