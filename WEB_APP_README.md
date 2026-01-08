# Brier Labs - Web Application

A clean, neobrutalist-inspired web interface for backtesting prediction market strategies.

## Running the App

```bash
# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Run the FastAPI server
python app.py

# Or with hot reload for development
uvicorn app:app --reload --port 8000
```

Visit: http://localhost:8000

## Features

- **Neobrutalist Design:** Bold borders, high contrast, green accents
- **Code Mode:** Paste Python strategy code
- **Natural Language Mode:** Coming soon
- **Real-time Results:** Visual dashboard with performance metrics
- **Professional UI:** Clean, minimal, data-focused

## Tech Stack

- **Backend:** FastAPI (async Python web framework)
- **Frontend:** Tailwind CSS (utility-first CSS)
- **Fonts:** Inter (UI) + JetBrains Mono (code)
- **Design:** Neobrutalist with financial/analytics focus

## Next Steps

1. Integrate actual backtest execution (currently demo)
2. Add natural language strategy input
3. Build results visualization (charts, equity curve)
4. Add authentication and user accounts
5. Create strategy library
6. Export reports (PDF, CSV)

