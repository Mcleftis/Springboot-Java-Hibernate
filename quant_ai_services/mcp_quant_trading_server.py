from mcp.server.fastmcp import FastMCP
import json
import sys

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

if __name__ == "__main__":
    print("🚀 Ξεκινάει ο Quant Trading MCP Server...", file=sys.stderr)
    mcp.run()