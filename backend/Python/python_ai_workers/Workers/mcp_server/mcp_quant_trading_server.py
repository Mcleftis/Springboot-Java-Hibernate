from mcp.server.fastmcp import FastMCP
import yfinance as yf
import json
import sys
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stderr, format="[DEBUG] %(message)s")

mcp = FastMCP("Market_Data_MCP_Server")

@mcp.tool()
def get_current_price(symbol: str) -> str:
    """Fetches the latest real-time market price for ANY given ticker symbol using Yahoo Finance.
    Example symbols: 'AAPL' for Apple, 'GC=F' for Gold, 'BTC-USD' for Bitcoin."""
    
    try:
        logging.debug(f"LLM requested price for symbol: {symbol}")
        
        
        ticker = yf.Ticker(symbol)
        hist_data = ticker.history(period="1d")
        
        if hist_data.empty:
            error_msg = f"Failed to fetch data. Symbol '{symbol}' might be invalid or delisted."
            logging.error(error_msg)
            return json.dumps({"error": error_msg})
        
        latest_price = round(hist_data['Close'].iloc[-1], 2)
        
        response_data = {
            "symbol": symbol.upper(), 
            "current_price": latest_price, 
            "source": "Yahoo Finance API"
        }
        
        logging.info(f"Successfully fetched price for {symbol}: {latest_price}")
        return json.dumps(response_data)

    except Exception as e:
        
        logging.error(f"System error fetching data for {symbol}: {str(e)}")
        return json.dumps({"error": f"Internal system error: {str(e)}"})

if __name__ == "__main__":
    logging.info("Starting Market Data MCP Server...")
    mcp.run()