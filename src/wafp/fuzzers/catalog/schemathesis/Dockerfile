FROM schemathesis/schemathesis:v3.19.5

COPY hooks.py hooks.py

USER root
RUN apk add --no-cache git

ARG EXTRA_REQUIREMENTS=empty-requirements.txt
COPY $EXTRA_REQUIREMENTS requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

USER schemathesis
