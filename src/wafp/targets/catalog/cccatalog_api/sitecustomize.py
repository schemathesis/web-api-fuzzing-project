from gevent import monkey

monkey.patch_all()

import os  # pylint: disable=wrong-import-order

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

dsn = os.environ.get("SENTRY_DSN")
run_id = os.environ.get("WAFP_RUN_ID")
sentry_sdk.init(
    dsn=dsn,
    integrations=[DjangoIntegration()],
)
sentry_sdk.set_tag("wafp.run-id", run_id)
print("Sentry installed!", dsn, run_id)
