# Container for packages that need to be built from source but have massive dev dependencies.
FROM python:3.7.9-slim-buster as builder

LABEL name="opentopodata-builder"

RUN set -e && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        python3.7-dev

RUN pip wheel --wheel-dir=/root/wheels uwsgi==2.0.19.1 && \
    pip wheel --wheel-dir=/root/wheels regex==2020.11.13

# The actual container.
FROM python:3.7.9-slim-buster

LABEL name="opentopodata"

RUN set -e \
    && apt-get update \
    && groupadd test \
    && useradd --gid test --create-home --home-dir /home/test test \
    && apt-get install -y --no-install-recommends git nginx memcached supervisor \
    && git clone --depth 1 https://github.com/ajnisbet/opentopodata.git /app \
    && chown test -R /app \
    && cd /app \
    && git fetch --depth 1 origin 3f6c20efb737c4b054a3407256e119cd8050fca8 \
    && git checkout 3f6c20efb737c4b054a3407256e119cd8050fca8 \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/wheels /root/wheels
RUN pip install \
        --no-index \
        --no-cache-dir \
        --disable-pip-version-check \
        --find-links=/root/wheels \
        uwsgi regex && \
    pip install --no-cache-dir --disable-pip-version-check -r /app/requirements.txt && \
        rm -rf /root/.cache/pip/* && \
        rm root/wheels/* && \
        rm /app/requirements.txt

WORKDIR /app

RUN echo > /etc/nginx/sites-available/default && \
    cp /app/docker/nginx.conf /etc/nginx/conf.d/nginx.conf && \
    cp /app/docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Sentry integration
RUN pip install --upgrade 'sentry-sdk[flask]'
ENV SENTRY_DSN $SENTRY_DSN
ENV WAFP_RUN_ID $WAFP_RUN_ID
ENV PYTHONPATH /app
COPY sitecustomize.py /app

CMD ["sh", "/app/docker/run.sh"]
EXPOSE 5000
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
