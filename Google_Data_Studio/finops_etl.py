import os
import requests
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

KUBECOST_URL = os.getenv("KUBECOST_URL", "http://kubecost-cost-analyzer.kubecost.svc.cluster.local:9090/model/allocation")
DB_URL = os.getenv("DB_URL", "postgresql://quant_user:password@postgres:5432/quantdb")

response = requests.get(f"{KUBECOST_URL}?window=today&aggregate=namespace")
data = response.json()

records = []
current_date = datetime.utcnow().date()

for item in data.get("data", []):
    for namespace, metrics in item.items():
        records.append({
            "date": current_date,
            "namespace": namespace,
            "total_cost": metrics.get("totalCost", 0.0),
            "cpu_cost": metrics.get("cpuCost", 0.0),
            "ram_cost": metrics.get("ramCost", 0.0),
            "gpu_cost": metrics.get("gpuCost", 0.0)
        })

df = pd.DataFrame(records)

engine = create_engine(DB_URL)
df.to_sql("finops_daily_costs", engine, if_exists="append", index=False)