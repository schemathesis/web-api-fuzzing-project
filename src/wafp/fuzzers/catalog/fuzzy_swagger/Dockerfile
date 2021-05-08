FROM python:3.6.13-slim

LABEL name="Fuzzy-swagger"

RUN apt-get update \
    && apt-get install -y git \
    && git clone https://github.com/namuan/fuzzy-swagger.git /app \
    && cd /app \
    && git checkout d8ec5eed70c9ac6771592e608ac9620223c940de \
    && apt remove -y git \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install openapi-spec-validator==0.3.0 swagger-spec-validator==2.7.3
RUN pip install .

ENTRYPOINT ["python", "-m", "local_main.py"]
