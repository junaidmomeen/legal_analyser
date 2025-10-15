import os
from prometheus_fastapi_instrumentator import Instrumentator


def setup_prometheus(app) -> None:
    if os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true":
        Instrumentator().instrument(app).expose(app, include_in_schema=False)
