from dataclasses import dataclass
from datetime import timedelta

import pandas as pd
import pygsheets
from attrs import field
from loguru import logger


@dataclass
class CaseReport:
    Platform: str
    CaseName: str
    Fail: int = 0
    Broken: int = 0  # 假設 Broken 是 Fail 的一部分
    Skip: int = 0
    Pass: int = 0
    Known: int = 0
    Link: str = ""
    StartTime: str = ""
    RunTime: timedelta = timedelta()
    EndTime: str = ""

    # 計算得出的屬性（不需要手動輸入）
    Total: int = field(init=False)
    FailPercent: float = field(init=False)
    BrokenPercent: float = field(init=False)
    SkipPercent: float = field(init=False)
    PassPercent: float = field(init=False)
    KnownPercent: float = field(init=False)

    def __post_init__(self):
        """初始化時根據 Pass、Fail、Skip、Known 自動計算 Total 和百分比"""
        self.Total = self.Pass + self.Fail + self.Skip + self.Known
        self.FailPercent = (self.Fail / self.Total * 100) if self.Total else 0
        self.BrokenPercent = (self.Broken / self.Total * 100) if self.Total else 0
        self.SkipPercent = (self.Skip / self.Total * 100) if self.Total else 0
        self.PassPercent = (self.Pass / self.Total * 100) if self.Total else 0
        self.KnownPercent = (self.Known / self.Total * 100) if self.Total else 0

    def to_dataframe(self) -> pd.DataFrame:
        """將 CaseReport 轉換成 pandas DataFrame，符合指定 headers 順序，
        並格式化百分比與 RunTime 欄位"""

        # 若 RunTime 為 datetime 物件則格式化為 HH:MM:SS，否則保持原狀
        run_time_seconds = self.RunTime.total_seconds()  # 轉換為秒數
        run_time_google_sheets = run_time_seconds / 86400  # 轉換為 Google Sheets 格式 (天)

        data = {
            "Platform": self.Platform,
            "CaseName": self.CaseName,
            "Fail": self.Fail,
            "Fail %": f"{self.FailPercent:.2f}%",
            "Broken": self.Broken,
            "Broken %": f"{self.BrokenPercent:.2f}%",
            "Skip": self.Skip,
            "Skip %": f"{self.SkipPercent:.2f}%",
            "Pass": self.Pass,
            "Pass %": f"{self.PassPercent:.2f}%",
            "Known": self.Known,
            "Known %": f"{self.KnownPercent:.2f}%",
            "Total": self.Total,
            "Link": self.Link,
            "StartTime": self.StartTime,
            "RunTime": run_time_google_sheets,
            "EndTime": self.EndTime,
        }
        return pd.DataFrame([data])


def update_google_sheet(data: pd.DataFrame, env: str, sheet_name: str = "bito_test"):
    """更新 Google 表單"""
    try:
        # 授權並打開 Google 表單
        gc = pygsheets.authorize(service_file="service_account_credentials.json")
        sh = gc.open(sheet_name)
        wks = sh.sheet1

        # 使用 set_dataframe 更新整個表單
        if isinstance(data, CaseReport):
            insert_row = 1
            data = data.to_dataframe()
        elif isinstance(data, pd.DataFrame):
            insert_row = len(data)
        else:
            raise ValueError("data 必須是 CaseReport 或 pd.DataFrame")
        wks.insert_rows(row=1, number=insert_row, inherit=False)
        wks.set_dataframe(data, start="A2", copy_head=False)  # 從A1開始插入,包含標題
        # **只格式化 P 欄（RunTime）**
        runtime_column = "P"  # `RunTime` 假設在第 16 欄（P）
        runtime_range = f"{runtime_column}2:{runtime_column}{insert_row + 1}"
        time_format = {"numberFormat": {"type": "TIME", "pattern": "h:mm:ss.000"}}

        # **套用時間格式**
        wks.apply_format(runtime_range, time_format)
        logger.info(f"Google 表單更新成功: {env}")
    except Exception as e:
        logger.error(f"更新 Google 表單時發生錯誤：{e!s}")


# 使用範例
if __name__ == "__main__":
    # 範例數據
    test_data = [
        [
            "iOS",
            "Login Test",
            1,
            0.1,
            0,
            0.0,
            0,
            0.0,
            8,
            0.8,
            1,
            0.1,
            10,
            "http://example.com/test?id=1001",
            "2025-03-10 10:00:00",
            "0:02:30",
            "2025-03-10 10:02:30",
        ],
        [
            "Android",
            "Payment Test",
            2,
            0.2,
            1,
            0.1,
            0,
            0.0,
            6,
            0.6,
            1,
            0.1,
            10,
            "http://example.com/test?id=1002",
            "2025-03-10 11:00:00",
            "0:03:00",
            "2025-03-10 11:03:00",
        ],
        [
            "Web",
            "Search Test",
            0,
            0.0,
            0,
            0.0,
            1,
            0.1,
            9,
            0.9,
            0,
            0.0,
            10,
            "http://example.com/test?id=1003",
            "2025-03-10 12:00:00",
            "0:01:45",
            "2025-03-10 12:01:45",
        ],
    ]

    # 指定的標題順序
    headers = [
        "Platform",
        "CaseName",
        "Fail",
        "Fail %",
        "Broken",
        "Broken %",
        "Skip",
        "Skip %",
        "Pass",
        "Pass %",
        "Known",
        "Known %",
        "Total",
        "Link",
        "StartTime",
        "RunTime",
        "EndTime",
    ]
    df = pd.DataFrame(test_data, columns=headers)
    # 使用自動標題
    result = update_google_sheet(update_info=df, sheet_name="bito_test", env="測試環境", data=df)
