import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
from typing import List

app = FastAPI()

# Enable CORS for POST requests from any origin, as required.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Determine the path to the data file, which is in the same directory.
data_file_path = os.path.join(os.path.dirname(__file__), 'q-vercel-latency.json')

# Load the data from the JSON file into a pandas DataFrame.
try:
    df = pd.read_json(data_file_path)
except Exception:
    df = pd.DataFrame()

# Define the structure of the incoming POST request body.
class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

@app.get("/api/hello")
def read_root():
    # A simple endpoint to test if the deployment is working.
    return {"message": "Vercel Latency API is running!"}

@app.post("/api/latency")
def get_latency_metrics(request: LatencyRequest):
    """
    Accepts a POST request and returns per-region metrics.
    """
    if df.empty:
        return {"error": "Data file could not be loaded."}

    # Filter the DataFrame for the regions specified in the request.
    filtered_df = df[df['region'].isin(request.regions)]

    if filtered_df.empty:
        return {}

    # Define a function to calculate the 95th percentile.
    def p95(x):
        return np.percentile(x, 95)

    # Define a function to count latency breaches.
    def count_breaches(x):
        return (x > request.threshold_ms).sum()

    # Group the data by region and calculate all the required metrics.
    result = filtered_df.groupby('region').agg(
        avg_latency=('latency_ms', 'mean'),
        p95_latency=('latency_ms', p95),
        avg_uptime=('uptime_pct', 'mean'),
        breaches=('latency_ms', count_breaches)
    ).reset_index()
    
    # Convert integer columns to standard int type for clean JSON.
    result['breaches'] = result['breaches'].astype(int)

    # Format the output as a dictionary keyed by region.
    return result.set_index('region').to_dict(orient='index')