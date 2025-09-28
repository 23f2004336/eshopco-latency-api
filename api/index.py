import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from typing import List, Dict

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    data_path = os.path.join(os.path.dirname(__file__), 'q-vercel-latency.json')
    with open(data_path, 'r') as f:
        telemetry_data = json.load(f)
except FileNotFoundError:
    telemetry_data = []

class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

@app.post("/api/latency")
async def get_latency_metrics(request: LatencyRequest) -> Dict:
    results = {}
    if not telemetry_data:
         return {"error": "Telemetry data could not be loaded."}
    for region in request.regions:
        region_data = [d for d in telemetry_data if d.get("region") == region]
        if not region_data:
            results[region] = "No data available"
            continue
        latencies = [d["latency_ms"] for d in region_data if "latency_ms" in d]
        uptimes = [d["uptime_pct"] for d in region_data if "uptime_pct" in d]
        if not latencies:
            results[region] = "Latency data missing for this region"
            continue
        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        avg_uptime = np.mean(uptimes)
        breaches = sum(1 for latency in latencies if latency > request.threshold_ms)
        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 3),
            "breaches": breaches
        }
    return results

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Latency API is running."}