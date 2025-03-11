from loguru import logger
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
import orjson


class BitoProClient:
    """BitoPro API 客戶端類，用於與 BitoPro API 進行交互"""

    BASE_URL = "https://api.bitopro.com/v3"

    # 有效的時間框架列表（僅用於參考，不再用於驗證）
    VALID_RESOLUTIONS = ["1m", "5m", "15m", "30m", "1h", "3h", "4h", "6h", "12h", "1d", "1w", "1M"]

    # INT64 的範圍（僅用於參考，不再用於驗證）
    INT64_MIN = -9223372036854775808
    INT64_MAX = 9223372036854775807

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        """
        初始化 BitoPro API 客戶端

        Args:
            session: 可選的 aiohttp.ClientSession 實例，如果未提供，將創建一個新的
        """
        self._session = session
        self._logger = logger

    async def __aenter__(self):
        if self._session is None:
            self._session = aiohttp.ClientSession(json_serialize=orjson.dumps)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session is not None:
            await self._session.close()
            self._session = None

    def _convert_headers_to_str_keys(self, headers: Dict) -> Dict[str, Any]:
        """
        將標頭字典的鍵轉換為字符串

        Args:
            headers: 標頭字典

        Returns:
            鍵為字符串的標頭字典
        """
        return {str(k): v for k, v in headers.items()}

    async def get_ohlc_data(
        self, pair: str, resolution: str, from_timestamp: int, to_timestamp: int
    ) -> Tuple[Dict[str, List[Dict[str, Union[int, str]]]], Dict[str, Any]]:
        """
        獲取指定交易對的 OHLC 數據

        API 請求:
        GET /trading-history/{pair}

        參數:
            pair (string, Required): 交易對，格式為 {BASE}_{QUOTE}，例如 bito_eth
            resolution (string, Required): 時間框架，可選值為 1m, 5m, 15m, 30m, 1h, 3h, 4h, 6h, 12h, 1d, 1w, 1M
            from (int64, Required): 開始時間的 Unix 時間戳
            to (int64, Required): 結束時間的 Unix 時間戳

        Returns:
            包含 OHLC 數據的字典，格式如下:
            {
                "data": [
                    {
                        "timestamp": 1551052800000,
                        "open": "4099.99",
                        "high": "4444.47",
                        "low": "3875.32",
                        "close": "3955.8",
                        "volume": "13.35162928"
                    },
                    ...
                ]
            }

            以及包含請求和響應詳細信息的字典
        """
        if self._session is None:
            raise RuntimeError("Session is not initialized. Use 'async with' context manager.")

        # 不再進行客戶端驗證，直接發送請求到伺服器
        endpoint = f"/trading-history/{pair}"
        params = {"resolution": resolution, "from": from_timestamp, "to": to_timestamp}

        url = f"{self.BASE_URL}{endpoint}"
        self._logger.info(f"Requesting OHLC data: {url} with params: {params}")

        # 記錄請求詳細信息
        request_info = {"method": "GET", "url": url, "params": params, "headers": {}}

        response_info = {}

        try:
            async with self._session.get(url, params=params) as response:
                # 記錄響應詳細信息
                response_info = {
                    "status": response.status,
                    "headers": self._convert_headers_to_str_keys(response.headers),
                    "url": str(response.url),
                }

                response.raise_for_status()
                data = await response.json(loads=orjson.loads)
                response_info["body"] = data
                self._logger.debug(f"Received OHLC data: {data}")
                return data, {"request": request_info, "response": response_info}
        except aiohttp.ClientResponseError as e:
            # 記錄錯誤響應
            try:
                # 嘗試獲取響應內容
                error_response = await e.response.json(loads=orjson.loads)
            except Exception:
                try:
                    # 如果無法解析為 JSON，則獲取原始文本
                    error_response = await e.response.text()
                except Exception:
                    error_response = "無法獲取響應內容"

            response_info["error"] = {
                "status": e.status,
                "message": str(e),
                "headers": self._convert_headers_to_str_keys(e.headers) if hasattr(e, "headers") else {},
                "body": error_response,
            }
            self._logger.error(f"Error requesting OHLC data: {e}")
            raise
        except Exception as e:
            # 記錄其他錯誤
            response_info["error"] = {"message": str(e), "type": type(e).__name__}
            self._logger.error(f"Unexpected error requesting OHLC data: {e}")
            raise
