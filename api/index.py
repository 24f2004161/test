from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import math
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
with open(os.path.join(BASE_DIR, "telemetry.json")) as f:
    telemetry = json.load(f)


class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float


def p95(values):
    values = sorted(values)
    if not values:
        return 0
    return values[math.ceil(0.95 * len(values)) - 1]


@app.post("/")
def analytics(req: RequestBody):
    result = []

    for region in req.regions:
        rows = [r for r in telemetry if r["region"] == region]

        if not rows:
            continue

        latencies = [r["latency_ms"] for r in rows]

        uptime_key = (
            "uptime_pct"
            if "uptime_pct" in rows[0]
            else "uptime"
        )
        uptimes = [r[uptime_key] for r in rows]

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
