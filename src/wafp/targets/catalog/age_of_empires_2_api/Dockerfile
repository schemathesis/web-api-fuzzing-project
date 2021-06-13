FROM python:3.7-slim AS source

LABEL name="age_of_empires_2_api"

RUN apt-get update \
    && groupadd test \
    && useradd --gid test --create-home --home-dir /home/test test \
    && apt-get install -y git \
    && git clone https://github.com/aalises/age-of-empires-II-api.git /app-tmp \
    && chown test -R /app-tmp \
    && cd /app-tmp \
    && git checkout 6bd9f29933382838a0e5b7b16f0e318ec6d312a6 \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

FROM tiangolo/uwsgi-nginx-flask:python3.7

COPY --from=source /app-tmp/ /app/

RUN ls -lh /app/
# Pinned dependencies
COPY requirements.txt /
RUN pip install -r /requirements.txt

# Sentry integration
RUN pip install --upgrade 'sentry-sdk[flask]'
ENV SENTRY_DSN $SENTRY_DSN
ENV WAFP_RUN_ID $WAFP_RUN_ID
ENV WAFP_FUZZER_ID $WAFP_FUZZER_ID
ENV PYTHONPATH /app
COPY sitecustomize.py /app
