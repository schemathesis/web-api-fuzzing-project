FROM python:3.8.6-slim

ARG repository=https://github.com/jupyter-server/jupyter_server.git
ARG revision=fad6c970949503d99658b583d7ac13c8d6e58973

LABEL name="jupyter-server"

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

ENV TINI_VERSION v0.6.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini
RUN chmod +x /usr/bin/tini
ENTRYPOINT ["/usr/bin/tini", "--"]

WORKDIR /app
RUN pip install .
RUN pip install tornado==6.1.0

# Sentry integration
RUN pip install --upgrade 'sentry-sdk' aiocontextvars
ENV SENTRY_DSN $SENTRY_DSN
ENV WAFP_RUN_ID $WAFP_RUN_ID
ENV WAFP_FUZZER_ID $WAFP_FUZZER_ID
ENV PYTHONPATH /app
COPY sitecustomize.py /app

USER test

EXPOSE 8888
CMD ["jupyter", "server", "--port=8888", "--no-browser", "--ip=0.0.0.0"]
