# QuoteFlow — Quote Generator with History

A complete Flask + SQLite web application for the VirtualWorks **Quote Generator with History (task4)** assignment. It fetches a random quote from a public API, displays it in a responsive dashboard, and stores every generated quote in a local SQLite database.

## Features

- Responsive, polished dashboard with a current quote and recent-history cards.
- Random quote API integration using `https://dummyjson.com/quotes/random`.
- SQLite persistence: quote text, author, source and timestamp are stored for each generated quote.
- Offline fallback quote if the public API is unavailable or internet access fails.
- History endpoint, clear-history action and copy-to-clipboard interactions.
- Parameterized SQL queries and HTML escaping for history rendering.
- Automated tests for page rendering, health check, API persistence, fallback behavior and clearing history.

## Requirements

- Windows 10/11
- Python 3.10 or newer
- Internet connection for live quotes (the app still works using fallback quotes offline)

## Run on Windows (PowerShell)

1. Extract the ZIP file.
2. Open the extracted `quote-generator-with-history` folder in VS Code.
3. In VS Code, select **Terminal → New Terminal** and confirm the terminal is in this folder.
4. Run these commands one by one:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, run this once in the same terminal and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

5. Open **http://127.0.0.1:5000** in Chrome.
6. Click **Generate new quote**. The new quote appears at the top and is added to the history below. Refresh the browser; saved history remains because it is stored in SQLite.

Stop the local server with `Ctrl+C` in the terminal.

## Run automated tests

With the virtual environment activated and dependencies installed:

```powershell
python -m pytest -v
```

Or use Python's built-in test runner:

```powershell
python -m unittest discover -s tests -v
```

## Project structure

```text
quote-generator-with-history/
├── app.py                   # Flask routes, API client, SQLite operations
├── requirements.txt         # Python dependencies
├── README.md                # Setup, run and test instructions
├── templates/
│   └── index.html           # Jinja dashboard template
├── static/
│   ├── css/styles.css       # Responsive dashboard styling
│   └── js/main.js           # Fetch, history, copy and clear interactions
└── tests/
    └── test_app.py          # Automated tests
```

The `quotes.db` SQLite database is created automatically beside `app.py` the first time the app starts. It is intentionally excluded from the ZIP so each install creates its own clean database.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Render the dashboard |
| `POST` | `/api/quotes/random` | Fetch (or fall back to) a quote and save it to SQLite |
| `GET` | `/api/history?limit=20` | Return newest saved quotes (limit capped at 100) |
| `DELETE` | `/api/history` | Delete all saved quote history |
| `GET` | `/api/health` | Basic application health check |

## Data flow

1. The Generate button sends `POST /api/quotes/random` from JavaScript.
2. Flask requests a quote from DummyJSON. If the request fails, a bundled fallback quote is used.
3. Flask inserts the quote and timestamp into SQLite using a parameterized query.
4. The API returns the saved quote as JSON; JavaScript updates the featured quote and reloads history.
5. On page load, JavaScript requests `/api/history`, so history remains available after refresh or server restart.

## Notes

- This is a local development app; Flask debug mode is enabled only for the provided local run command. Do not expose the debug server directly to the public internet.
- The public quote API and Google Fonts require internet access. The app's core functionality and layout still work if the quote API is unavailable.
- For a public production deployment, set a strong `FLASK_SECRET_KEY`, disable debug mode, and use a production WSGI server.
