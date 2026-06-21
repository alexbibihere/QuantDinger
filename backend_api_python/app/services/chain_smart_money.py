"""
链上聪明钱 (On-chain Smart Money) 数据服务
调用 Binance Web3 API 获取链上聪明钱买卖信号
支持 Solana 和 BSC 链
"""
import requests
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

API_URL = "https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/web/signal/smart-money/ai"
HEADERS = {
    "Content-Type": "application/json",
    "Accept-Encoding": "identity",
    "User-Agent": "binance-web3/1.1 (Skill)",
}

# 使用的代理
SMART_MONEY_PROXY = "socks5://127.0.0.1:7891"


def get_smart_money_signals(
    chain_id: str = "CT_501",
    page: int = 1,
    page_size: int = 10,
    signal_type: str = "",
) -> Optional[list]:
    """
    获取链上聪明钱信号

    Args:
        chain_id: CT_501 = Solana, 56 = BSC
        page: 页码
        page_size: 每页数量 (max 100)
        signal_type: 信号类型过滤

    Returns:
        list of signal dicts, 或 None
    """
    try:
        resp = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "smartSignalType": signal_type,
                "page": page,
                "pageSize": page_size,
                "chainId": chain_id,
            },
            proxies={"http": SMART_MONEY_PROXY, "https": SMART_MONEY_PROXY},
            timeout=15,
        )

        if resp.status_code != 200:
            logger.warning(f"链上聪明钱 API 返回 {resp.status_code}: {resp.text[:200]}")
            return None

        data = resp.json()
        if data.get("code") != "000000":
            logger.warning(f"链上聪明钱 API 异常: {data.get('message', '未知错误')}")
            return None

        return _format_signals(data.get("data", []))

    except requests.exceptions.Timeout:
        logger.warning("链上聪明钱 API 超时")
        return None
    except Exception as e:
        logger.error(f"链上聪明钱 API 错误: {e}")
        return None


def _format_signals(raw_signals: list) -> list:
    """格式化原始信号数据"""
    result = []
    for s in raw_signals:
        result.append(
            {
                "signalId": s.get("signalId"),
                "symbol": s.get("ticker"),
                "chainId": s.get("chainId"),
                "contractAddress": s.get("contractAddress"),
                "direction": s.get("direction"),  # buy / sell
                "smartMoneyCount": s.get("smartMoneyCount"),
                "signalCount": s.get("signalCount"),
                "currentPrice": s.get("currentPrice"),
                "alertPrice": s.get("alertPrice"),
                "alertMarketCap": s.get("alertMarketCap"),
                "currentMarketCap": s.get("currentMarketCap"),
                "highestPrice": s.get("highestPrice"),
                "maxGain": s.get("maxGain"),
                "exitRate": s.get("exitRate"),
                "status": s.get("status"),  # active / timeout / completed
                "timeFrame": s.get("timeFrame"),
                "signalTriggerTime": s.get("signalTriggerTime"),
                "totalTokenValue": s.get("totalTokenValue"),
                "launchPlatform": s.get("launchPlatform"),
                "tokenTags": s.get("tokenTag", {}),
            }
        )
    return result


def get_recent_signals(page_size: int = 5) -> dict:
    """一次性获取 Solana 和 BSC 的最新聪明钱信号"""
    result = {}

    solana_data = get_smart_money_signals(
        chain_id="CT_501", page=1, page_size=page_size
    )
    if solana_data is not None:
        result["solana"] = solana_data

    bsc_data = get_smart_money_signals(chain_id="56", page=1, page_size=page_size)
    if bsc_data is not None:
        result["bsc"] = bsc_data

    result["_count"] = {
        "solana": len(result.get("solana", [])),
        "bsc": len(result.get("bsc", [])),
    }
    return result
