from typing import Any, AsyncGenerator, Dict, List

import aiohttp
import allure
import orjson
import pytest
import pytest_asyncio
from api.bitopro_client import BitoProClient


@pytest_asyncio.fixture
async def aiohttp_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """提供一個 aiohttp.ClientSession 實例"""
    session = aiohttp.ClientSession()
    try:
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture
async def bitopro_client(aiohttp_session) -> AsyncGenerator[BitoProClient, None]:
    """提供一個 BitoProClient 實例"""
    async with BitoProClient(session=aiohttp_session) as client:
        yield client


# 定義測試數據
@pytest.fixture
def test_pair() -> str:
    """測試用的交易對"""
    return "btc_twd"


@pytest.fixture
def test_resolution() -> str:
    """測試用的時間框架"""
    return "1h"


@pytest.fixture
def test_from_timestamp() -> int:
    """測試用的開始時間戳"""
    return 1609459200  # 2021-01-01 00:00:00 UTC


@pytest.fixture
def test_to_timestamp() -> int:
    """測試用的結束時間戳"""
    return 1609545600  # 2021-01-02 00:00:00 UTC


@pytest.fixture
def all_resolutions() -> List[str]:
    """所有有效的時間框架"""
    return ["1m", "5m", "15m", "30m", "1h", "3h", "4h", "6h", "12h", "1d", "1w", "1M"]


@pytest.fixture
def sql_injection_payloads() -> List[str]:
    """SQL 注入測試的有效載荷"""
    return [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM information_schema.tables; --",
        "' OR '1'='1' --",
        "admin' --",
        "1' OR '1' = '1",
        "1 OR 1=1",
        "' OR 1=1 --",
        "' OR 'a'='a",
        "') OR ('a'='a",
    ]


@pytest.fixture
def int64_edge_cases() -> Dict[str, int]:
    """INT64 邊界值測試用例"""
    return {
        "min": -9223372036854775808,  # INT64_MIN
        "max": 9223372036854775807,  # INT64_MAX
        "overflow": 9223372036854775808,  # INT64_MAX + 1
        "underflow": -9223372036854775809,  # INT64_MIN - 1
        "zero": 0,
        "negative": -1,
        "positive": 1,
    }


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


@pytest_asyncio.fixture
async def gather_all_test_data(
    bitopro_client: BitoProClient,
    test_pair: str,
    test_resolution: str,
    test_from_timestamp: int,
    test_to_timestamp: int,
) -> Dict[str, Any]:
    """
    預先獲取所有測試數據，以便在測試中重複使用

    Returns:
        包含所有測試數據的字典
    """
    try:
        # 獲取有效參數的 OHLC 數據
        with allure.step("獲取有效參數的 OHLC 數據"):
            valid_data, valid_req_resp = await bitopro_client.get_ohlc_data(
                pair=test_pair,
                resolution=test_resolution,
                from_timestamp=test_from_timestamp,
                to_timestamp=test_to_timestamp,
            )

            # 記錄請求和響應資料
            allure.attach(
                safe_json_dumps(valid_req_resp["request"]), "獲取有效測試數據的請求", allure.attachment_type.JSON
            )
            allure.attach(
                safe_json_dumps(valid_req_resp["response"]), "獲取有效測試數據的響應", allure.attachment_type.JSON
            )

        # 獲取所有時間框架的 OHLC 數據
        resolution_data = {}
        resolution_req_resp = {}

        with allure.step("獲取所有時間框架的 OHLC 數據"):
            for resolution in BitoProClient.VALID_RESOLUTIONS:
                try:
                    data, req_resp = await bitopro_client.get_ohlc_data(
                        pair=test_pair,
                        resolution=resolution,
                        from_timestamp=test_from_timestamp,
                        to_timestamp=test_to_timestamp,
                    )
                    resolution_data[resolution] = data
                    resolution_req_resp[resolution] = req_resp

                    # 記錄請求和響應資料
                    allure.attach(
                        safe_json_dumps(req_resp["request"]),
                        f"時間框架 {resolution} 的請求資料",
                        allure.attachment_type.JSON,
                    )
                    allure.attach(
                        safe_json_dumps(req_resp["response"]),
                        f"時間框架 {resolution} 的響應資料",
                        allure.attachment_type.JSON,
                    )
                except Exception as e:
                    resolution_data[resolution] = {"error": str(e)}
                    resolution_req_resp[resolution] = {"error": str(e)}

                    # 記錄錯誤
                    allure.attach(
                        f"獲取時間框架 {resolution} 的數據時發生錯誤: {str(e)}",
                        f"時間框架 {resolution} 錯誤",
                        allure.attachment_type.TEXT,
                    )

        return {
            "valid_data": valid_data,
            "valid_req_resp": valid_req_resp,
            "resolution_data": resolution_data,
            "resolution_req_resp": resolution_req_resp,
        }
    except Exception as e:
        # 如果獲取數據失敗，返回錯誤信息
        allure.attach(f"獲取測試數據時發生錯誤: {str(e)}", "錯誤", allure.attachment_type.TEXT)
        return {"error": str(e)}
