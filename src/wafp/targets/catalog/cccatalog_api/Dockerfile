FROM python:3.7-stretch

ENV PYTHONBUFFERED 1

RUN apt-get update \
    && apt-get install -y git libexempi3 \
    && mkdir -p /var/log/cccatalog-api/cccatalog-api.log \
    && git clone https://github.com/creativecommons/cccatalog-api.git \
    && cd cccatalog-api \
    && git checkout 87bf3f702170483f3576e004162f68191c6654df

WORKDIR /cccatalog-api/cccatalog-api

# Install Python dependency management tools
RUN pip install --upgrade pip \
    && pip install --upgrade setuptools \
    && pip install --upgrade pipenv

# Install the dependencies system-wide
RUN pipenv install --deploy --system --dev

# Sentry integration
RUN pip install --upgrade 'sentry-sdk'
ENV SENTRY_DSN $SENTRY_DSN
ENV WAFP_RUN_ID $WAFP_RUN_ID
ENV WAFP_FUZZER_ID $WAFP_FUZZER_ID
ENV PYTHONPATH /cccatalog-api/cccatalog-api
COPY sitecustomize.py /cccatalog-api/cccatalog-api

ENTRYPOINT ["./run.sh"]
