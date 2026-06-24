import os
import requests
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

KUBECOST_URL = os.getenv("KUBECOST_URL", "http://kubecost-cost-analyzer.kubecost.svc.cluster.local:9090/model/allocation")
DB_URL = os.getenv("DB_URL", "postgresql://quant_user:password@postgres:5432/quantdb")

try:
    response = requests.get(f"{KUBECOST_URL}?window=today&aggregate=namespace", timeout=10)
    data = response.json()
except Exception as e:
    print(f"Error fetching from Kubecost: {e}")
    data = {}

records = []
current_date = datetime.utcnow().date()

for item in data.get("data", []):
    if not item:
        continue
    for namespace, metrics in item.items():
        records.append({
            "date": current_date,
            "namespace": namespace,
            "total_cost": metrics.get("totalCost", 0.0),
            "cpu_cost": metrics.get("cpuCost", 0.0),
            "ram_cost": metrics.get("ramCost", 0.0),
            "gpu_cost": metrics.get("gpuCost", 0.0)
        })

if records:
    df = pd.DataFrame(records)
    engine = create_engine(DB_URL)
    df.to_sql("finops_daily_costs", engine, if_exists="append", index=False)
    print(f"Successfully inserted {len(records)} records.")
else:
    print("No cost data available for today yet. Kubecost might still be scraping metrics.")
