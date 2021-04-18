FROM python:3.8.6-slim

LABEL name="fuzz-lightyear"

RUN apt-get update \
    && apt-get install -y git \
    && git clone https://github.com/Yelp/fuzz-lightyear.git /app \
    && cd /app \
    && git checkout e558337134ee9b938e95026708ecdc139d409327 \
    && apt remove -y git \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install .

ENTRYPOINT ["fuzz-lightyear"]
