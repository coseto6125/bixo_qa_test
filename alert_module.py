from datetime import datetime

import aiohttp
import orjson

from update_module import CaseReport

WEBHOOK_URL = "https://hooks.slack.com/services/T00000000/B00000000/X00000000"


async def send_slack_message(case_report: CaseReport, webhook_url=WEBHOOK_URL):
    message = parse_case2slack(case_report)
    headers = {"Content-Type": "application/json"}
    payload = orjson.dumps({"text": message})
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, headers=headers, data=payload) as response:
            if response.status != 200:
                raise ValueError(
                    f"Request to Slack returned an error {response.status}, the response is:\n{response.text}"
                )


def parse_case2slack(case_report: CaseReport):
    message = f"""
    【{case_report.Platform}】
    測試案例: {case_report.CaseName}／報告連結: {case_report.Link}
    Failed: {case_report.Fail} ／Broken: {case_report.Broken} ／Skip: {case_report.Skip} ／Pass: {case_report.Pass} ／Total: {case_report.Total}
    開始時間: {case_report.StartTime}／執行時間: {case_report.RunTime}／結束時間: {case_report.EndTime}
    """
    print(message)
    return message


def main():
    # 取得當前日期
    start_time = datetime.now()
    end_time = datetime.now()
    run_time = end_time - start_time

    case_report = CaseReport(
        Platform="Production",
        CaseName="API_TEST_public/get_ohlc_data",
        Fail=2,
        Broken=1,
        Skip=1,
        Pass=6,
        Known=0,
        Link="http://localhost:8000/allure-report/index.html",
        StartTime=start_time,
        RunTime=run_time,
        EndTime=end_time,
    )

    # 替換為你的 Slack Webhook URL
    webhook_url = "https://hooks.slack.com/services/你的/Slack/Webhook/URL"

    # 發送訊息
    send_slack_message(webhook_url, case_report)

    # 【Production】
    # 測試案例: API_TEST_public/get_ohlc_data／報告連結: http://localhost:8000/allure-report/index.html
    # Failed: 2 ／Broken: 1 ／Skip: 1 ／Pass: 6 ／Total: 9
    # 開始時間: 2025-03-11 22:46:35.188384／執行時間: 0:00:00.000004／結束時間: 2025-03-11 22:46:35.188388


if __name__ == "__main__":
    main()
