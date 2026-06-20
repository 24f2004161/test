from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import math

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

with open("telemetry.json", "r") as f:
    telemetry = json.load(f)


class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float


def p95(values):
    values = sorted(values)
    index = math.ceil(0.95 * len(values)) - 1
    return values[index]


@app.post("/")
def analytics(req: RequestBody):

    result = {}

    for region in req.regions:

        rows = [r for r in telemetry if r["region"] == region]

        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime_pct"] for r in rows]

        result[region] = {
            "avg_latency": round(sum(latencies) / len(latencies), 2),
            "p95_latency": round(p95(latencies), 2),
            "avg_uptime": round(sum(uptimes) / len(uptimes), 3),
            "breaches": sum(
                1 for x in latencies if x > req.threshold_ms
            )
        }

    return result
