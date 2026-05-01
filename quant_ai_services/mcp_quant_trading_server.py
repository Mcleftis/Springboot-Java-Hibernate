from mcp.server.fastmcp import FastMCP
import json
import sys
import logging
import urllib.request
import urllib.error
import subprocess

# Ρύθμιση Logging για τον MCP
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr, format="[DEBUG] %(message)s")

mcp = FastMCP("Quant_Trading_MCP_Server")

@mcp.resource("market://gold/latest")
def get_latest_market_data() -> str:
    """Επιστρέφει τα τελευταία δεδομένα αγοράς για Quant Trading."""
    return json.dumps({"symbol": "GOLD", "price": 2450.50, "trend": "BULLISH"})

@mcp.tool()
def trigger_quant_analysis(symbol: str, indicator: str) -> str:
    """Καλεί τους αλγόριθμους τεχνικής ανάλυσης (MACD, Wyckoff)."""
    if indicator.upper() == "MACD":
        return f"Ανάλυση MACD για {symbol}: Signal Line Crossover Detected. Recommendation: BUY."
    return f"Ο δείκτης {indicator} δεν αναγνωρίζεται."

# --- ΤΟ ΝΕΟ ΕΡΓΑΛΕΙΟ: RAG DEBUGGER ---
@mcp.tool()
def debug_rag_server(port: int = 8002) -> str:
    """
    Ελέγχει αν ο Python RAG Server είναι ζωντανός και κάνει διάγνωση της πόρτας.
    """
    logging.debug(f"Ξεκινάει ο διαγνωστικός έλεγχος για τον RAG Server στην πόρτα {port}...")
    diagnosis_report = []

    # 1. Έλεγχος αν η πόρτα είναι ανοιχτή (Windows)
    try:
        logging.debug("Εκτέλεση netstat για έλεγχο της πόρτας...")
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        if f":{port}" in result.stdout:
            diagnosis_report.append(f"✅ H πόρτα {port} ΕΙΝΑΙ ανοιχτή και ακούει (κάποιο πρόγραμμα την χρησιμοποιεί).")
        else:
            diagnosis_report.append(f"❌ H πόρτα {port} ΕΙΝΑΙ ΚΛΕΙΣΤΗ. Ο server (uvicorn) ΔΕΝ τρέχει ή έσκασε.")
            return "\n".join(diagnosis_report) # Δεν συνεχίζουμε αν είναι κλειστή
    except Exception as e:
        diagnosis_report.append(f"⚠️ Αποτυχία ελέγχου πόρτας με netstat: {str(e)}")

    # 2. Έλεγχος του /ask endpoint
    url = f"http://127.0.0.1:{port}/ask"
    payload = json.dumps({"question": "TEST CONNECTION"}).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    req = urllib.request.Request(url, data=payload, headers=headers, method='POST')

    try:
        logging.debug(f"Στέλνω δοκιμαστικό POST Request στο {url}...")
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.getcode()
            response_data = response.read().decode('utf-8')
            diagnosis_report.append(f"✅ Ο RAG Server απάντησε! HTTP Status: {status}")
            diagnosis_report.append(f"✅ Δεδομένα Επιστροφής (JSON): {response_data}")
            
            # Έλεγχος αν το format είναι σωστό για τη Java
            if '"result"' in response_data:
                 diagnosis_report.append("✅ Η απάντηση περιέχει το κλειδί 'result'. Η Java θα το διαβάσει τέλεια.")
            else:
                 diagnosis_report.append("❌ Η απάντηση ΔΕΝ περιέχει το κλειδί 'result'. H Java θα σκάσει (NullPointerException).")

    except urllib.error.URLError as e:
        diagnosis_report.append(f"❌ Αποτυχία σύνδεσης στο {url}. Λόγος: {e.reason}")
    except Exception as e:
        diagnosis_report.append(f"❌ Άγνωστο σφάλμα κατά το request: {str(e)}")

    return "\n".join(diagnosis_report)

if __name__ == "__main__":
    logging.info("🚀 Ξεκινάει ο Quant Trading MCP Server...")
    mcp.run()