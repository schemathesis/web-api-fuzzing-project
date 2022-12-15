ARG repository=https://github.com/Teebytes/TnT-Fuzzer.git
ARG revision=c1b333ced51d515e45827d7817a8004cadb98d45

FROM python:3.8.6-alpine

LABEL name="TnT-Fuzzer"

RUN apk add --no-cache git \
    # The latest PyPI release is outdated - Python 2 only
    # Therefore building it manually, similarly to their Dockerfile
    # https://github.com/Teebytes/TnT-Fuzzer/blob/master/Dockerfile
    && git clone $repository /app \
    && cd /app \
    && git checkout $revision \
    && git clone https://github.com/mseclab/PyJFuzz.git \
    && cd PyJFuzz \
    && git checkout f777067076f62c9ab74ffea6e90fd54402b7a1b4 \
    && python setup.py install \
    && cd .. \
    && rm -rf PyJFuzz \
    && pip install -r requirements.txt \
    && apk del git

WORKDIR /app

ENTRYPOINT ["python", "tntfuzzer/tntfuzzer.py"]
