# Web API Fuzzing Project (WAFP)

The WAFP project is a test suite for evaluating various characteristics of Web API fuzzers.
WAFP is fully runnable as a CLI tool that spins up fuzzing targets & runs fuzzers against them.

## Citation

If you use WAFP in research, please cite our paper
[*Deriving Semantics-Aware Fuzzers from Web API Schemas*](https://arxiv.org/abs/2112.10328)
by Zac Hatfield-Dodds (@Zac-HD) and Dmitry Dygalo (@Stranger6667) - we built it to
evaluate Schemathesis, it's designed to be extensible.  Our goal was to make future
studies as easy -- and easy to compare -- as possible.

Use it as-is, or extend it and contribute new tools, targets, or integrations
back to our repo so that others can benefit from your hard work!

If you just want to grab results, see Zenodo: [unprocessed data (23 GB)](https://zenodo.org/record/5339649)
and [processed data (263 MB)](https://zenodo.org/record/5392010).

## Installation

WAFP is built around Docker and is tested against the `20.10.0` version. Check [the official Docker docs](https://docs.docker.com/get-docker/) for installation guide.
Other dependencies are managed via `poetry` (check out the [installation guide](https://github.com/sdispater/poetry#installation)):

```
poetry install
```

It also automatically installs WAFP CLI to the current environment that is available via the `wafp` entry point.

## Getting started

To run a fuzzer against a target, you need to pass their names in CLI:

```
wafp schemathesis:Default jupyter_server --output-dir=./artifacts
```

The command above will run the `Default` variant of Schemathesis against the Jupyter Server target and will store
all available artifacts in the `./artifacts` directory.

Alternatively you can run it via ``poetry``:

```
poetry run wafp schemathesis:Default jupyter_server --output-dir=./artifacts
```

If you want to run the whole suite, use the `run.py` script:

```
python run.py --output-dir=./artifacts --iterations=30
```

It will run all the defined combinations for 30 times and store the artifacts in the `./artifacts` directory.
The combinations are defined in the `COMBINATIONS` variable in the `run.py` file. It excludes combinations that are known
to not work for some reason (usually due to fuzzer failures).

Note, that the `run.py` file does not include the Sentry integration (see below).

## Fuzzing targets

Every fuzzing target is a web application that runs via `docker-compose`. WAFP provides an API on top of
`docker-compose` that allows fuzzers to work with targets in a unified fashion.

A target is represented as a directory with at least two components:

- `__init__.py` file. Contains target's Python API & metadata;
- `docker-compose.yml` file. Docker-compose project for the target.

But generally, there could be any dependencies needed to build a `docker-compose` project.
All available targets are located in `src/wafp/targets/catalog`.

You can run targets with the following command (replace `<target-name>` with any target name from the catalog):

```
python -m wafp.targets <target-name> --output-dir=./artifacts
```

### Target structure

Python API for a target consists of one or more classes inherited from `wafp.targets.BaseTarget`. Each class requires
implementing at least four methods:

- `get_base_url`. Service base URL. All URLs used in API calls will extend this value;
- `get_schema_location`. URL or a filesystem path to the API schema;
- `is_ready`. Detects whether the target is ready for fuzzing. It is called on each stdout line emitted by the `docker-compose` stack;
- `get_metadata`. Describes the programming language, API schema type, and other meta information.

Targets are parametrized with TCP ports, and by default, they start working on a random port that is available via the `port` attribute.

Here is an example of the `httpbin` target:

```python
from wafp.targets import BaseTarget, Metadata


class Default(BaseTarget):
    def get_base_url(self) -> str:
        # A common case that has no additional path
        return f"http://0.0.0.0:{self.port}/"

    def get_schema_location(self) -> str:
        return f"http://0.0.0.0:{self.port}/spec.json"

    def is_ready(self, line: bytes) -> bool:
        return b"Listening at: " in line

    def get_metadata(self) -> Metadata:
        return Metadata.flasgger(
            flask_version="1.0.2",
            flasgger_version="0.9.0",
            openapi_version="2.0",
            validation_from_schema=False,
        )
```

Docker-compose:

```
version: '3'
services:
  web:
    build:
      context: https://github.com/postmanlabs/httpbin.git#f8ec666b4d1b654e4ff6aedd356f510dcac09f83
    init: true
    environment:
      - PORT=3000
    ports:
      - '${PORT-3000}:80'
```

Compose files should support the `PORT` environment variable and provide a proper port mapping.

Running the target from the example above:

```python
target = Default()
target.start()
# ... Run fuzzing ...
target.stop()
target.cleanup()
```

Some targets may require additional actions to be prepared for fuzzing, for example, creating a user and getting credentials.
You can extract headers from `docker-compose` output via the `get_headers` method:

```python
import re
...

class Default(BaseTarget):
    ...
    def get_headers(self, line: bytes) -> Dict[str, str]:
        match = re.search(b"token=(.+)", line)
        if match is None:
            return {}
        token = match.groups()[0]
        return {"Authorization": f"token {token.decode()}"}
```

Credentials can be obtained in the `after_start` hook. At this moment, the target is ready to accept network requests:

```python
import requests
...

class Default(BaseTarget):
    ...
    def after_start(self, stdout: bytes, headers: Dict[str, str]) -> None:
        base_url = self.get_base_url()
        # Authorize & get the token
        response = requests.post(
            f"{base_url}/authorizations/token",
            json={"username": "root", "password": "test"}
        )
        token = response.json()["token"]
        headers["Authorization"] = f"token {token}"
```

### Sentry integration

Some targets provide Sentry integration, and it is possible to collect all errors reported during a fuzzing run.
To enable the integration, you need to pass the `sentry_dsn` argument during the target initialization or provide the `--sentry-dsn` CLI option.
To collect errors from the used Sentry instance you need to provide more info:

```python
# Target initialization
target = target.Default(
    sentry_dsn="https://c4715cd284cf4f509c32e49f27643f30@sentry.company.com/42"
)
# Load all artifacts including errors reported to Sentry
artifacts = target.collect_artifacts(
    # Your Sentry instance base URL
    sentry_url="https://sentry.company.com",
    # Sentry access token
    sentry_token="7a7d025aafe34326b789356b62d2b6dc01af594c33ca48a3a0f76421a137ef9a",
    # The slug of the organization the target project belongs to
    sentry_organization="my_org",
    # The slug of the project
    sentry_project="target",
)
```

The `artifacts` variable will contain container logs and Sentry events as Python dictionaries wrapped into the `Artifact` class.

WAFP uses the `GET /api/0/projects/{organization_slug}/{project_slug}/events/` endpoint to retrieve events data.
See more info in Sentry documentation - https://docs.sentry.io/api/events/list-a-projects-events/

If you'd like to use the `run.py` file to run all combinations, you'll need to add `sentry_dsn` keys to the desired combinations in the `COMBINATIONS` variable in the `run.py` file.

As Sentry does not process events immediately, you'll need to download them separately, when the processing is done in your Sentry instance.

To load the events you need the latest stable Rust version (see the [rustup](https://rustup.rs/) docs for the installation instructions) and run the following command in the `sentry_events` directory:

```
cargo run --release <path-to-artifacts> --token <your Sentry API token> --url <your Sentry instance URL>
```

It will load all the events relevant to the artifacts and store them in the same artifacts directory. Note, it might take a while to download all the events.

## Fuzzers

API fuzzers are also run via `docker-compose` and are available via a similar interface:

```
python -m wafp.fuzzers schemathesis:Default \
  --schema=<Schema file or URL> \
  --base-url=<Service base URL> \
  --output-dir=./artifacts
```

Each fuzzer can be represented as one or more variants - you can have different running modes as different variants.
For example, there are four different variants for Schemathesis:

- `schemathesis:Default` - checks only for 5xx HTTP response codes
- `schemathesis:AllChecks` - runs all available checks
- `schemathesis:StatefulOld` - additionally execute stateful tests via Schemathesis's deprecated approach
- `schemathesis:StatefulNew` - utilizes the state-machine-based stateful testing

Fuzzers' names are derived from Python packages they are in - you can find them in the `./src/wafp/fuzzers/catalog` directory.

## Artifacts processing

To process the artifacts you need the latest stable Rust version (see the [rustup](https://rustup.rs/) docs for the installation instruction).

Run the following command in the `postprocessing` directory:

```
cargo run --release <path-to-artifacts> <output-directory>
```

The output directory will have the same top-level structure as the input one. Sub-directories named by the following pattern - `<fuzzer>-<target>-<iteration-number>`. Then, each directory may have the following files:

- `metadata.json`. Metadata about a test run - tested fuzzer name, run duration, etc
- `fuzzer.json` - Structured fuzzer output
- `deduplicated_cases.json` - Deduplicated reported failures, when fuzzers provide it
- `sentry.json` - Cleaned Sentry events for this run
- `target.json` - Parsed stdout for Gitlab & Disease.sh targets that are tested without Sentry integration

## Related projects

- [HypoFuzz](https://hypofuzz.com/). Putting smart fuzzing into the world's best testing workflow for Python. HypoFuzz runs your property-based test suite, using cutting-edge fuzzing techniques and coverage instrumentation to find even the rarest inputs which trigger an error.
- [Schemathesis.io](https://schemathesis.io/). A modern API testing tool that allows you to find bugs faster without leaving your browser. Schemathesis.io be available soon!
