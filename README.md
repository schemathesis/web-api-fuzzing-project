# Web API Fuzzing Project (WAFP)

The WAFP project is a test suite for evaluating various characteristics of Web API fuzzers.
WAFP is fully runnable as a CLI tool that spins up fuzzing targets & runs fuzzers against them.

## Fuzzing targets

Every fuzzing target is a web application that runs via `docker-compose`. WAFP provides an API on top of
`docker-compose` that allows fuzzers to work with targets in a unified fashion.

A target is represented as a directory with at least two components:

- `__init__.py` file. Contains target's Python API & metadata;
- `docker-compose.yml` file. Docker-compose project for the target.

But generally, there could be any dependencies needed to build a `docker-compose` project.
All available targets are located in `src/wafp/targets/catalog`.
