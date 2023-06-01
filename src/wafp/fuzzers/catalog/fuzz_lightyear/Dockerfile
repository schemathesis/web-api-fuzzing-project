FROM python:3.8.6-slim

ARG repository=https://github.com/Yelp/fuzz-lightyear.git
ARG revision=e558337134ee9b938e95026708ecdc139d409327

LABEL name="fuzz-lightyear"

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

ENTRYPOINT ["fuzz-lightyear"]
