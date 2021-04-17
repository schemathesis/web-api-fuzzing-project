# Web API Fuzzing Project (WAFP)

The WAFP project is a test suite for evaluating various characteristics of Web API fuzzers.
WAFP is fully runnable as a CLI tool that spins up fuzzing targets & runs fuzzers against them.
The project started as an evaluation suite for the `Property-Based Testing of Web APIs` academic paper by Zac Hatfield-Dodds (@Zac-HD) and Dmitry Dygalo (@Stranger6667).

## Installation

WAFP is built around Docker and is tested against the `20.10.0` version. Check [the official Docker docs](https://docs.docker.com/get-docker/) for installation guide.
Other dependencies are managed via `poetry` (check out the [installation guide](https://github.com/sdispater/poetry#installation)):

```
poetry install
```

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
python -m wafp.targets.cli <target-name>
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
