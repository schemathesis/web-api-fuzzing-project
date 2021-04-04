FROM rust:1.48-slim as builder

RUN apt-get update \
    && apt-get install -y git \
    && git clone https://github.com/rtyler/otto.git /app \
    && cd /app \
    && git checkout 504d49884649b658dbce8828390a4e0b81450ad1 \
    && apt remove -y git \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/services/parser

RUN sed -i 's/localhost/0.0.0.0/g' src/main.rs
RUN cargo build --release

FROM debian:buster-slim

COPY --from=builder /app/target/release/otto-parser /app/

ENTRYPOINT ["/app/otto-parser"]
