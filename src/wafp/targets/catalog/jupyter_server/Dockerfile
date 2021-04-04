FROM python:3.8.6-slim

LABEL name="jupyter-server"

RUN apt-get update \
    && groupadd test \
    && useradd --gid test --create-home --home-dir /home/test test \
    && apt-get install -y git \
    && git clone https://github.com/jupyter-server/jupyter_server.git /app \
    && chown test -R /app \
    && cd /app \
    && git checkout fad6c970949503d99658b583d7ac13c8d6e58973 \
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
RUN pip install --upgrade 'sentry-sdk'
ENV SENTRY_DSN $SENTRY_DSN
ENV WAFP_RUN_ID $WAFP_RUN_ID
ENV PYTHONPATH /app
COPY sitecustomize.py /app

USER test

EXPOSE 8888
CMD ["jupyter", "server", "--port=8888", "--no-browser", "--ip=0.0.0.0"]
