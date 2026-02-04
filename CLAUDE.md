# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QuantDinger is a quantitative trading monitoring system based on the HAMA (Hull Moving Average) technical indicator. The system uses browser automation (Playwright/Brave) to scrape TradingView charts and local OCR (RapidOCR) to extract HAMA indicator data.

**Tech Stack:**
- **Backend**: Python 3.11+ with Flask 2.3, Playwright 1.40, RapidOCR 1.3, SQLAlchemy 2.0
- **Frontend**: Vue 2.6.14, Ant Design Vue 1.7.8, ECharts 6.0, Axios
- **Database**: SQLite (primary), Redis (optional cache)

## Development Commands

### Backend (Python)

```bash
cd backend_api_python

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run development server (port 5000)
python run.py

# Run with gunicorn (production)
gunicorn -c gunicorn_config.py "run:app"
```

### Frontend (Vue.js)

```bash
cd quantdinger_vue

# Install dependencies
npm install

# Run development server (port 8000)
npm run serve

# Build for production
npm run build

# Lint code
npm run lint
```

### Full Stack Development

```bash
# Terminal 1:
cd backend_api_python && python run.py

# Terminal 2:
cd quantdinger_vue && npm run serve
```

## Architecture Overview

```
QuantDinger/
├── backend_api_python/          # Python Flask backend
│   ├── app/
│   │   ├── __init__.py          # Application factory with singletons
│   │   ├── routes/              # API blueprints (endpoints)
│   │   ├── services/            # Business logic layer
│   │   ├── config/              # Configuration classes
│   │   ├── data/                # SQLite databases
│   │   └── utils/               # Utilities (logger, SSE, etc.)
│   └── run.py                   # Flask entry point
│
├── quantdinger_vue/             # Vue.js frontend
│   ├── src/
│   │   ├── views/               # Page components
│   │   ├── mixins/              # Vue mixins (realtimePrice, etc.)
│   │   └── utils/               # Utilities (request, SSE, etc.)
│   └── package.json
│
└── docs/                        # Additional documentation
    ├── BRAVE_MONITOR_LOGIC.md   # Brave monitoring details
    └── TECH_STACK.md            # Complete dependency list
```

## Backend Architecture

### Application Factory Pattern

The Flask app uses the application factory pattern ([`app/__init__.py`](backend_api_python/app/__init__.py)). Key singletons initialized at startup:
- `_redis_client` - Redis connection (optional)
- `_hama_scheduler` - APScheduler for periodic HAMA data fetching
- `_hama_brave_monitor` - Browser automation monitor
- `_trading_executor` - Strategy execution engine
- `_pending_order_worker` - Order dispatch worker
- `_reflection_worker` - AI reflection verification

### Key Services

1. **HAMA Brave Monitor** ([`services/hama_brave_monitor.py`](backend_api_python/app/services/hama_brave_monitor.py))
   - Controls Brave/Chromium browser in headless mode
   - Navigates to TradingView charts, captures screenshots
   - Parallel monitoring with `monitor_batch_parallel()`
   - SQLite + Redis dual-layer caching

2. **OCR Extractor** ([`services/hama_ocr_extractor.py`](backend_api_python/app/services/hama_ocr_extractor.py))
   - Uses RapidOCR for local text recognition (no API keys needed)
   - Extracts: HAMA value, color, trend, MA status, Bollinger status
   - Clip coordinates configurable for screenshot region

3. **Trading Executor** ([`services/trading_executor.py`](backend_api_python/app/services/trading_executor.py))
   - Manages trading strategy lifecycle (start/stop)
   - Handles indicator-based strategies
   - Simulated trading (paper mode)

4. **Monitor Worker** ([`services/hama_monitor_worker.py`](backend_api_python/app/services/hama_monitor_worker.py))
   - Background thread continuously monitoring configured symbols
   - Detects HAMA crossover signals (金叉/死叉)
   - Sends email notifications on signal detection

### API Routes Structure

Routes are organized by feature in [`app/routes/`](backend_api_python/app/routes/):
- `dashboard.py` - KPI metrics, trades, positions
- `hama_market.py` - HAMA watchlist, symbol data, signals
- `hama_monitor.py` - Smart monitoring control
- `tradingview_scanner.py` - Top gainers, screenshots
- `trading_assistant.py` - AI decisions, positions
- `settings.py` - Configuration management

### Environment Configuration

Create [`backend_api_python/.env`](backend_api_python/.env):

```env
# Flask
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key

# TradingView
TRADINGVIEW_URL=https://cn.tradingview.com/chart/U1FY2qxO/

# Brave Monitor
BRAVE_MONITOR_ENABLED=true
BRAVE_MONITOR_CACHE_TTL=900
BRAVE_MONITOR_BROWSER_TYPE=brave
BRAVE_PATH=C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe

# HAMA Scheduler
HAMA_SCHEDULER_ENABLED=true
HAMA_SCHEDULER_AUTO_START=true

# Redis (optional)
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379

# Monitoring
HAMA_DEMO_MODE=false
```

### TradingView Cookie Configuration (Optional)

For auto-login, create [`backend_api_python/tradingview_cookies.json`](backend_api_python/tradingview_cookies.json):

```json
{
  "cookies": [
    {
      "name": "sessionid",
      "value": "your-cookie-value",
      "domain": ".tradingview.com",
      "path": "/"
    }
  ]
}
```

## Frontend Architecture

### Page Components

Located in [`src/views/`](quantdinger_vue/src/views/):
- **Dashboard** - KPI cards, calendar heatmap, charts
- **HAMA Market** - Real-time HAMA status table with SSE price updates
- **Smart Monitor** - Monitoring control with gainers list and signal history
- **TradingView Scanner** - Top gainers with expandable screenshot rows
- **Indicator Analysis** - Multi-chart display (TradingView, HAMA, K-line)
- **Settings** - Dynamic form generated from backend schema

### Mixins

[`mixins/realtimePrice.js`](quantdinger_vue/src/mixins/realtimePrice.js) provides SSE-based real-time Binance prices:
- `getRealtimePrice(symbol)` - Get current price
- `isPriceJustUpdated(symbol)` - Flash effect on price update
- `formatPrice(symbol, fallback)` - Smart decimal formatting

### State Management

Vuex store in [`src/store/modules/app.js`](quantdinger_vue/src/store/modules/app.js):
- Theme (light/dark/realdark)
- Sidebar state

### API Client

[`src/utils/request.js`](quantdinger_vue/src/utils/request.js) wraps Axios:
- Base URL: `http://localhost:5000`
- Request/response interceptors for auth and error handling

## Data Flow

### HAMA Monitoring Flow

```
TradingView URL → Playwright (Brave/Chromium) → Screenshot (PNG) → RapidOCR → Parse → SQLite + Redis → API → Frontend
```

### Real-time Price Updates

```
Binance WebSocket → Redis Pub/Sub → SSE Endpoint (/api/sse/prices) → Frontend SSE Client → Mixin → UI Update
```

## Important Implementation Details

### Brave Monitor
- Screenshot region configured via clip coordinates in [`hama_ocr_extractor.py`](backend_api_python/app/services/hama_ocr_extractor.py)
- Falls back to Chromium if Brave not found
- Cache TTL: 15 minutes default (configurable via `BRAVE_MONITOR_CACHE_TTL`)

### Frontend SSE
- Uses `event-source-polyfill` for wider compatibility
- Auto-reconnect on connection loss
- Flash animation via `@keyframes priceFlash`

### Dynamic Forms (Settings)
- Schema fetched from `/api/settings/schema`
- Supports: text, password, number, boolean, select types
- Boolean values stored as strings "True"/"False"

### Database Schema
- SQLite files in [`backend_api_python/data/`](backend_api_python/data/)
- Tables: `hama_brave_data`, `hama_signals`, `hama_email_log`
- Auto-created on first run if missing

## Common Patterns

### Adding a New API Endpoint

Create route function in [`app/routes/`](backend_api_python/app/routes/):
```python
@bp.route('/api/feature/action', methods=['POST'])
def feature_action():
    data = request.get_json()
    # Business logic here
    return jsonify(success=True, data=result)
```

### Adding a New Frontend Page

1. Create component in [`src/views/`](quantdinger_vue/src/views/)
2. Add route in [`src/config/router.config.js`](quantdinger_vue/src/config/router.config.js)
3. Add menu item in [`src/config/menu.config.js`](quantdinger_vue/src/config/menu.config.js)
4. Add i18n keys in [`src/locales/`](quantdinger_vue/src/locales/)

### Adding New Monitoring Symbols

Edit [`backend_api_python/app/routes/hama_market.py`](backend_api_python/app/routes/hama_market.py):
```python
DEFAULT_SYMBOLS = [
    'BTCUSDT',
    'ETHUSDT',
    'YOURCOINUSDT',  # Add new symbol
]
```

### Adjusting OCR Parameters

Edit [`backend_api_python/app/services/hama_ocr_extractor.py`](backend_api_python/app/services/hama_ocr_extractor.py):
```python
clip = {
    'x': int(page_width * 0.72),
    'y': int(page_height * 0.45),
    'width': int(page_width * 0.28),
    'height': int(page_height * 0.55)
}
```

### Performance Optimization

```python
# Parallel monitoring (3x faster)
monitor.monitor_batch_parallel(symbols, max_workers=3)

# Cache warmup
monitor.warmup_cache(hot_symbols=['BTCUSDT', 'ETHUSDT'])

# Dynamic interval (based on market activity)
interval = monitor.get_dynamic_interval()  # 300 or 600 seconds

# Clean old records
monitor.cleanup_old_records(days=7)
monitor.cleanup_old_screenshots(max_age_days=7)
```

## Troubleshooting

### Brave Browser Not Found
```
Warning: Brave browser not found, falling back to Chromium
```
- Install Brave from https://brave.com/download/
- Or set `BRAVE_MONITOR_BROWSER_TYPE=chromium` in .env

### OCR Initialization Failed
```
RapidOCR initialization failed
```
- Install: `pip install rapidocr_onnxruntime`

### TradingView Auto-login Failed
```
Auto-login failed
```
- Manually login to TradingView and export cookies to `tradingview_cookies.json`
- Or configure account/password in `file/tradingview.txt`

### SQLite Database Locked
```
sqlite3.OperationalError: database is locked
```
- Each thread creates its own connection (already implemented)
- Restart backend if issue persists

## File References

- [README.md](README.md) - Project overview and setup
- [docs/BRAVE_MONITOR_LOGIC.md](docs/BRAVE_MONITOR_LOGIC.md) - Brave monitoring system details
- [docs/TECH_STACK.md](docs/TECH_STACK.md) - Complete dependency list
- [backend_api_python/run.py](backend_api_python/run.py) - Backend entry point
- [backend_api_python/app/__init__.py](backend_api_python/app/__init__.py) - App factory with singletons
