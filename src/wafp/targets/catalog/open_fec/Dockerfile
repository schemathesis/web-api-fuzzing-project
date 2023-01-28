FROM python:3.7.9-slim

ARG repository=https://github.com/fecgov/openFEC.git
ARG revision=ea5aa5db7e847d2de0de8be07cb1dcc029cd5a05

LABEL name="open-fec"

ENV FLYWAY_VERSION=5.2.4

RUN apt-get update \
    && groupadd test \
    && useradd --gid test --create-home --home-dir /home/test test \
    && apt-get install -y git libpq-dev build-essential python3-dev wget postgresql-client \
    && wget -qO- https://repo1.maven.org/maven2/org/flywaydb/flyway-commandline/$FLYWAY_VERSION/flyway-commandline-$FLYWAY_VERSION-linux-x64.tar.gz | tar xvz && ln -s `pwd`/flyway-$FLYWAY_VERSION/flyway /usr/local/bin \
    && git config --global --add safe.directory /app \
    && git clone --depth 1 $repository /app \
    && chown test -R /app \
    && cd /app \
    && git fetch --depth 1 origin $revision \
    && git checkout $revision \
    && apt remove -y wget \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

RUN sed -i 's/flyway.url=/flyway.url=jdbc:postgresql:\/\/db:5432\/test?user=test&password=test/g' /flyway-5.2.4/conf/flyway.conf && \
  sed -i 's/# flyway.locations=/flyway.locations=\/app\/data\/migrations/g' /flyway-5.2.4/conf/flyway.conf && \
  sed -i 's/http:\/\/localhost:9200/http:\/\/elastic:9200/g' /app/webservices/utils.py

WORKDIR /app
COPY requirements.txt frozen-requirements.txt
RUN pip install --no-cache-dir -r frozen-requirements.txt

ENV SENTRY_DSN $SENTRY_DSN
ENV WAFP_RUN_ID $WAFP_RUN_ID
ENV WAFP_FUZZER_ID $WAFP_FUZZER_ID
ENV PYTHONPATH /app
COPY sitecustomize.py /app

CMD ["gunicorn", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "-k", "gevent", "webservices.rest:app"]
