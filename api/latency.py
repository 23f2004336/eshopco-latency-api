from http.server import BaseHTTPRequestHandler
import json
import numpy as np
import os

# Load telemetry data
TELEMETRY_DATA = [
    {"region": "apac", "service": "payments", "latency_ms": 138.06, "uptime_pct": 99.085, "timestamp": 20250301},
    {"region": "apac", "service": "analytics", "latency_ms": 149.06, "uptime_pct": 98.246, "timestamp": 20250302},
    {"region": "apac", "service": "recommendations", "latency_ms": 143.35, "uptime_pct": 98.509, "timestamp": 20250303},
    {"region": "apac", "service": "payments", "latency_ms": 173.73, "uptime_pct": 98.931, "timestamp": 20250304},
    {"region": "apac", "service": "checkout", "latency_ms": 183.52, "uptime_pct": 98.718, "timestamp": 20250305},
    {"region": "apac", "service": "analytics", "latency_ms": 166.83, "uptime_pct": 98.63, "timestamp": 20250306},
    {"region": "apac", "service": "recommendations", "latency_ms": 219.12, "uptime_pct": 98.0, "timestamp": 20250307},
    {"region": "apac", "service": "recommendations", "latency_ms": 229.48, "uptime_pct": 98.508, "timestamp": 20250308},
    {"region": "apac", "service": "recommendations", "latency_ms": 213.66, "uptime_pct": 97.982, "timestamp": 20250309},
    {"region": "apac", "service": "checkout", "latency_ms": 126.44, "uptime_pct": 97.74, "timestamp": 20250310},
    {"region": "apac", "service": "recommendations", "latency_ms": 192.86, "uptime_pct": 97.743, "timestamp": 20250311},
    {"region": "apac", "service": "analytics", "latency_ms": 188.47, "uptime_pct": 97.197, "timestamp": 20250312},
    {"region": "emea", "service": "payments", "latency_ms": 142.82, "uptime_pct": 98.626, "timestamp": 20250301},
    {"region": "emea", "service": "checkout", "latency_ms": 198.36, "uptime_pct": 99.489, "timestamp": 20250302},
    {"region": "emea", "service": "support", "latency_ms": 171.29, "uptime_pct": 99.248, "timestamp": 20250303},
    {"region": "emea", "service": "analytics", "latency_ms": 198.41, "uptime_pct": 99.474, "timestamp": 20250304},
    {"region": "emea", "service": "payments", "latency_ms": 207.24, "uptime_pct": 97.453, "timestamp": 20250305},
    {"region": "emea", "service": "support", "latency_ms": 202.41, "uptime_pct": 97.937, "timestamp": 20250306},
    {"region": "emea", "service": "checkout", "latency_ms": 182.44, "uptime_pct": 98.623, "timestamp": 20250307},
    {"region": "emea", "service": "payments", "latency_ms": 116.61, "uptime_pct": 99.323, "timestamp": 20250308},
    {"region": "emea", "service": "catalog", "latency_ms": 147.46, "uptime_pct": 97.929, "timestamp": 20250309},
    {"region": "emea", "service": "recommendations", "latency_ms": 161.43, "uptime_pct": 97.944, "timestamp": 20250310},
    {"region": "emea", "service": "catalog", "latency_ms": 164.76, "uptime_pct": 98.624, "timestamp": 20250311},
    {"region": "emea", "service": "payments", "latency_ms": 160.09, "uptime_pct": 97.523, "timestamp": 20250312},
    {"region": "amer", "service": "support", "latency_ms": 141.85, "uptime_pct": 97.148, "timestamp": 20250301},
    {"region": "amer", "service": "payments", "latency_ms": 157.58, "uptime_pct": 99.299, "timestamp": 20250302},
    {"region": "amer", "service": "support", "latency_ms": 221.43, "uptime_pct": 98.792, "timestamp": 20250303},
    {"region": "amer", "service": "catalog", "latency_ms": 206.46, "uptime_pct": 98.906, "timestamp": 20250304},
    {"region": "amer", "service": "analytics", "latency_ms": 215.87, "uptime_pct": 99.499, "timestamp": 20250305},
    {"region": "amer", "service": "checkout", "latency_ms": 138.99, "uptime_pct": 97.585, "timestamp": 20250306},
    {"region": "amer", "service": "support", "latency_ms": 166.9, "uptime_pct": 98.67, "timestamp": 20250307},
    {"region": "amer", "service": "catalog", "latency_ms": 152.33, "uptime_pct": 98.223, "timestamp": 20250308},
    {"region": "amer", "service": "payments", "latency_ms": 196.2, "uptime_pct": 97.478, "timestamp": 20250309},
    {"region": "amer", "service": "checkout", "latency_ms": 228.45, "uptime_pct": 99.101, "timestamp": 20250310},
    {"region": "amer", "service": "checkout", "latency_ms": 146.98, "uptime_pct": 98.88, "timestamp": 20250311},
    {"region": "amer", "service": "catalog", "latency_ms": 206.62, "uptime_pct": 98.808, "timestamp": 20250312},
]

class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            request_data = json.loads(body)
            
            regions = request_data.get('regions', [])
            threshold_ms = request_data.get('threshold_ms', 0)
            
            result = {}
            
            for region in regions:
                entries = [e for e in TELEMETRY_DATA if e['region'] == region]
                
                if not entries:
                    result[region] = {
                        'avg_latency': 0,
                        'p95_latency': 0,
                        'avg_uptime': 0,
                        'breaches': 0
                    }
                    continue
                
                latency_list = [e['latency_ms'] for e in entries]
                uptime_list = [e['uptime_pct'] for e in entries]
                breaches = sum(1 for e in entries if e['latency_ms'] > threshold_ms)
                
                result[region] = {
                    'avg_latency': round(sum(latency_list) / len(latency_list), 2),
                    'p95_latency': round(np.percentile(latency_list, 95), 2),
                    'avg_uptime': round(sum(uptime_list) / len(uptime_list), 2),
                    'breaches': breaches
                }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())