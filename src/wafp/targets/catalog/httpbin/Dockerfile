ARG repository=https://github.com/postmanlabs/httpbin.git
ARG revision=f8ec666b4d1b654e4ff6aedd356f510dcac09f83

FROM ubuntu:18.04

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

COPY requirements.txt frozen-requirements.txt
RUN apt-get update \
    && groupadd test \
    && useradd --gid test --create-home --home-dir /home/test test \
    && apt-get install -y git python3-pip \
    && pip3 install --no-cache-dir -r /frozen-requirements.txt \
    && git clone $repository /app \
    && cd /app \
    && git checkout $revision \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Sentry integration
ENV SENTRY_DSN $SENTRY_DSN
ENV WAFP_RUN_ID $WAFP_RUN_ID
ENV WAFP_FUZZER_ID $WAFP_FUZZER_ID
ENV PYTHONPATH /app/httpbin/
COPY sitecustomize.py /app/httpbin/

EXPOSE 80

CMD ["gunicorn", "-b", "0.0.0.0:80", "httpbin:app", "-k", "gevent"]
