FROM python:3.6.12-stretch

LABEL name="pslab-webapp"

RUN apt-get update \
    && groupadd test \
    && useradd --gid test --create-home --home-dir /home/test test \
    && apt-get install -y git libpq-dev \
    && git clone https://github.com/fossasia/pslab-webapp.git /app \
    && chown test -R /app \
    && cd /app \
    && git checkout 624e56fcae939b11e4e671e0fbde816a9e17162c \
    && apt remove -y git \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# Default `requirements.txt` file doesn't have dependencies properly locked
COPY requirements.txt requirements-pinned.txt
RUN pip install -r requirements-pinned.txt


# Sentry integration
RUN pip install --upgrade 'sentry-sdk[flask]'
ENV SENTRY_DSN $SENTRY_DSN
ENV WAFP_RUN_ID $WAFP_RUN_ID
ENV PYTHONPATH /app
COPY sitecustomize.py /app

USER test

COPY run.py backend/run.py

CMD ["python", "backend/run.py"]
