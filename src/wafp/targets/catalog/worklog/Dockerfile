FROM python:3.7-alpine

COPY requirements.txt frozen-requirements.txt
RUN apk add --no-cache git gcc g++ make libffi-dev openssl-dev \
    && git clone https://github.com/IBM/worklog.git /app \
    && cd /app \
    && git checkout 14a176ef233c7996a37fcb24e72d5e2f03993f9a \
    && pip install --no-cache-dir -r /frozen-requirements.txt \
    && apk del git gcc g++ make

WORKDIR /app

# Sentry integration
ENV SENTRY_DSN $SENTRY_DSN
ENV WAFP_RUN_ID $WAFP_RUN_ID
ENV WAFP_FUZZER_ID $WAFP_FUZZER_ID
ENV PYTHONPATH /app
COPY sitecustomize.py /app

CMD ["python", "-m", "app.__init__"]
