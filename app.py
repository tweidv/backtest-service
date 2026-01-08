"""
Brier Labs - Backtest Platform
FastAPI web application for backtesting prediction market strategies
"""
import os
import asyncio
import traceback
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backtest_service import DomeBacktestClient

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Brier Labs")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Landing page with backtest interface"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/backtest")
async def run_backtest(request: Request):
    """Run a backtest with provided code"""
    try:
        data = await request.json()
        
        # Extract parameters
        code = data.get("code", "")
        start_date = data.get("start_date", "2024-10-24")
        end_date = data.get("end_date", "2024-10-25")
        initial_cash_str = data.get("initial_cash", "$10,000")
        
        # Debug: Log first 200 chars of code to help diagnose issues
        if code:
            print(f"DEBUG: Received code (first 200 chars): {repr(code[:200])}")
            print(f"DEBUG: Code length: {len(code)}")
        
        # Parse initial cash (remove $ and commas)
        initial_cash = float(initial_cash_str.replace("$", "").replace(",", ""))
        
        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        start_time = int(start_dt.timestamp())
        end_time = int(end_dt.timestamp())
        
        # Get API key from environment
        api_key = os.environ.get("DOME_API_KEY")
        if not api_key:
            return JSONResponse(
                status_code=400,
                content={"error": "DOME_API_KEY environment variable not set"}
            )
        
        # Validate code is not empty
        if not code or not code.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "Code cannot be empty"}
            )
        
        # Create a safe namespace for executing user code
        # Import necessary modules for strategies
        import decimal
        import math
        
        # Create namespace with safe builtins and common imports
        strategy_namespace = {
            "__builtins__": __builtins__,
            "Decimal": Decimal,
            "decimal": decimal,
            "math": math,
        }
        
        # First, try to compile the code to catch syntax errors
        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            return JSONResponse(
                status_code=400,
                content={
                    "error": f"Syntax error in code: {str(e)}",
                    "line": e.lineno,
                    "offset": e.offset
                }
            )
        
        # Execute the strategy code to create the function
        # The code should define an async function called 'strategy' or 'my_strategy'
        try:
            exec(code, strategy_namespace)
        except SyntaxError as e:
            return JSONResponse(
                status_code=400,
                content={
                    "error": f"Syntax error: {str(e)}",
                    "line": e.lineno,
                    "offset": e.offset
                }
            )
        
        # Find the strategy function
        strategy_func = None
        for name in ["strategy", "my_strategy"]:
            if name in strategy_namespace and callable(strategy_namespace[name]):
                strategy_func = strategy_namespace[name]
                break
        
        if strategy_func is None:
            return JSONResponse(
                status_code=400,
                content={"error": "No strategy function found. Define 'async def strategy(dome):' or 'async def my_strategy(dome):'"}
            )
        
        # Create backtest client
        dome = DomeBacktestClient({
            "api_key": api_key,
            "start_time": start_time,
            "end_time": end_time,
            "step": 3600,  # 1 hour intervals
            "initial_cash": initial_cash,
        })
        
        # Run the backtest
        result = await dome.run(strategy_func)
        
        # Format results for JSON response
        trades_data = []
        for trade in result.trades:
            trades_data.append({
                "timestamp": trade.timestamp,
                "platform": trade.platform,
                "token_id": trade.token_id,
                "side": trade.side,
                "quantity": str(trade.quantity),
                "price": str(trade.price),
                "value": str(trade.value),
            })
        
        equity_curve_data = [
            {"timestamp": ts, "value": str(val)} 
            for ts, val in result.equity_curve
        ]
        
        return JSONResponse({
            "status": "success",
            "result": {
                "initial_cash": str(result.initial_cash),
                "final_value": str(result.final_value),
                "total_return": str(result.total_return),
                "total_return_pct": result.total_return_pct,
                "trades_count": len(result.trades),
                "trades": trades_data,
                "equity_curve": equity_curve_data,
            }
        })
        
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid input: {str(e)}"}
        )
    except Exception as e:
        error_trace = traceback.format_exc()
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "traceback": error_trace
            }
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
