from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import math
import os

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Handle preflight requests
@app.options("/{path:path}")
def options(path: str):
    return Response(status_code=200)


# Optional: prevent 405 on GET /
@app.get("/")
def root():
    return {"status": "ok"}


# Load telemetry file
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FILE = os.path.join(BASE_DIR, "telemetry.json")

with open(FILE, "r") as f:
    telemetry = json.load(f)


class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float


def p95(values):
    if not values:
        return 0

    values = sorted(values)
    idx = math.ceil(0.95 * len(values)) - 1
    return values[idx]


@app.post("/")
def analytics(req: RequestBody):
    result = []

    for region in req.regions:
        rows = [r for r in telemetry if r["region"] == region]

        if not rows:
            continue

        latencies = [r["latency_ms"] for r in rows]

        # Use whichever field exists
        if "uptime_pct" in rows[0]:
            uptimes = [r["uptime_pct"] for r in rows]
        else:
            uptimes = [r["uptime"] for r in rows]

        result.append({
            "region": region,
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": p95(latencies),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(
                1 for x in latencies
                if x > req.threshold_ms
            )
        })

    return result
