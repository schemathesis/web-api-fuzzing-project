FROM python:3.6.12-stretch

LABEL name="pslab-webapp"

COPY requirements.txt frozen-requirements.txt
RUN apt-get update \
    && groupadd test \
    && useradd --gid test --create-home --home-dir /home/test test \
    && apt-get install -y git libpq-dev \
    && pip install --no-cache-dir -r frozen-requirements.txt \
    && git clone https://github.com/fossasia/pslab-webapp.git /app \
    && chown test -R /app \
    && cd /app \
    && git checkout 624e56fcae939b11e4e671e0fbde816a9e17162c \
    && apt remove -y git \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Sentry integration
ENV SENTRY_DSN $SENTRY_DSN
ENV WAFP_RUN_ID $WAFP_RUN_ID
ENV WAFP_FUZZER_ID $WAFP_FUZZER_ID
ENV PYTHONPATH /app
COPY sitecustomize.py /app

USER test

COPY run.py backend/run.py

CMD ["python", "backend/run.py"]
