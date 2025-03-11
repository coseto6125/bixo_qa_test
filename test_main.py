import asyncio
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from orjson import loads

from bito_front.compare_bitopro_data import BitoProDataComparer
from update_module import CaseReport, update_google_sheet


def run_api_tests():
    """執行測試並生成報告"""
    # 清理之前的測試結果
    # pytest.main(["./tests/", "-v"])

    import os

    start_time = datetime.now()
    # import shutil

    # shutil.rmtree("bito_api_test/allure-results")

    # # 執行測試
    # pytest.main(
    #     [
    #         "bito_api_test/tests/",
    #         "-v",
    #         "--alluredir=bito_api_test/allure-results",
    #     ]
    # )
    # 讀取 JSON 檔案
    result_json = Path("bito_api_test/allure-results").glob("*-result.json")

    # 使用 defaultdict 簡化初始化
    test_case = defaultdict(list)

    # 解析 JSON
    for result in result_json:
        data = loads(result.read_text("utf-8"))
        test_case[data["status"]].append(data["name"])

    # 計算各狀態的數量
    fail_count = len(test_case["failed"])
    pass_count = len(test_case["passed"])
    skip_count = len(test_case["skipped"])
    known_count = len(test_case["known"])
    broken_count = len(test_case["broken"])

    # 生成報告
    os.system("allure generate bito_api_test/allure-results -o bito_api_test/allure-report --clean --single-file")

    # 打開報告
    # os.system("start ./allure-report/index.html")
    end_time = datetime.now()
    run_time = end_time - start_time
    case_report = CaseReport(
        Platform="Production",
        CaseName="API_TEST_public/get_ohlc_data",
        Fail=fail_count,
        Broken=broken_count,
        Skip=skip_count,
        Pass=pass_count,
        Known=known_count,
        Link="http://localhost:8000/allure-report/index.html",
        StartTime=start_time,
        RunTime=run_time,
        EndTime=end_time,
    )
    update_google_sheet(case_report, "生產環境")


async def run_front_tests():
    """執行前端測試並生成報告"""
    start_time = datetime.now()

    comparer = BitoProDataComparer()
    await comparer.run()

    end_time = datetime.now()
    run_time = end_time - start_time
    case_report = CaseReport(
        Platform="Production",
        CaseName="front_test_/ns/fees",
        Fail=comparer.failed_checks,
        Broken=0,
        Skip=0,
        Pass=comparer.passed_checks,
        Known=0,
        Link=f"http://localhost:8000/{comparer.report_path}",
        StartTime=start_time,
        RunTime=run_time,
        EndTime=end_time,
    )
    update_google_sheet(case_report, "生產環境2")


if __name__ == "__main__":
    asyncio.run(run_front_tests()) # 執行前端測試
    run_api_tests() # 執行API測試
