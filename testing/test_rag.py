import requests
import time

print("1. Στέλνω το Report στη Βάση Δεδομένων (Ingestion)...")
with open("report_for_rag.txt", "rb") as f:
    files = {"file": ("report_for_rag.txt", f, "text/plain")}
    response = requests.post("http://localhost:8002/ingest", files=files)
    print("✅ Απάντηση Βάσης:", response.json())

print("\n--- Περιμένω 2 δευτερόλεπτα να 'κάτσουν' τα διανύσματα... ---\n")
time.sleep(2)

print("2. Ρωτάω το LLM (Retrieval & Generation)...")
payload = {"question": "Τι κέρδη είχε η εταιρεία και από ποιο τμήμα;"}
response = requests.post("http://localhost:8002/ask", json=payload)
print("🤖 Απάντηση AI:")
print(response.json()["answer"])
