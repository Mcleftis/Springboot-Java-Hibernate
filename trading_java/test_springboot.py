import sys
import json
import os
import urllib.request
import urllib.error
import time
import socket

OK   = "[OK]  "
FAIL = "[FAIL]"
WARN = "[WARN]"

BASE_URL     = "http://localhost:8080"
PYTHON_URL   = "http://localhost:8000"
RABBITMQ_URL = "localhost"
RABBITMQ_PORT = 5672
RABBITMQ_MGT  = "http://localhost:15672"
CSV_PATH     = "test.csv"
SYMBOL       = "GOLD"

errors   = 0
warnings = 0

def ok(label, detail=""):
    print(f"  {OK} {label}" + (f" - {detail}" if detail else ""))

def fail(label, detail=""):
    global errors
    errors += 1
    print(f"  {FAIL} {label}" + (f" - {detail}" if detail else ""))

def warn(label, detail=""):
    global warnings
    warnings += 1
    print(f"  {WARN} {label}" + (f" - {detail}" if detail else ""))

def get(path, base=None, timeout=10):
    base = base or BASE_URL
    req = urllib.request.Request(f"{base}{path}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8")

def post(path, data=None, base=None, timeout=30):
    base = base or BASE_URL
    req = urllib.request.Request(f"{base}{path}", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8")

def post_json(path, payload, base=None, timeout=30):
    base = base or BASE_URL
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{base}{path}", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8")

def post_multipart(path, filepath, timeout=60):
    import uuid
    boundary = uuid.uuid4().hex
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        file_data = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: text/csv\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8")

def tcp_check(host, port, timeout=3):
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False

print("\n" + "="*58)
print("  fleet-manager - Full System Health Check")
print("="*58)

print("\n[1] Spring Boot (port 8080)")
spring_ok = False
try:
    try:
        status, _ = get("/actuator/health", timeout=5)
        ok("Spring Boot running", "actuator OK")
        spring_ok = True
    except Exception:
        urllib.request.urlopen(f"{BASE_URL}/api/market/data/{SYMBOL}", timeout=5)
        ok("Spring Boot running", "port 8080")
        spring_ok = True
except urllib.error.HTTPError as e:
    if e.code in (400, 404, 500):
        ok("Spring Boot running", f"HTTP {e.code}")
        spring_ok = True
    else:
        fail("Spring Boot NOT running", "Run: .\mvnw spring-boot:run")
except Exception as e:
    fail("Spring Boot NOT running", str(e))

print("\n[2] RabbitMQ")
rabbit_ok = False
if tcp_check(RABBITMQ_URL, RABBITMQ_PORT):
    ok("AMQP port 5672 open", "RabbitMQ broker reachable")
    rabbit_ok = True
else:
    fail("AMQP port 5672 closed", "Run: docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management")

if tcp_check(RABBITMQ_URL, 15672):
    ok("Management UI port 15672 open", "http://localhost:15672  guest/guest")
else:
    warn("Management UI not reachable", "Not critical - broker may still work")

if rabbit_ok:
    try:
        import base64
        creds = base64.b64encode(b"guest:guest").decode()
        req = urllib.request.Request(f"{RABBITMQ_MGT}/api/queues")
        req.add_header("Authorization", f"Basic {creds}")
        with urllib.request.urlopen(req, timeout=5) as r:
            queues = json.loads(r.read().decode())
        names = [q["name"] for q in queues]
        if "gold_prices_queue" in names:
            q = next(q for q in queues if q["name"] == "gold_prices_queue")
            ok("Queue 'gold_prices_queue' exists",
               f"messages={q.get('messages',0)} | consumers={q.get('consumers',0)}")
        else:
            warn("Queue 'gold_prices_queue' not found yet",
                 "Will be created on first message send")
    except Exception as e:
        warn("Could not query RabbitMQ Management API", str(e))

print("\n[3] Python AI Service (port 8000)")
python_ok = False
if tcp_check("localhost", 8000):
    try:
        status, body = get("/health", base=PYTHON_URL, timeout=5)
        ok("Python service running", f"/health -> HTTP {status}")
        python_ok = True
    except urllib.error.HTTPError as e:
        if e.code in (404,):
            ok("Python service running", "port 8000 open")
            python_ok = True
        else:
            warn("Python service reachable but /health failed", f"HTTP {e.code}")
    except Exception as e:
        ok("Python service port open", str(e))
        python_ok = True
else:
    fail("Python AI service NOT running",
         "Run: docker-compose up  OR  cd python-service && uvicorn main:app --port 8000")

if python_ok:
    try:
        status, body = post_json("/analyze", {
            "symbol": SYMBOL,
            "prices": [1850.5, 1862.3, 1845.0, 1878.9, 1901.2,
                       1888.4, 1920.0, 1935.5, 1910.3, 1955.8]
        }, base=PYTHON_URL)
        data = json.loads(body)
        ok("/analyze endpoint works",
           f"predicted={data.get('predicted_next_price','?')} | trend={data.get('trend','?')}")
    except Exception as e:
        warn("/analyze endpoint failed", str(e))

if python_ok:
    try:
        status, body = post_json("/wyckoff-full", {
            "symbol": SYMBOL,
            "prices": [1850.5, 1862.3, 1845.0, 1878.9, 1901.2,
                       1888.4, 1920.0, 1935.5, 1910.3, 1955.8]
        }, base=PYTHON_URL)
        data = json.loads(body)
        ok("/wyckoff-full endpoint works",
           f"phase={data.get('current_phase','?')}")
    except Exception as e:
        warn("/wyckoff-full endpoint failed", str(e))

print("\n[4] CSV Data")
if os.path.isfile(CSV_PATH):
    size = os.path.getsize(CSV_PATH)
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        lines = f.readlines()
    if len(lines) > 1:
        ok("test.csv found", f"{len(lines)-1} records, {size} bytes")
    else:
        fail("test.csv is empty", "Needs Date,USD columns with data")
else:
    fail("test.csv NOT found", f"Expected at: {CSV_PATH}")

print("\n[5] Upload CSV -> /api/market/upload/GOLD")
if spring_ok and os.path.isfile(CSV_PATH):
    try:
        status, body = post_multipart(f"/api/market/upload/{SYMBOL}", CSV_PATH)
        if "Saved" in body:
            ok("Upload successful", body.strip())
        else:
            ok("Upload responded", body[:80])
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        if "duplicate" in body.lower() or "constraint" in body.lower():
            warn("Data already in DB", "OK - not an error")
        else:
            fail("Upload failed", f"HTTP {e.code}: {body[:100]}")
    except Exception as e:
        fail("Upload failed", str(e))
else:
    warn("Upload skipped", "Spring Boot not running or CSV missing")

print("\n[6] Analysis -> /api/market/analyze/GOLD")
if spring_ok:
    try:
        status, body = post(f"/api/market/analyze/{SYMBOL}")
        data = json.loads(body)
        required = ["cyclePhase", "condition", "recommendation", "supportZone", "resistanceZone", "riskLevel"]
        missing  = [k for k in required if k not in data]
        if missing:
            warn("Analysis OK but missing fields", str(missing))
        else:
            ok("Analysis successful", "all fields present")
        print(f"\n      cyclePhase  : {data.get('cyclePhase','-')}")
        print(f"      condition   : {data.get('condition','-')}")
        print(f"      riskLevel   : {data.get('riskLevel','-')}")
        print(f"      support     : {data.get('supportZone','-')}")
        print(f"      resistance  : {data.get('resistanceZone','-')}")
        rec = str(data.get('recommendation',''))
        print(f"      rec         : {rec[:120]}...")
        if "AI: unavailable" in rec:
            warn("Python AI service offline", "Start docker-compose for full analysis")
        elif "AI:" in rec:
            ok("Python AI integrated in recommendation")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        fail("Analysis failed", f"HTTP {e.code}: {body[:100]}")
    except Exception as e:
        fail("Analysis failed", str(e))
else:
    warn("Analysis skipped", "Spring Boot not running")

print("\n[7] Wyckoff Full (Java -> Python)")
if spring_ok:
    try:
        status, body = post(f"/api/market/wyckoff-full/{SYMBOL}")
        data = json.loads(body)
        ok("Wyckoff Full successful",
           f"phase={data.get('current_phase','-')} | events={len(data.get('recent_events',[]))}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if "fleet-python" in body or "8000" in body:
            fail("Wyckoff failed - Python service offline", "Start: docker-compose up")
        else:
            fail("Wyckoff failed", f"HTTP {e.code}: {body[:100]}")
    except Exception as e:
        fail("Wyckoff failed", str(e))
else:
    warn("Wyckoff skipped", "Spring Boot not running")

print("\n" + "="*58)
print("  SUMMARY")
print("="*58)
print(f"  Spring Boot  : {'[OK] UP' if spring_ok else '[FAIL] DOWN'}")
print(f"  RabbitMQ     : {'[OK] UP' if rabbit_ok else '[FAIL] DOWN'}")
print(f"  Python AI    : {'[OK] UP' if python_ok else '[FAIL] DOWN'}")
print("-" * 58)
if errors == 0 and warnings == 0:
    print(f"  [OK] All OK! The system is running normally.")
elif errors == 0:
    print(f"  [WARN] {warnings} warning(s) - non critical.")
else:
    print(f"  [FAIL] {errors} error(s), {warnings} warning(s).")
print("="*58 + "\n")
