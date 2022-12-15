ARG repository=https://github.com/microsoft/restler-fuzzer.git
ARG revision=a0ba706a2156e31cf6053b639b57aa1b9acad442

FROM mcr.microsoft.com/dotnet/core/sdk:3.1-alpine AS builder

RUN apk add --no-cache git python3 \
    && git clone $repository /app \
    && cd /app \
    && git checkout $revision \
    && apk del git

WORKDIR /app

RUN ln -s /usr/bin/python3 /usr/bin/python

RUN python3 /app/build-restler.py --dest_dir /restler
RUN python3 -m compileall -b /restler/engine

FROM mcr.microsoft.com/dotnet/core/aspnet:3.1-alpine

RUN apk add --no-cache python3
RUN python3 -m ensurepip
RUN pip3 install --upgrade pip
RUN pip3 install requests
RUN ln -s /usr/bin/python3 /usr/bin/python

COPY --from=builder /restler/compiler /RESTler/compiler
COPY --from=builder /restler/restler /RESTler/restler
COPY --from=builder /restler/engine /RESTler/engine
COPY --from=builder /restler/resultsAnalyzer /RESTler/resultsAnalyzer

COPY entrypoint.sh /

ENTRYPOINT ["./entrypoint.sh"]
