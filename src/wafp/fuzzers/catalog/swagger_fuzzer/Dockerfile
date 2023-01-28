FROM python:3.5-slim

ARG repository=https://github.com/Lothiraldan/swagger-fuzzer.git
ARG revision=b0d2ab9298bdd7f8c39c2d6ee449c70d44b1b472

LABEL name="Swagger-Fuzzer"

RUN apt-get update \
    && apt-get install -y git \
    && git clone $repository /app \
    && cd /app \
    && git checkout $revision \
    && apt remove -y git \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install "hypothesis[datetime]==3.55.1" furl==2.1.2 swagger_spec_validator==2.7.3 requests==2.25.1

ENTRYPOINT ["python", "-m", "swagger_fuzzer.swagger_fuzzer"]
