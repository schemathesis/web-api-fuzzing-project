FROM maven:3.6.3-jdk-8-slim

LABEL name="Cats"

RUN apt-get update \
    && groupadd test \
    && useradd --gid test --create-home --home-dir /home/test test \
    && apt-get install -y git \
    && git clone https://github.com/Endava/cats.git /app \
    && chown test -R /app \
    && cd /app \
    && git checkout e8dc1e1a90a6a3e0634debadf3d2ba22702fe524 \
    && apt remove -y git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

USER test

RUN mvn clean package && chmod +x cats.jar

ENTRYPOINT ["./cats.jar"]
