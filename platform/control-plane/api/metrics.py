from prometheus_client import Counter, Histogram, generate_latest
from fastapi import APIRouter, Response

router = APIRouter()

REQUEST_COUNT = Counter(
    "aurora_requests_total",
    "Total number of HTTP requests",
    ["method", "path"],
)

REQUEST_LATENCY = Histogram(
    "aurora_request_latency_seconds",
    "Request latency in seconds",
)

ERROR_COUNT = Counter(
    "aurora_errors_total",
    "Total number of failed requests",
    ["path"],
)

@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")

