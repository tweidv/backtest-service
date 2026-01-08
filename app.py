"""
Brier Labs - Backtest Platform
FastAPI web application for backtesting prediction market strategies
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI(title="Brier Labs")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Landing page with backtest interface"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/backtest")
async def run_backtest(request: Request):
    """Run a backtest with provided code"""
    # TODO: Implement backtest execution
    data = await request.json()
    return {"status": "success", "message": "Backtest started"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
