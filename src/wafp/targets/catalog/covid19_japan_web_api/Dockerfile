ARG repository=https://github.com/ryo-ma/covid19-japan-web-api.git
ARG revision=2c7ff7383100c2f7e652d15388f6b46324575a31

FROM python:3.6.12-slim

LABEL name="covid19-japan-web-api"

RUN apt-get update \
    && groupadd test \
    && useradd --gid test --create-home --home-dir /home/test test \
    && apt-get install -y git \
    && git clone $repository /app \
    && chown test -R /app \
    && cd /app \
    && git checkout $revision \
    && apt remove -y git \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install pipenv
RUN /bin/bash -c "pip3 install --no-cache-dir -r <(pipenv lock -r)"

# Sentry integration
RUN pip install --upgrade 'sentry-sdk[flask]'
ENV SENTRY_DSN $SENTRY_DSN
ENV WAFP_RUN_ID $WAFP_RUN_ID
ENV WAFP_FUZZER_ID $WAFP_FUZZER_ID
ENV PYTHONPATH /app
COPY sitecustomize.py /app

USER test

RUN echo "from index import app;import os;app.run(host='0.0.0.0', port=os.environ['PORT'])" >> test.py
CMD ["python", "test.py"]
