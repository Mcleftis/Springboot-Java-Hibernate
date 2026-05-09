import requests

url = "http://localhost:8001/generate-image"

# Η παραγγελία μας
payload = {
    "prompt": "an astronaut riding a horse on Mars, highly detailed, 4k"
}

print("🚀 Στέλνω την παραγγελία στο API...")
try:
    response = requests.post(url, json=payload)
    print("✅ Απάντηση από τον Server:")
    print(response.json())
except Exception as e:
    print(f"❌ Αποτυχία σύνδεσης: {e}")