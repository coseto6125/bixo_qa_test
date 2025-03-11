from datetime import datetime
from typing import Any

import allure
import orjson
import pytest
from aiohttp import ClientResponseError
from api.bitopro_client import BitoProClient

pytestmark = [pytest.mark.asyncio, allure.feature("OHLC API")]


def safe_json_dumps(data: Any) -> str:
    """
    安全地將數據轉換為 JSON 字符串，確保所有字典的鍵都是字符串

    Args:
        data: 要轉換的數據

    Returns:
        JSON 字符串
    """
    try:
        return orjson.dumps(data, option=orjson.OPT_INDENT_2).decode("utf-8")
    except TypeError:
        # 如果有非字符串鍵，則將其轉換為字符串
        if isinstance(data, dict):
            return orjson.dumps(
                {str(k): safe_json_dumps(v) if isinstance(v, dict) else v for k, v in data.items()},
                option=orjson.OPT_INDENT_2,
            ).decode("utf-8")
        elif isinstance(data, list):
            return orjson.dumps(
                [safe_json_dumps(item) if isinstance(item, dict) else item for item in data], option=orjson.OPT_INDENT_2
            ).decode("utf-8")
        else:
            raise


class TestOHLCApi:
    """BitoPro OHLC 數據 API 測試類"""

    @allure.story("獲取 OHLC 數據")
    @allure.title("測試獲取有效的 OHLC 數據")
    @allure.description("""
    測試使用有效參數獲取 OHLC 數據
    
    API 請求:
    GET /trading-history/{pair}
    
    參數:
        pair (string, Required): 交易對，格式為 {BASE}_{QUOTE}，例如 bito_eth
        resolution (string, Required): 時間框架，可選值為 1m, 5m, 15m, 30m, 1h, 3h, 4h, 6h, 12h, 1d, 1w, 1M
        from (int64, Required): 開始時間的 Unix 時間戳
        to (int64, Required): 結束時間的 Unix 時間戳
    """)
    async def test_get_ohlc_data_valid_params(self, gather_all_test_data: dict[str, Any]):
        """測試使用有效參數獲取 OHLC 數據"""
        # 檢查是否成功獲取數據
        assert "error" not in gather_all_test_data, f"獲取測試數據失敗: {gather_all_test_data.get('error')}"

        # 使用預先獲取的數據
        response = gather_all_test_data["valid_data"]
        req_resp = gather_all_test_data["valid_req_resp"]

        # 記錄請求和響應資料
        with allure.step("記錄請求和響應資料"):
            allure.attach(
                safe_json_dumps(req_resp["request"]),
                "請求資料",
                allure.attachment_type.JSON,
            )
            allure.attach(
                safe_json_dumps(req_resp["response"]),
                "響應資料",
                allure.attachment_type.JSON,
            )

        with allure.step("驗證響應格式"):
            assert isinstance(response, dict), "響應應該是一個字典"
            assert "data" in response, "響應應該包含 'data' 字段"
            assert isinstance(response["data"], list), "'data' 字段應該是一個列表"

        if response["data"]:
            with allure.step("驗證 OHLC 數據格式"):
                first_item = response["data"][0]
                assert "timestamp" in first_item, "OHLC 數據應該包含 'timestamp' 字段"
                assert "open" in first_item, "OHLC 數據應該包含 'open' 字段"
                assert "high" in first_item, "OHLC 數據應該包含 'high' 字段"
                assert "low" in first_item, "OHLC 數據應該包含 'low' 字段"
                assert "close" in first_item, "OHLC 數據應該包含 'close' 字段"
                assert "volume" in first_item, "OHLC 數據應該包含 'volume' 字段"

                # 將時間戳轉換為可讀格式並添加到 Allure 報告
                timestamp = first_item["timestamp"]
                readable_time = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
                allure.attach(
                    safe_json_dumps(first_item),
                    f"OHLC 數據示例 ({readable_time})",
                    allure.attachment_type.JSON,
                )

    @allure.story("獲取 OHLC 數據")
    @allure.title("測試獲取 OHLC 數據時使用無效的交易對")
    @allure.description("""
    測試使用無效的交易對獲取 OHLC 數據時的錯誤處理
    
    API 請求:
    GET /trading-history/{pair}
    
    參數:
        pair (string, Required): 無效的交易對
        resolution (string, Required): 有效的時間框架
        from (int64, Required): 有效的開始時間戳
        to (int64, Required): 有效的結束時間戳
    """)
    async def test_get_ohlc_data_invalid_pair(
        self, bitopro_client: BitoProClient, test_resolution: str, test_from_timestamp: int, test_to_timestamp: int
    ):
        """測試使用無效的交易對獲取 OHLC 數據時的錯誤處理"""
        invalid_pair = "invalid_pair"

        with allure.step(f"嘗試獲取無效交易對 {invalid_pair} 的 OHLC 數據"):
            try:
                data, req_resp = await bitopro_client.get_ohlc_data(
                    pair=invalid_pair,
                    resolution=test_resolution,
                    from_timestamp=test_from_timestamp,
                    to_timestamp=test_to_timestamp,
                )

                # 記錄請求和響應資料
                allure.attach(
                    safe_json_dumps(req_resp["request"]),
                    "請求資料",
                    allure.attachment_type.JSON,
                )
                allure.attach(
                    safe_json_dumps(req_resp["response"]),
                    "響應資料",
                    allure.attachment_type.JSON,
                )

                # 如果沒有引發異常，則測試失敗
                pytest.fail(f"應該引發異常，但獲取到了數據: {data}")
            except ClientResponseError as e:
                # 記錄錯誤信息
                allure.attach(
                    str(e),
                    "錯誤信息",
                    allure.attachment_type.TEXT,
                )
                # 如果有響應內容，也記錄下來
                if hasattr(e, "headers"):
                    allure.attach(
                        safe_json_dumps({"headers": dict(e.headers)} if e.headers else {}),
                        "錯誤響應標頭",
                        allure.attachment_type.JSON,
                    )
                if hasattr(e, "message"):
                    allure.attach(
                        str(e.message),
                        "錯誤響應訊息",
                        allure.attachment_type.TEXT,
                    )
            except Exception as e:
                # 記錄其他類型的錯誤信息
                allure.attach(
                    str(e),
                    "錯誤信息",
                    allure.attachment_type.TEXT,
                )

    @allure.story("獲取 OHLC 數據")
    @allure.title("測試獲取 OHLC 數據時使用無效的時間框架")
    @allure.description("""
    測試使用無效的時間框架獲取 OHLC 數據時的錯誤處理
    
    API 請求:
    GET /trading-history/{pair}
    
    參數:
        pair (string, Required): 有效的交易對
        resolution (string, Required): 無效的時間框架
        from (int64, Required): 有效的開始時間戳
        to (int64, Required): 有效的結束時間戳
    """)
    async def test_get_ohlc_data_invalid_resolution(
        self, bitopro_client: BitoProClient, test_pair: str, test_from_timestamp: int, test_to_timestamp: int
    ):
        """測試使用無效的時間框架獲取 OHLC 數據時的錯誤處理"""
        invalid_resolution = "invalid_resolution"

        with allure.step(f"嘗試使用無效的時間框架 {invalid_resolution} 獲取 OHLC 數據"):
            try:
                data, req_resp = await bitopro_client.get_ohlc_data(
                    pair=test_pair,
                    resolution=invalid_resolution,
                    from_timestamp=test_from_timestamp,
                    to_timestamp=test_to_timestamp,
                )

                # 記錄請求和響應資料
                allure.attach(
                    safe_json_dumps(req_resp["request"]),
                    "請求資料",
                    allure.attachment_type.JSON,
                )
                allure.attach(
                    safe_json_dumps(req_resp["response"]),
                    "響應資料",
                    allure.attachment_type.JSON,
                )

                # 如果沒有引發異常，則測試失敗
                pytest.fail(f"應該引發異常，但獲取到了數據: {data}")
            except ClientResponseError as e:
                # 記錄錯誤信息
                allure.attach(
                    str(e),
                    "錯誤信息",
                    allure.attachment_type.TEXT,
                )
                # 如果有響應內容，也記錄下來
                if hasattr(e, "headers"):
                    allure.attach(
                        safe_json_dumps({"headers": dict(e.headers)} if e.headers else {}),
                        "錯誤響應標頭",
                        allure.attachment_type.JSON,
                    )
                if hasattr(e, "message"):
                    allure.attach(
                        str(e.message),
                        "錯誤響應訊息",
                        allure.attachment_type.TEXT,
                    )
            except Exception as e:
                # 記錄其他類型的錯誤信息
                allure.attach(
                    str(e),
                    "錯誤信息",
                    allure.attachment_type.TEXT,
                )

    @allure.story("獲取 OHLC 數據")
    @allure.title("測試獲取 OHLC 數據時使用無效的時間範圍")
    @allure.description("""
    測試使用無效的時間範圍獲取 OHLC 數據時的錯誤處理
    
    API 請求:
    GET /trading-history/{pair}
    
    參數:
        pair (string, Required): 有效的交易對
        resolution (string, Required): 有效的時間框架
        from (int64, Required): 晚於結束時間的開始時間戳
        to (int64, Required): 早於開始時間的結束時間戳
    """)
    async def test_get_ohlc_data_invalid_time_range(
        self, bitopro_client: BitoProClient, test_pair: str, test_resolution: str
    ):
        """測試使用無效的時間範圍獲取 OHLC 數據時的錯誤處理"""
        # 結束時間早於開始時間
        from_timestamp = 1609545600  # 2021-01-02 00:00:00 UTC
        to_timestamp = 1609459200  # 2021-01-01 00:00:00 UTC

        with allure.step(f"嘗試使用無效的時間範圍獲取 OHLC 數據 (從 {from_timestamp} 到 {to_timestamp})"):
            try:
                data, req_resp = await bitopro_client.get_ohlc_data(
                    pair=test_pair,
                    resolution=test_resolution,
                    from_timestamp=from_timestamp,
                    to_timestamp=to_timestamp,
                )

                # 記錄請求和響應資料
                allure.attach(
                    safe_json_dumps(req_resp["request"]),
                    "請求資料",
                    allure.attachment_type.JSON,
                )
                allure.attach(
                    safe_json_dumps(req_resp["response"]),
                    "響應資料",
                    allure.attachment_type.JSON,
                )

                # 如果沒有引發異常，則測試失敗
                pytest.fail(f"應該引發異常，但獲取到了數據: {data}")
            except ClientResponseError as e:
                # 記錄錯誤信息
                allure.attach(
                    str(e),
                    "錯誤信息",
                    allure.attachment_type.TEXT,
                )
                # 如果有響應內容，也記錄下來
                if hasattr(e, "headers"):
                    allure.attach(
                        safe_json_dumps({"headers": dict(e.headers)} if e.headers else {}),
                        "錯誤響應標頭",
                        allure.attachment_type.JSON,
                    )
                if hasattr(e, "message"):
                    allure.attach(
                        str(e.message),
                        "錯誤響應訊息",
                        allure.attachment_type.TEXT,
                    )
            except Exception as e:
                # 記錄其他類型的錯誤信息
                allure.attach(
                    str(e),
                    "錯誤信息",
                    allure.attachment_type.TEXT,
                )

    @allure.story("獲取 OHLC 數據")
    @allure.title("測試獲取 OHLC 數據時使用所有有效的時間框架")
    @allure.description("""
    測試使用所有有效的時間框架獲取 OHLC 數據
    
    API 請求:
    GET /trading-history/{pair}
    
    參數:
        pair (string, Required): 有效的交易對
        resolution (string, Required): 所有有效的時間框架 (1m, 5m, 15m, 30m, 1h, 3h, 4h, 6h, 12h, 1d, 1w, 1M)
        from (int64, Required): 有效的開始時間戳
        to (int64, Required): 有效的結束時間戳
    """)
    async def test_get_ohlc_data_all_resolutions(
        self, gather_all_test_data: dict[str, Any], all_resolutions: list[str]
    ):
        """測試使用所有有效的時間框架獲取 OHLC 數據"""
        # 檢查是否成功獲取數據
        assert "error" not in gather_all_test_data, f"獲取測試數據失敗: {gather_all_test_data.get('error')}"

        # 使用預先獲取的數據
        resolution_data = gather_all_test_data["resolution_data"]
        resolution_req_resp = gather_all_test_data["resolution_req_resp"]

        for resolution in all_resolutions:
            with allure.step(f"驗證時間框架 {resolution} 的 OHLC 數據"):
                assert resolution in resolution_data, f"缺少時間框架 {resolution} 的數據"

                # 記錄請求和響應資料
                if resolution in resolution_req_resp and "error" not in resolution_req_resp[resolution]:
                    allure.attach(
                        safe_json_dumps(resolution_req_resp[resolution]["request"]),
                        f"時間框架 {resolution} 的請求資料",
                        allure.attachment_type.JSON,
                    )
                    allure.attach(
                        safe_json_dumps(resolution_req_resp[resolution]["response"]),
                        f"時間框架 {resolution} 的響應資料",
                        allure.attachment_type.JSON,
                    )

                # 檢查是否有錯誤
                if "error" in resolution_data[resolution]:
                    allure.attach(
                        str(resolution_data[resolution]["error"]),
                        f"時間框架 {resolution} 的錯誤信息",
                        allure.attachment_type.TEXT,
                    )
                    continue

                data = resolution_data[resolution]
                assert isinstance(data, dict), "響應應該是一個字典"
                assert "data" in data, "響應應該包含 'data' 字段"
                assert isinstance(data["data"], list), "'data' 字段應該是一個列表"

                # 添加數據點數量到報告
                allure.attach(
                    f"數據點數量: {len(data['data'])}",
                    f"時間框架 {resolution} 的數據點數量",
                    allure.attachment_type.TEXT,
                )

                # 添加第一個數據點到報告（如果有）
                if data["data"]:
                    first_item = data["data"][0]
                    timestamp = first_item["timestamp"]
                    readable_time = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    allure.attach(
                        safe_json_dumps(first_item),
                        f"時間框架 {resolution} 的第一個數據點 ({readable_time})",
                        allure.attachment_type.JSON,
                    )

    @allure.story("獲取 OHLC 數據")
    @allure.title("測試獲取 OHLC 數據時使用 INT64 邊界值")
    @allure.description("""
    測試使用 INT64 邊界值獲取 OHLC 數據時的錯誤處理
    
    API 請求:
    GET /trading-history/{pair}
    
    參數:
        pair (string, Required): 有效的交易對
        resolution (string, Required): 有效的時間框架
        from (int64, Required): INT64 邊界值
        to (int64, Required): 有效的結束時間戳
    """)
    async def test_get_ohlc_data_int64_edge_cases(
        self,
        bitopro_client: BitoProClient,
        test_pair: str,
        test_resolution: str,
        test_to_timestamp: int,
        int64_edge_cases: dict[str, int],
    ):
        """測試使用 INT64 邊界值獲取 OHLC 數據時的錯誤處理"""
        # 測試 from_timestamp 的邊界值
        for case_name, value in int64_edge_cases.items():
            with allure.step(f"測試 from_timestamp 的邊界值: {case_name} = {value}"):
                try:
                    data, req_resp = await bitopro_client.get_ohlc_data(
                        pair=test_pair,
                        resolution=test_resolution,
                        from_timestamp=value,
                        to_timestamp=test_to_timestamp,
                    )

                    # 記錄請求和響應資料
                    allure.attach(
                        safe_json_dumps(req_resp["request"]),
                        f"from_timestamp = {value} 的請求資料",
                        allure.attachment_type.JSON,
                    )
                    allure.attach(
                        safe_json_dumps(req_resp["response"]),
                        f"from_timestamp = {value} 的響應資料",
                        allure.attachment_type.JSON,
                    )

                    allure.attach(
                        f"成功獲取數據，數據點數量: {len(data.get('data', []))}",
                        f"from_timestamp = {value} 的響應",
                        allure.attachment_type.TEXT,
                    )

                except ClientResponseError as e:
                    # 記錄錯誤信息
                    allure.attach(
                        str(e),
                        f"from_timestamp = {value} 的錯誤信息",
                        allure.attachment_type.TEXT,
                    )
                    # 如果有響應內容，也記錄下來
                    if hasattr(e, "headers"):
                        allure.attach(
                            safe_json_dumps({"headers": dict(e.headers)} if e.headers else {}),
                            f"from_timestamp = {value} 的錯誤響應標頭",
                            allure.attachment_type.JSON,
                        )
                    if hasattr(e, "message"):
                        allure.attach(
                            str(e.message),
                            f"from_timestamp = {value} 的錯誤響應訊息",
                            allure.attachment_type.TEXT,
                        )
                except Exception as e:
                    # 記錄其他類型的錯誤信息
                    allure.attach(
                        str(e),
                        f"from_timestamp = {value} 的錯誤信息",
                        allure.attachment_type.TEXT,
                    )

    @allure.story("獲取 OHLC 數據")
    @allure.title("測試獲取 OHLC 數據時的 SQL 注入防禦")
    @allure.description("""
    測試 OHLC 數據 API 對 SQL 注入攻擊的防禦
    
    API 請求:
    GET /trading-history/{pair}
    
    參數:
        pair (string, Required): 包含 SQL 注入攻擊的交易對
        resolution (string, Required): 有效的時間框架
        from (int64, Required): 有效的開始時間戳
        to (int64, Required): 有效的結束時間戳
    """)
    async def test_get_ohlc_data_sql_injection(
        self,
        bitopro_client: BitoProClient,
        test_resolution: str,
        test_from_timestamp: int,
        test_to_timestamp: int,
        sql_injection_payloads: list[str],
    ):
        """測試 OHLC 數據 API 對 SQL 注入攻擊的防禦"""
        for payload in sql_injection_payloads:
            with allure.step(f"測試 SQL 注入攻擊: {payload}"):
                try:
                    data, req_resp = await bitopro_client.get_ohlc_data(
                        pair=payload,
                        resolution=test_resolution,
                        from_timestamp=test_from_timestamp,
                        to_timestamp=test_to_timestamp,
                    )

                    # 記錄請求和響應資料
                    allure.attach(
                        safe_json_dumps(req_resp["request"]),
                        f"SQL 注入攻擊 '{payload}' 的請求資料",
                        allure.attachment_type.JSON,
                    )
                    allure.attach(
                        safe_json_dumps(req_resp["response"]),
                        f"SQL 注入攻擊 '{payload}' 的響應資料",
                        allure.attachment_type.JSON,
                    )

                    # 如果成功獲取數據，檢查是否有敏感信息洩露
                    if "data" in data:
                        allure.attach(
                            f"成功獲取數據，數據點數量: {len(data.get('data', []))}",
                            f"SQL 注入攻擊 '{payload}' 的響應",
                            allure.attachment_type.TEXT,
                        )

                except ClientResponseError as e:
                    # 記錄錯誤信息
                    error_msg = str(e)
                    allure.attach(
                        error_msg,
                        f"SQL 注入攻擊 '{payload}' 的錯誤信息",
                        allure.attachment_type.TEXT,
                    )
                    # 如果有響應內容，也記錄下來
                    if hasattr(e, "headers"):
                        allure.attach(
                            safe_json_dumps({"headers": dict(e.headers)} if e.headers else {}),
                            f"SQL 注入攻擊 '{payload}' 的錯誤響應標頭",
                            allure.attachment_type.JSON,
                        )
                    if hasattr(e, "message"):
                        allure.attach(
                            str(e.message),
                            f"SQL 注入攻擊 '{payload}' 的錯誤響應訊息",
                            allure.attachment_type.TEXT,
                        )

                    # 檢查錯誤消息是否包含敏感信息
                    sensitive_keywords = [
                        "SQL",
                        "syntax",
                        "database",
                        "query",
                        "select",
                        "insert",
                        "update",
                        "delete",
                        "drop",
                    ]
                    contains_sensitive_info = any(
                        keyword.lower() in error_msg.lower() for keyword in sensitive_keywords
                    )

                    if contains_sensitive_info:
                        allure.attach(
                            f"錯誤消息包含敏感信息: {error_msg}",
                            f"SQL 注入攻擊 '{payload}' 的安全風險",
                            allure.attachment_type.TEXT,
                        )

                except Exception as e:
                    # 記錄其他類型的錯誤信息
                    error_msg = str(e)
                    allure.attach(
                        error_msg,
                        f"SQL 注入攻擊 '{payload}' 的錯誤信息",
                        allure.attachment_type.TEXT,
                    )

    @allure.story("獲取 OHLC 數據")
    @allure.title("測試 OHLC 數據 API 的必填參數驗證")
    @allure.description("""
    測試 OHLC 數據 API 的必填參數驗證
    
    API 請求:
    GET /trading-history/{pair}
    
    參數:
        pair (string, Required): 交易對，格式為 {BASE}_{QUOTE}，例如 bito_eth
        resolution (string, Required): 時間框架，可選值為 1m, 5m, 15m, 30m, 1h, 3h, 4h, 6h, 12h, 1d, 1w, 1M
        from (int64, Required): 開始時間的 Unix 時間戳
        to (int64, Required): 結束時間的 Unix 時間戳
    """)
    async def test_get_ohlc_data_required_params(
        self,
        bitopro_client: BitoProClient,
        test_pair: str,
        test_resolution: str,
        test_from_timestamp: int,
        test_to_timestamp: int,
    ):
        """測試 OHLC 數據 API 的必填參數驗證"""
        test_cases = [
            {
                "name": "缺少 pair 參數",
                "params": {
                    "pair": "",
                    "resolution": test_resolution,
                    "from_timestamp": test_from_timestamp,
                    "to_timestamp": test_to_timestamp,
                },
            },
            {
                "name": "缺少 resolution 參數",
                "params": {
                    "pair": test_pair,
                    "resolution": "",
                    "from_timestamp": test_from_timestamp,
                    "to_timestamp": test_to_timestamp,
                },
            },
            {
                "name": "缺少 from_timestamp 參數",
                "params": {
                    "pair": test_pair,
                    "resolution": test_resolution,
                    "from_timestamp": None,
                    "to_timestamp": test_to_timestamp,
                },
            },
            {
                "name": "缺少 to_timestamp 參數",
                "params": {
                    "pair": test_pair,
                    "resolution": test_resolution,
                    "from_timestamp": test_from_timestamp,
                    "to_timestamp": None,
                },
            },
        ]

        for test_case in test_cases:
            with allure.step(f"測試 {test_case['name']}"):
                try:
                    data, req_resp = await bitopro_client.get_ohlc_data(**test_case["params"])

                    # 記錄請求和響應資料
                    allure.attach(
                        safe_json_dumps(req_resp["request"]),
                        f"{test_case['name']} 的請求資料",
                        allure.attachment_type.JSON,
                    )
                    allure.attach(
                        safe_json_dumps(req_resp["response"]),
                        f"{test_case['name']} 的響應資料",
                        allure.attachment_type.JSON,
                    )

                    # 如果沒有引發異常，則測試失敗
                    pytest.fail(f"應該引發異常，但獲取到了數據: {data}")

                except ClientResponseError as e:
                    # 記錄錯誤信息
                    allure.attach(
                        str(e),
                        f"{test_case['name']} 的錯誤信息",
                        allure.attachment_type.TEXT,
                    )
                    # 如果有響應內容，也記錄下來
                    if hasattr(e, "headers"):
                        allure.attach(
                            safe_json_dumps({"headers": dict(e.headers)} if e.headers else {}),
                            f"{test_case['name']} 的錯誤響應標頭",
                            allure.attachment_type.JSON,
                        )
                    if hasattr(e, "message"):
                        allure.attach(
                            str(e.message),
                            f"{test_case['name']} 的錯誤響應訊息",
                            allure.attachment_type.TEXT,
                        )
                except Exception as e:
                    # 記錄其他類型的錯誤信息
                    allure.attach(
                        str(e),
                        f"{test_case['name']} 的錯誤信息",
                        allure.attachment_type.TEXT,
                    )
