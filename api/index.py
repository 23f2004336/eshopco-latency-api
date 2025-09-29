# api/index.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
import os
import json
import numpy as np

app = FastAPI(debug=True)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Pydantic model for request validation
class CheckRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

@app.post("/")
def check(data: CheckRequest):
    regions = data.regions
    threshold_ms = data.threshold_ms

    # Load telemetry data
    file_path = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")
    with open(file_path, "r") as f:
        telemetry = json.load(f)

    result = {}

    for region in regions:
        region_entries = [e for e in telemetry if e["region"] == region]
        count = len(region_entries)
        if count == 0:
            result[region] = {"avg_latency": 0, "p95": 0, "avg_uptime": 0, "breaches": 0}
            continue

        latency_sum = sum(e["latency_ms"] for e in region_entries)
        uptime_sum = sum(e["uptime_pct"] for e in region_entries)
        breaches = sum(1 for e in region_entries if e["latency_ms"] > threshold_ms)
        region_latencies = [e["latency_ms"] for e in region_entries]
        p95 = np.percentile(region_latencies, 95)

        result[region] = {
            "avg_latency": round(latency_sum / count, 2),
            "p95": round(p95, 2),
            "avg_uptime": round(uptime_sum / count, 2),
            "breaches": breaches
        }

    return {"regions": result}

# Local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
