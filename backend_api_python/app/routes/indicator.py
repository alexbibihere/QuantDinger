"""
Indicator APIs (local-first).

These endpoints are used by the frontend `/indicator-analysis` page.
In the original architecture, the frontend called PHP endpoints like:
`/addons/quantdinger/indicator/getIndicators`.

For local mode, we expose Python equivalents under `/api/indicator/*`.
"""

from __future__ import annotations

import json
import os
import re
import time
import traceback
from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify, request
import pandas as pd
import numpy as np

from app.utils.db import get_db_connection
from app.utils.logger import get_logger
import requests

logger = get_logger(__name__)

indicator_bp = Blueprint("indicator", __name__)


def _now_ts() -> int:
    return int(time.time())


def _parse_user_id(userid) -> int:
    """
    解析用户 ID，兼容整数和字符串类型

    Args:
        userid: 用户 ID (整数) 或用户名 (字符串)

    Returns:
        整数类型的用户 ID
    """
    if isinstance(userid, int):
        return userid
    elif isinstance(userid, str):
        # 尝试将字符串转换为整数
        try:
            return int(userid)
        except ValueError:
            # 如果转换失败（如 "quantdinger"），使用默认值 1
            return 1
    else:
        return 1


def _extract_indicator_meta_from_code(code: str) -> Dict[str, str]:
    """
    Extract indicator name/description from python code.
    Expected variables:
      my_indicator_name = "..."
      my_indicator_description = "..."
    """
    if not code or not isinstance(code, str):
        return {"name": "", "description": ""}

    # Simple assignment capture for single/double quoted strings.
    name_match = re.search(r'^\s*my_indicator_name\s*=\s*([\'"])(.*?)\1\s*$', code, re.MULTILINE)
    desc_match = re.search(r'^\s*my_indicator_description\s*=\s*([\'"])(.*?)\1\s*$', code, re.MULTILINE)

    name = (name_match.group(2).strip() if name_match else "")[:100]
    description = (desc_match.group(2).strip() if desc_match else "")[:500]
    return {"name": name, "description": description}


def _row_to_indicator(row: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """
    Map SQLite row -> frontend expected indicator shape.

    Frontend uses:
    - id, name, description, code
    - is_buy (1 bought, 0 custom)
    - user_id / userId
    - end_time (optional)
    """
    return {
        "id": row.get("id"),
        "user_id": row.get("user_id") if row.get("user_id") is not None else user_id,
        "is_buy": row.get("is_buy") if row.get("is_buy") is not None else 0,
        "end_time": row.get("end_time") if row.get("end_time") is not None else 1,
        "name": row.get("name") or "",
        "code": row.get("code") or "",
        "description": row.get("description") or "",
        "publish_to_community": row.get("publish_to_community") if row.get("publish_to_community") is not None else 0,
        "pricing_type": row.get("pricing_type") or "free",
        "price": row.get("price") if row.get("price") is not None else 0,
        # Local mode: encryption is not supported; keep field for frontend compatibility (always 0).
        "is_encrypted": 0,
        "preview_image": row.get("preview_image") or "",
        # Prefer MySQL-like time fields; fallback to legacy local columns.
        "createtime": row.get("createtime") or row.get("created_at"),
        "updatetime": row.get("updatetime") or row.get("updated_at"),
    }


def _generate_mock_df(length=200):
    """Generate mock K-line data for verification."""
    from datetime import datetime, timedelta
    
    dates = [datetime.now() - timedelta(minutes=i) for i in range(length)]
    dates.reverse()
    
    # Random walk with trend
    returns = np.random.normal(0, 0.002, length)
    price_path = 10000 * np.exp(np.cumsum(returns))
    
    close = price_path
    high = close * (1 + np.abs(np.random.normal(0, 0.001, length)))
    low = close * (1 - np.abs(np.random.normal(0, 0.001, length)))
    open_p = close * (1 + np.random.normal(0, 0.001, length)) # Slight deviation from close
    # Ensure High is highest and Low is lowest
    high = np.maximum(high, np.maximum(open_p, close))
    low = np.minimum(low, np.minimum(open_p, close))
    
    volume = np.abs(np.random.normal(100, 50, length)) * 1000
    
    df = pd.DataFrame({
        'time': [int(d.timestamp() * 1000) for d in dates],
        'open': open_p,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })
    return df


@indicator_bp.route("/getIndicators", methods=["POST"])
def get_indicators():
    """
    Get indicator list for a user.

    Request:
      { userid: number }

    Response:
      { code: 1, data: [ ... ] }
    """
    try:
        data = request.get_json() or {}
        user_id = _parse_user_id(data.get("userid"))

        with get_db_connection() as db:
            cur = db.cursor()
            # Local mode: "我的指标" should include both purchased and custom indicators.
            cur.execute(
                """
                SELECT
                  id, user_id, is_buy, end_time, name, code, description,
                  publish_to_community, pricing_type, price, is_encrypted, preview_image,
                  createtime, updatetime, created_at, updated_at
                FROM qd_indicator_codes
                WHERE user_id = ?
                ORDER BY id DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall() or []
            cur.close()

        out = [_row_to_indicator(r, user_id) for r in rows]
        return jsonify({"code": 1, "msg": "success", "data": out})
    except Exception as e:
        logger.error(f"get_indicators failed: {str(e)}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e), "data": []}), 500


@indicator_bp.route("/saveIndicator", methods=["POST"])
def save_indicator():
    """
    Create or update an indicator.

    Request (frontend sends many extra fields; we store only the essentials):
      {
        userid: number,
        id: number (0 for create),
        name: string,
        code: string,
        description?: string,
        ...
      }
    """
    try:
        data = request.get_json() or {}
        user_id = _parse_user_id(data.get("userid"))
        indicator_id = int(data.get("id") or 0)
        code = data.get("code") or ""
        name = (data.get("name") or "").strip()
        description = (data.get("description") or "").strip()
        publish_to_community = 1 if data.get("publishToCommunity") or data.get("publish_to_community") else 0
        pricing_type = (data.get("pricingType") or data.get("pricing_type") or "free").strip() or "free"
        try:
            price = float(data.get("price") or 0)
        except Exception:
            price = 0.0
        preview_image = (data.get("previewImage") or data.get("preview_image") or "").strip()

        if not code or not str(code).strip():
            return jsonify({"code": 0, "msg": "code is required", "data": None}), 400

        # Local dev UX: if name/description not provided, derive from code variables.
        if not name or not description:
            meta = _extract_indicator_meta_from_code(code)
            if not name:
                name = meta.get("name") or ""
            if not description:
                description = meta.get("description") or ""

        if not name:
            name = "Custom Indicator"

        now = _now_ts()

        with get_db_connection() as db:
            cur = db.cursor()
            if indicator_id and indicator_id > 0:
                cur.execute(
                    """
                    UPDATE qd_indicator_codes
                    SET name = ?, code = ?, description = ?,
                        publish_to_community = ?, pricing_type = ?, price = ?, preview_image = ?,
                        updatetime = ?, updated_at = ?
                    WHERE id = ? AND user_id = ? AND (is_buy IS NULL OR is_buy = 0)
                    """,
                    (name, code, description, publish_to_community, pricing_type, price, preview_image, now, now, indicator_id, user_id),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO qd_indicator_codes
                      (user_id, is_buy, end_time, name, code, description,
                       publish_to_community, pricing_type, price, preview_image,
                       createtime, updatetime, created_at, updated_at)
                    VALUES (?, 0, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, name, code, description, publish_to_community, pricing_type, price, preview_image, now, now, now, now),
                )
                indicator_id = int(cur.lastrowid or 0)
            db.commit()
            cur.close()

        return jsonify({"code": 1, "msg": "success", "data": {"id": indicator_id, "userid": user_id}})
    except Exception as e:
        logger.error(f"save_indicator failed: {str(e)}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e), "data": None}), 500


@indicator_bp.route("/deleteIndicator", methods=["POST"])
def delete_indicator():
    """Delete an indicator by id."""
    try:
        data = request.get_json() or {}
        user_id = _parse_user_id(data.get("userid"))
        indicator_id = int(data.get("id") or 0)
        if not indicator_id:
            return jsonify({"code": 0, "msg": "id is required", "data": None}), 400

        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute(
                "DELETE FROM qd_indicator_codes WHERE id = ? AND user_id = ? AND (is_buy IS NULL OR is_buy = 0)",
                (indicator_id, user_id),
            )
            db.commit()
            cur.close()

        return jsonify({"code": 1, "msg": "success", "data": None})
    except Exception as e:
        logger.error(f"delete_indicator failed: {str(e)}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e), "data": None}), 500


@indicator_bp.route("/verifyCode", methods=["POST"])
def verify_code():
    """
    Verify/Dry-run indicator code with mock data.
    Checks for:
    - Syntax errors
    - Runtime errors
    - Output format (must define 'output' dict)
    """
    try:
        data = request.get_json() or {}
        code = data.get("code") or ""
        
        if not code or not str(code).strip():
            return jsonify({"code": 0, "msg": "Code is empty", "data": None}), 400

        # 1. Generate mock data
        df = _generate_mock_df()
        
        # 2. Prepare execution environment
        exec_env = {
            'df': df.copy(),
            'pd': pd,
            'np': np,
            'output': None
        }
        
        # 3. Execute code
        try:
            exec(code, exec_env)
        except SyntaxError as e:
            return jsonify({
                "code": 0, 
                "msg": f"Syntax Error at line {e.lineno}: {e.msg}", 
                "data": {"type": "SyntaxError", "line": e.lineno, "details": str(e)}
            })
        except Exception as e:
            # Capture traceback for better debugging
            tb = traceback.format_exc()
            # Extract the line number from the exec() call in the traceback if possible
            # This is tricky because the traceback includes the backend frames. 
            # We'll just return the exception message.
            return jsonify({
                "code": 0, 
                "msg": f"Runtime Error: {str(e)}", 
                "data": {"type": type(e).__name__, "details": tb}
            })
            
        # 4. Check output
        output = exec_env.get('output')
        
        if output is None:
            return jsonify({
                "code": 0, 
                "msg": "Missing 'output' variable. Your code must define an 'output' dictionary.", 
                "data": {"type": "MissingOutput"}
            })
            
        if not isinstance(output, dict):
            return jsonify({
                "code": 0, 
                "msg": f"'output' must be a dictionary, got {type(output).__name__}", 
                "data": {"type": "InvalidOutputType"}
            })
            
        # Check required fields
        if 'plots' not in output and 'signals' not in output:
             return jsonify({
                "code": 0, 
                "msg": "'output' dict should contain 'plots' or 'signals' list.", 
                "data": {"type": "InvalidOutputStructure"}
            })
            
        # Basic check for lengths
        plots = output.get('plots', [])
        signals = output.get('signals', [])
        
        for p in plots:
            if 'data' not in p:
                return jsonify({"code": 0, "msg": f"Plot '{p.get('name')}' missing 'data' field.", "data": {"type": "InvalidPlot"}})
            if len(p['data']) != len(df):
                return jsonify({
                    "code": 0, 
                    "msg": f"Plot '{p.get('name')}' data length ({len(p['data'])}) does not match DataFrame length ({len(df)}).", 
                    "data": {"type": "LengthMismatch"}
                })
                
        for s in signals:
            if 'data' not in s:
                return jsonify({"code": 0, "msg": f"Signal '{s.get('type')}' missing 'data' field.", "data": {"type": "InvalidSignal"}})
            if len(s['data']) != len(df):
                return jsonify({
                    "code": 0, 
                    "msg": f"Signal '{s.get('type')}' data length ({len(s['data'])}) does not match DataFrame length ({len(df)}).", 
                    "data": {"type": "LengthMismatch"}
                })

        return jsonify({
            "code": 1, 
            "msg": "Verification passed! Code executed successfully.", 
            "data": {
                "plots_count": len(plots),
                "signals_count": len(signals)
            }
        })

    except Exception as e:
        logger.error(f"verify_code failed: {str(e)}", exc_info=True)
        return jsonify({"code": 0, "msg": f"System Error: {str(e)}", "data": None}), 500


@indicator_bp.route("/aiGenerate", methods=["POST"])
def ai_generate():
    """
    SSE endpoint to generate indicator code.

    Frontend expects 'text/event-stream' with chunks:
      data: {"content":"..."}\n\n
    then:
      data: [DONE]\n\n

    Local-first: if OpenRouter key is not configured, we return a reasonable template.
    """
    data = request.get_json() or {}
    prompt = (data.get("prompt") or "").strip()
    existing = (data.get("existingCode") or "").strip()

    if not prompt:
        # Keep SSE contract (match PHP behavior) so frontend doesn't look "stuck".
        def _err_stream():
            yield "data: " + json.dumps({"error": "提示词不能为空"}, ensure_ascii=False) + "\n\n"
            yield "data: [DONE]\n\n"

        return Response(
            _err_stream(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # System prompt copied/adapted from the legacy PHP implementation.
    SYSTEM_PROMPT = """# Role

You are an expert Python quantitative trading developer. Your task is to write custom indicator or strategy scripts for a professional K-line chart component running in a browser (Pyodide environment).

# Context & Environment

1. **Runtime Environment**: Code runs in a browser sandbox, **network access is prohibited** (cannot use `pip` or `requests`).

2. **Pre-installed Libraries**: The system has already imported `pandas as pd` and `numpy as np`. **DO NOT** include `import pandas as pd` or `import numpy as np` in your generated code. Use `pd` and `np` directly.

3. **Input Data**: The system provides a variable `df` (Pandas DataFrame) with index from 0 to N.
   - Columns include: `df['time']` (timestamp), `df['open']`, `df['high']`, `df['low']`, `df['close']`, `df['volume']`.

# Output Requirement (Strict)

At the end of code execution, you **MUST** define a dictionary variable named `output`. The system only reads this variable to render the chart.

Additionally, you MUST define:
- my_indicator_name = "..."
- my_indicator_description = "..."

`output` MUST follow this shape:
output = {
  "name": my_indicator_name,
  "plots": [ { "name": str, "data": list, "color": "#RRGGBB", "overlay": bool, "type": "line" (optional) } ],
  "signals": [ { "type": "buy"|"sell", "text": str, "data": list, "color": "#RRGGBB" } ] (optional),
  "calculatedVars": {} (optional)
}
Where `data` lists MUST have the same length as `df` and use `None` for "no value".

Backtest/execution compatibility (recommended):
- Also set df['buy'] and df['sell'] as boolean columns (same length as df).

# Signal confirmation / execution timing (IMPORTANT)
- Signals are generally confirmed on bar close. The backtest engine may execute them on the next bar open to better match live trading and avoid look-ahead bias.

# Robustness requirements (IMPORTANT)
- Always handle NaN/inf and division-by-zero (common in RSI/BB/RSV calculations).
- Avoid overly restrictive entry/exit logic that results in zero buy or zero sell signals.
  For multi-indicator strategies, do NOT require a crossover AND extreme RSI on the same bar unless explicitly requested.
- Prefer edge-triggered signals (one-shot) to avoid repeated consecutive signals:
  buy = raw_buy.fillna(False) & (~raw_buy.shift(1).fillna(False))
  sell = raw_sell.fillna(False) & (~raw_sell.shift(1).fillna(False))
- If your final conditions produce no buys or no sells in the visible range, relax logically (e.g., remove one filter or widen thresholds).

IMPORTANT: Output Python code directly, without explanations, without descriptions, start directly with code, and do NOT use markdown code blocks like ```python.
"""

    def _template_code() -> str:
        # Fallback template that follows the project expectations.
        cleaned_prompt = prompt.replace('\n', ' ')[:200]
        header = (
            f"my_indicator_name = \"Custom Indicator\"\n"
            f"my_indicator_description = \"{cleaned_prompt}\"\n\n"
        )
        body = (
            "df = df.copy()\n\n"
            "# Example: robust RSI with edge-triggered buy/sell (no position management, no TP/SL on chart)\n"
            "rsi_len = 14\n"
            "delta = df['close'].diff()\n"
            "gain = delta.clip(lower=0)\n"
            "loss = (-delta).clip(lower=0)\n"
            "# Wilder-style smoothing (stable and avoids early NaN explosion)\n"
            "avg_gain = gain.ewm(alpha=1/rsi_len, adjust=False).mean()\n"
            "avg_loss = loss.ewm(alpha=1/rsi_len, adjust=False).mean()\n"
            "rs = avg_gain / avg_loss.replace(0, np.nan)\n"
            "rsi = 100 - (100 / (1 + rs))\n"
            "rsi = rsi.fillna(50)\n\n"
            "# Raw conditions (avoid overly strict filters)\n"
            "raw_buy = (rsi < 30)\n"
            "raw_sell = (rsi > 70)\n"
            "# One-shot signals\n"
            "buy = raw_buy.fillna(False) & (~raw_buy.shift(1).fillna(False))\n"
            "sell = raw_sell.fillna(False) & (~raw_sell.shift(1).fillna(False))\n"
            "df['buy'] = buy.astype(bool)\n"
            "df['sell'] = sell.astype(bool)\n\n"
            "buy_marks = [df['low'].iloc[i] * 0.995 if bool(buy.iloc[i]) else None for i in range(len(df))]\n"
            "sell_marks = [df['high'].iloc[i] * 1.005 if bool(sell.iloc[i]) else None for i in range(len(df))]\n\n"
            "output = {\n"
            "  'name': my_indicator_name,\n"
            "  'plots': [\n"
            "    {'name': 'RSI(14)', 'data': rsi.tolist(), 'color': '#faad14', 'overlay': False}\n"
            "  ],\n"
            "  'signals': [\n"
            "    {'type': 'buy', 'text': 'B', 'data': buy_marks, 'color': '#00E676'},\n"
            "    {'type': 'sell', 'text': 'S', 'data': sell_marks, 'color': '#FF5252'}\n"
            "  ]\n"
            "}\n"
        )
        if existing:
            header = "# Existing code was provided as context.\n" + header
        return header + body

    def _openrouter_base_and_key() -> tuple[str, str]:
        """
        Support both:
          - OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
          - OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
        """
        key = os.getenv("OPENROUTER_API_KEY", "").strip()
        base = os.getenv("OPENROUTER_BASE_URL", "").strip()
        if not base:
            api_url = os.getenv("OPENROUTER_API_URL", "").strip()
            if api_url.endswith("/chat/completions"):
                base = api_url[: -len("/chat/completions")]
        if not base:
            base = "https://openrouter.ai/api/v1"
        return base, key

    def _generate_code_via_openrouter() -> str:
        base_url, api_key = _openrouter_base_and_key()
        if not api_key:
            return _template_code()

        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip() or "openai/gpt-4o-mini"
        # Match legacy PHP default more closely
        temperature = float(os.getenv("OPENROUTER_TEMPERATURE", "0.7") or 0.7)

        # Build user prompt (match PHP behavior)
        user_prompt = prompt
        if existing:
            user_prompt = (
                "# Existing Code (modify based on this):\n\n```python\n"
                + existing.strip()
                + "\n```\n\n# Modification Requirements:\n\n"
                + prompt
                + "\n\nPlease generate complete new Python code based on the existing code above and my modification requirements. Output the complete Python code directly, without explanations, without segmentation."
            )

        payload = {
            "model": model,
            "temperature": temperature,
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }

        resp = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        j = resp.json()
        content = (((j.get("choices") or [{}])[0]).get("message") or {}).get("content") or ""
        return content.strip() or _template_code()

    def stream():
        # 不扣任何 QDT：开源本地版直接生成/返回代码
        try:
            code_text = _generate_code_via_openrouter()
        except Exception as e:
            logger.warning(f"ai_generate openrouter failed, fallback to template: {e}")
            code_text = _template_code()



@indicator_bp.route("/ma100", methods=["POST"])
def get_ma100():
    """
    Get MA100 data for a symbol.
    
    Request:
      {
        "symbol": "BTCUSDT",
        "interval": "15m",
        "limit": 1
      }
    
    Response:
      {
        "success": true,
        "data": [{
          "close": 90665.2,
          "ma100": 89500.45
        }]
      }
    """
    try:
        data = request.get_json() or {}
        symbol = data.get("symbol", "").upper()
        interval = data.get("interval", "15m")
        limit = data.get("limit", 1)
        
        if not symbol:
            return jsonify({"success": False, "error": "symbol is required"}), 400
        
        # 获取 K 线数据
        from app.services.kline import KlineService
        kline_service = KlineService()
        kline_data = kline_service.get_kline(
            market="Crypto",
            symbol=symbol,
            timeframe=interval,
            limit=200
        )
        
        if not kline_data or len(kline_data) < 100:
            return jsonify({
                "success": False,
                "error": "Insufficient data to calculate MA100"
            }), 400
        
        # 计算 MA100
        import pandas as pd
        df = pd.DataFrame(kline_data, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['ma100'] = df['close'].rolling(window=100).mean()
        
        # 获取最新的数据
        latest = df.iloc[-1].to_dict()
        
        return jsonify({
            "success": True,
            "data": [{
                "close": float(latest['close']),
                "ma100": float(latest['ma100']) if not pd.isna(latest['ma100']) else None
            }]
        })
        
    except Exception as e:
        logger.error(f"get_ma100 failed: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
