ARG repository=https://github.com/KissPeter/APIFuzzer.git
ARG revision=b786c1b96366b953fd375036f16f3a50c41d7111

FROM python:3.8.6-slim

LABEL name="APIFuzzer"

RUN apt-get update \
    && apt-get install -y git libcurl4-openssl-dev libssl-dev build-essential \
    && git clone $repository /app \
    && cd /app \
    && git checkout $revision \
    && apt remove -y git \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "fuzzer.py"]
