import asyncio
import time
from typing import Any

import allure
import orjson
import pytest
from api.bitopro_client import BitoProClient

pytestmark = [pytest.mark.asyncio, allure.feature("OHLC API 性能測試")]


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


class TestOHLCApiPerformance:
    """BitoPro OHLC 數據 API 性能測試類"""

    @allure.story("API 響應時間")
    @allure.title("測試 OHLC API 的響應時間")
    @allure.description("""
    測試 OHLC API 在不同參數下的響應時間
    
    API 請求:
    GET /trading-history/{pair}
    
    參數:
        pair (string, Required): 交易對，格式為 {BASE}_{QUOTE}，例如 bito_eth
        resolution (string, Required): 不同的時間框架 (1m, 5m, 15m, 30m, 1h, 1d)
        from (int64, Required): 開始時間的 Unix 時間戳
        to (int64, Required): 結束時間的 Unix 時間戳
    """)
    async def test_ohlc_api_response_time(
        self,
        bitopro_client: BitoProClient,
        test_pair: str,
        test_from_timestamp: int,
        test_to_timestamp: int,
    ):
        """測試 OHLC API 的響應時間"""
        # 定義測試參數
        resolutions = ["1m", "5m", "15m", "30m", "1h", "1d"]
        results = []

        for resolution in resolutions:
            with allure.step(f"測試時間框架 {resolution} 的響應時間"):
                start_time = time.time()

                response, req_resp = await bitopro_client.get_ohlc_data(
                    pair=test_pair,
                    resolution=resolution,
                    from_timestamp=test_from_timestamp,
                    to_timestamp=test_to_timestamp,
                )

                end_time = time.time()
                response_time = end_time - start_time

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

                results.append(
                    {
                        "resolution": resolution,
                        "response_time": response_time,
                        "data_count": len(response.get("data", [])),
                    }
                )

                allure.attach(
                    f"響應時間: {response_time:.4f} 秒\n數據點數量: {len(response.get('data', []))}",
                    f"{resolution} 響應時間",
                    allure.attachment_type.TEXT,
                )

        # 將結果添加到 Allure 報告
        with allure.step("比較不同時間框架的響應時間"):
            # 按響應時間排序
            sorted_results = sorted(results, key=lambda x: x["response_time"])

            report = "時間框架響應時間比較:\n\n"
            report += "| 時間框架 | 響應時間 (秒) | 數據點數量 |\n"
            report += "|----------|--------------|------------|\n"

            for result in sorted_results:
                report += f"| {result['resolution']} | {result['response_time']:.4f} | {result['data_count']} |\n"

            allure.attach(report, "響應時間比較", allure.attachment_type.TEXT)

    @allure.story("API 併發性能")
    @allure.title("測試 OHLC API 的併發性能")
    @allure.description("""
    測試 OHLC API 在併發請求下的性能
    
    API 請求:
    GET /trading-history/{pair}
    
    參數:
        pair (string, Required): 交易對，格式為 {BASE}_{QUOTE}，例如 bito_eth
        resolution (string, Required): 時間框架，可選值為 1m, 5m, 15m, 30m, 1h, 3h, 4h, 6h, 12h, 1d, 1w, 1M
        from (int64, Required): 開始時間的 Unix 時間戳
        to (int64, Required): 結束時間的 Unix 時間戳
        
    併發級別: 1, 5, 10
    """)
    async def test_ohlc_api_concurrent_performance(
        self,
        bitopro_client: BitoProClient,
        test_pair: str,
        test_resolution: str,
        test_from_timestamp: int,
        test_to_timestamp: int,
    ):
        """測試 OHLC API 在併發請求下的性能"""
        # 定義併發請求數
        concurrency_levels = [1, 5, 10]
        results = []

        for concurrency in concurrency_levels:
            with allure.step(f"測試併發級別 {concurrency} 的性能"):
                # 創建併發任務
                tasks = []
                for _ in range(concurrency):
                    tasks.append(
                        bitopro_client.get_ohlc_data(
                            pair=test_pair,
                            resolution=test_resolution,
                            from_timestamp=test_from_timestamp,
                            to_timestamp=test_to_timestamp,
                        )
                    )

                # 測量執行時間
                start_time = time.time()
                responses_with_req_resp = await asyncio.gather(*tasks)
                end_time = time.time()

                total_time = end_time - start_time
                avg_time = total_time / concurrency

                # 記錄請求和響應資料（僅記錄第一個請求的詳細信息）
                if responses_with_req_resp:
                    response, req_resp = responses_with_req_resp[0]
                    allure.attach(
                        safe_json_dumps(req_resp["request"]),
                        f"並發級別 {concurrency} 的請求資料示例",
                        allure.attachment_type.JSON,
                    )
                    allure.attach(
                        safe_json_dumps(req_resp["response"]),
                        f"並發級別 {concurrency} 的響應資料示例",
                        allure.attachment_type.JSON,
                    )

                results.append({"concurrency": concurrency, "total_time": total_time, "avg_time": avg_time})

                allure.attach(
                    f"總執行時間: {total_time:.4f} 秒\n平均響應時間: {avg_time:.4f} 秒",
                    f"併發級別 {concurrency} 性能",
                    allure.attachment_type.TEXT,
                )

        # 將結果添加到 Allure 報告
        with allure.step("比較不同併發級別的性能"):
            report = "併發性能比較:\n\n"
            report += "| 併發級別 | 總執行時間 (秒) | 平均響應時間 (秒) |\n"
            report += "|----------|----------------|------------------|\n"

            for result in results:
                report += f"| {result['concurrency']} | {result['total_time']:.4f} | {result['avg_time']:.4f} |\n"

            allure.attach(report, "併發性能比較", allure.attachment_type.TEXT)
