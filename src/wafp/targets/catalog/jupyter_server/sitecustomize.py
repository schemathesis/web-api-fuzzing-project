import os

import sentry_sdk
from sentry_sdk.integrations.tornado import TornadoIntegration

dsn = os.environ.get("SENTRY_DSN")
run_id = os.environ.get("WAFP_RUN_ID")
fuzzer_id = os.environ.get("WAFP_FUZZER_ID")
sentry_sdk.init(
    dsn=dsn,
    integrations=[TornadoIntegration()],
)
sentry_sdk.set_tag("wafp.run-id", run_id)
if fuzzer_id is not None:
    sentry_sdk.set_tag("wafp.fuzzer-id", fuzzer_id)
print("Sentry installed!", dsn, run_id)
