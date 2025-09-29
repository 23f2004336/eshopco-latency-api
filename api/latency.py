from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
import os, json
import numpy as np

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

class CheckRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

@app.post("/")
def check(data: CheckRequest):
    file_path = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")
    with open(file_path, "r") as f:
        telemetry = json.load(f)

    result = {}
    for region in data.regions:
        entries = [e for e in telemetry if e["region"] == region]
        count = len(entries)
        if count == 0:
            result[region] = {"avg_latency": 0, "p95": 0, "avg_uptime": 0, "breaches": 0}
            continue
        latency_list = [e["latency_ms"] for e in entries]
        uptime_list = [e["uptime_pct"] for e in entries]
        breaches = sum(1 for e in entries if e["latency_ms"] > data.threshold_ms)

        result[region] = {
            "avg_latency": round(sum(latency_list)/count, 2),
            "p95": round(np.percentile(latency_list, 95), 2),
            "avg_uptime": round(sum(uptime_list)/count, 2),
            "breaches": breaches
        }
    return {"regions": result}
