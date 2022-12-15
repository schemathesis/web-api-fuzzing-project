ARG repository=https://github.com/microsoft/restler-fuzzer.git
ARG revision=ad867673db70c6f39807a57314a89e86e2346ece

FROM python:3.8-slim

LABEL name="restler-demo"

COPY requirements.txt frozen-requirements.txt
RUN apt-get update \
    && groupadd test \
    && useradd --gid test --create-home --home-dir /home/test test \
    && apt-get install -y git \
    && git clone $repository /app \
    && pip install --no-cache-dir -r frozen-requirements.txt \
    && cd /app \
    && chown test -R /app \
    && git checkout $revision \
    && apt remove -y git \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/demo_server

ENV SENTRY_DSN $SENTRY_DSN
ENV WAFP_RUN_ID $WAFP_RUN_ID
ENV WAFP_FUZZER_ID $WAFP_FUZZER_ID
ENV PYTHONPATH /app/demo_server
COPY sitecustomize.py /app/demo_server

# Override Flask's `SERVER_NAME` config option
RUN echo "import os;FLASK_SERVER_NAME = f\"0.0.0.0:{os.environ['PORT']}\"" >> demo_server/settings.py

CMD ["python", "demo_server/app.py"]
