import asyncio
from datetime import datetime
from pathlib import Path

import orjson
import pandas as pd
from playwright.async_api import async_playwright

from bito_front.bitopro_report_generator import BitoProReportGenerator


class BitoProDataComparer:
    """
    比較BitoPro網頁和API數據的類別
    """

    def __init__(self):
        self.web_tables = []
        self.web_vip_fee_table = None
        self.trading_fee_df = None
        self.order_limits_df = None
        self.withdrawal_fees_df = None

        # 統計數據
        self.total_checks = 0
        self.passed_checks = 0
        self.failed_checks = 0
        self.web_table_count = 2  # 下單限制表和VIP費用等級表各算一張

        # 比較結果
        self.comparison_results = {}
        self.report_path = None

    async def fetch_data(self):
        """
        使用Playwright獲取網頁和API數據
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            print("正在獲取網頁數據...")
            await page.goto("https://www.bitopro.com/ns/fees")

            # 獲取網頁表格數據
            table_data = await page.evaluate("""() => {
                const tables = Array.from(document.querySelectorAll('table'));
                const tableData = tables.map((table, index) => {
                    const headers = Array.from(table.querySelectorAll('thead tr th')).map(th => th.textContent.trim());
                    const rows = Array.from(table.querySelectorAll('tbody tr')).map(tr => {
                        return Array.from(tr.querySelectorAll('td')).map(td => td.textContent.trim());
                    });
                    return { index, headers, rows };
                });
                return tableData;
            }""")

            # 嘗試獲取 VIP 費用等級表
            vip_fee_table = await page.evaluate("""() => {
                // 尋找 VIP 費用等級列表 標題
                const vipTitle = Array.from(document.querySelectorAll('h4')).find(h => h.textContent.includes('VIP 費用等級列表'));
                if (!vipTitle) return null;
                
                // 找到標題後的 DIV 容器
                const container = vipTitle.nextElementSibling;
                if (!container || container.tagName !== 'DIV') return null;
                
                // 獲取表格式結構的行
                const rows = container.querySelectorAll('.sc-c62c0220-2, .sc-c62c0220-3');
                if (!rows || rows.length === 0) return null;
                
                // 獲取表頭
                const headerRow = rows[0];
                const headers = Array.from(headerRow.querySelectorAll('.sc-c62c0220-1')).map(cell => cell.textContent.trim());
                
                // 獲取數據行
                const dataRows = [];
                for (let i = 1; i < rows.length; i++) {
                    const row = rows[i];
                    const cells = Array.from(row.querySelectorAll('.sc-c62c0220-1')).map(cell => cell.textContent.trim());
                    if (cells.length > 0) {
                        dataRows.push(cells);
                    }
                }
                
                return { headers, rows: dataRows };
            }""")

            # 獲取 API 數據
            print("正在獲取 API 數據...")
            response = await page.goto(
                "https://www.bitopro.com/ns-api/v3/provisioning/limitations-and-fees?locale=zh-TW"
            )
            api_data = orjson.loads(await response.text())

            await browser.close()

            # 處理網頁表格數據
            print("處理網頁表格數據...")
            for table in table_data:
                df = pd.DataFrame(table["rows"], columns=table["headers"])
                self.web_tables.append(df)
                print(f"網頁表格 {table['index']} 標題: {table['headers']}")
                print(df.head())
                print("\n")

            # 處理 VIP 費用等級表
            if vip_fee_table and vip_fee_table["headers"] and vip_fee_table["rows"]:
                self.web_vip_fee_table = pd.DataFrame(vip_fee_table["rows"], columns=vip_fee_table["headers"])
                print("網頁 VIP 費用等級表:")
                print(self.web_vip_fee_table.head())
                print(f"總行數: {len(self.web_vip_fee_table)}")
                print("\n")

            # 處理 API 數據
            print("處理 API 數據...")

            # 交易費率表
            self.trading_fee_df = pd.DataFrame(api_data["tradingFeeRate"])
            print("API 交易費率表:")
            print(self.trading_fee_df.head())
            print(f"總行數: {len(self.trading_fee_df)}")
            print("\n")

            # 訂單限制表
            self.order_limits_df = pd.DataFrame(api_data["orderFeesAndLimitations"])
            print("API 訂單限制表 (前5行):")
            print(self.order_limits_df.head())
            print(f"總行數: {len(self.order_limits_df)}")
            print("\n")

            # 提款費用表
            self.withdrawal_fees_df = pd.DataFrame(api_data["restrictionsOfWithdrawalFees"])
            print("API 提款費用表 (前5行):")
            print(self.withdrawal_fees_df.head())
            print(f"總行數: {len(self.withdrawal_fees_df)}")
            print("\n")

    def compare_order_limits(self):
        """
        比較下單限制表
        """
        print("=" * 80)
        print("比較網頁表格和 API 數據...")
        print("=" * 80)

        order_limits_result = {}

        # 假設第一個表格是下單限制表
        if (
            len(self.web_tables) > 0
            and "交易對" in self.web_tables[0].columns
            and "最小下單數量" in self.web_tables[0].columns
        ):
            web_order_limits = self.web_tables[0].copy()  # 使用 copy() 避免 SettingWithCopyWarning

            # 從 API 數據中提取相應的信息
            api_order_limits_data = []
            for _, row in self.order_limits_df.iterrows():
                api_order_limits_data.append(
                    {
                        "交易對": row["pair"],
                        "最小下單數量": f"{row['minimumOrderAmount']} {row['minimumOrderAmountBase']}",
                        "最小下單位數": row["minimumOrderNumberOfDigits"],
                    }
                )

            api_order_limits = pd.DataFrame(api_order_limits_data)

            print("網頁下單限制表 (前5行):")
            print(web_order_limits.head())
            print(f"總行數: {len(web_order_limits)}")

            print("\nAPI 下單限制表 (前5行):")
            print(api_order_limits.head())
            print(f"總行數: {len(api_order_limits)}")

            # 保存表格數據
            order_limits_result["web_table"] = web_order_limits
            order_limits_result["api_table"] = api_order_limits

            # 比較兩個表格
            print("\n比較結果:")

            # 檢查行數是否一致
            rows_match = len(web_order_limits) == len(api_order_limits)
            order_limits_result["rows_match"] = rows_match
            print(
                f"網頁表格和 API 數據的行數{'一致' if rows_match else '不一致'} (網頁: {len(web_order_limits)}, API: {len(api_order_limits)})"
            )

            # 更新統計數據 - 行數一致性檢查
            self.total_checks += 1
            if rows_match:
                self.passed_checks += 1
            else:
                self.failed_checks += 1

            # 合併表格進行比較
            merged_df = pd.merge(web_order_limits, api_order_limits, on="交易對", suffixes=("_網頁", "_API"))
            order_limits_result["merged_df"] = merged_df

            # 檢查最小下單數量是否一致
            merged_df["最小下單數量一致"] = merged_df.apply(
                lambda row: BitoProReportGenerator.clean_amount(row["最小下單數量_網頁"])
                == BitoProReportGenerator.clean_amount(row["最小下單數量_API"]),
                axis=1,
            )

            # 檢查最小下單位數是否一致
            merged_df["最小下單位數一致"] = merged_df["最小下單位數_網頁"] == merged_df["最小下單位數_API"].astype(str)

            # 顯示不一致的行
            inconsistent_rows = merged_df[~(merged_df["最小下單數量一致"] & merged_df["最小下單位數一致"])]
            order_limits_result["inconsistent_rows"] = inconsistent_rows

            print(f"合併後的表格行數: {len(merged_df)}")
            print(f"網頁表格中的交易對數量: {len(web_order_limits)}")
            print(f"API 數據中的交易對數量: {len(api_order_limits)}")

            # 更新統計數據 - 每個True/False算一筆case
            # 檢查最小下單數量是否一致
            min_order_amount_checks = len(merged_df)
            min_order_amount_passed = merged_df["最小下單數量一致"].sum()
            self.total_checks += min_order_amount_checks
            self.passed_checks += min_order_amount_passed
            self.failed_checks += min_order_amount_checks - min_order_amount_passed

            # 檢查最小下單位數是否一致
            min_order_digits_checks = len(merged_df)
            min_order_digits_passed = merged_df["最小下單位數一致"].sum()
            self.total_checks += min_order_digits_checks
            self.passed_checks += min_order_digits_passed
            self.failed_checks += min_order_digits_checks - min_order_digits_passed

            # 檢查哪些交易對只存在於網頁表格中
            web_only_pairs = set(web_order_limits["交易對"]) - set(api_order_limits["交易對"])
            if web_only_pairs:
                print(f"\n只存在於網頁表格中的交易對: {web_only_pairs}")
                order_limits_result["web_only_pairs"] = web_only_pairs

            # 檢查哪些交易對只存在於 API 數據中
            api_only_pairs = set(api_order_limits["交易對"]) - set(web_order_limits["交易對"])
            if api_only_pairs:
                print(f"\n只存在於 API 數據中的交易對: {api_only_pairs}")
                order_limits_result["api_only_pairs"] = api_only_pairs

            if len(inconsistent_rows) > 0:
                print("\n發現不一致的數據:")
                print(
                    inconsistent_rows[
                        [
                            "交易對",
                            "最小下單數量_網頁",
                            "最小下單數量_API",
                            "最小下單數量一致",
                            "最小下單位數_網頁",
                            "最小下單位數_API",
                            "最小下單位數一致",
                        ]
                    ]
                )
            else:
                print("\n網頁表格和 API 數據中共同存在的交易對數據完全一致!")

            # 保存比較結果
            self.comparison_results["order_limits"] = order_limits_result
        else:
            print("未找到可比較的下單限制表數據")
            self.total_checks += 1
            self.failed_checks += 1

    def compare_vip_fee(self):
        """
        比較VIP費用等級表
        """
        print("\n2. VIP 費用等級表比較")
        print("-" * 50)

        vip_fee_result = {}

        if self.web_vip_fee_table is not None and not self.web_vip_fee_table.empty:
            print("網頁 VIP 費用等級表 (前5行):")
            print(self.web_vip_fee_table.head())
            print(f"總行數: {len(self.web_vip_fee_table)}")

            print("\nAPI 交易費率表 (前5行):")
            print(self.trading_fee_df.head())
            print(f"總行數: {len(self.trading_fee_df)}")

            # 保存表格數據
            vip_fee_result["web_table"] = self.web_vip_fee_table
            vip_fee_result["api_table"] = self.trading_fee_df

            # 嘗試比較兩個表格
            print("\n比較結果:")

            # 檢查行數是否一致
            rows_match = len(self.web_vip_fee_table) == len(self.trading_fee_df)
            vip_fee_result["rows_match"] = rows_match
            print(
                f"網頁表格和 API 數據的行數{'一致' if rows_match else '不一致'} (網頁: {len(self.web_vip_fee_table)}, API: {len(self.trading_fee_df)})"
            )

            # 更新統計數據 - 行數一致性檢查
            self.total_checks += 1
            if rows_match:
                self.passed_checks += 1
            else:
                self.failed_checks += 1

            try:
                # 創建比較數據
                comparison_data = []

                # 假設兩個表格的行數相同，且按照相同的順序排列
                for i in range(min(len(self.web_vip_fee_table), len(self.trading_fee_df))):
                    web_row = self.web_vip_fee_table.iloc[i]
                    api_row = self.trading_fee_df.iloc[i]

                    # 提取 VIP 等級
                    web_level = web_row["等級"] if "等級" in self.web_vip_fee_table.columns else f"VIP {i}"
                    api_level = f"VIP {api_row['rank']}" if "rank" in self.trading_fee_df.columns else f"VIP {i}"

                    # 提取交易量
                    web_volume = web_row["前 30 天交易量"] if "前 30 天交易量" in self.web_vip_fee_table.columns else ""
                    api_volume = (
                        f"{api_row['twdVolumeSymbol']} {api_row['twdVolume']}"
                        if "twdVolumeSymbol" in self.trading_fee_df.columns
                        and "twdVolume" in self.trading_fee_df.columns
                        else ""
                    )

                    # 提取手續費率
                    web_maker_fee = (
                        web_row["Maker / Taker"] if "Maker / Taker" in self.web_vip_fee_table.columns else ""
                    )
                    web_fee = web_maker_fee

                    api_maker_fee = api_row["makerFee"] if "makerFee" in self.trading_fee_df.columns else ""
                    api_taker_fee = api_row["takerFee"] if "takerFee" in self.trading_fee_df.columns else ""
                    api_fee = f"{api_maker_fee} / {api_taker_fee}" if api_maker_fee and api_taker_fee else ""

                    # 清理手續費率以便比較
                    web_fee_normalized = BitoProReportGenerator.normalize_fee(web_fee)
                    api_fee_normalized = BitoProReportGenerator.normalize_fee(api_fee)
                    fee_match = web_fee_normalized == api_fee_normalized

                    # 使用改進的交易量比較邏輯
                    volume_match = BitoProReportGenerator.normalize_volume(
                        web_volume
                    ) == BitoProReportGenerator.normalize_volume(api_volume)

                    comparison_data.append(
                        {
                            "VIP等級_網頁": web_level,
                            "VIP等級_API": api_level,
                            "等級一致": web_level == api_level,
                            "交易量_網頁": web_volume,
                            "交易量_API": api_volume,
                            "交易量一致": volume_match,
                            "手續費_網頁": web_fee,
                            "手續費_API": api_fee,
                            "手續費一致": fee_match,
                            "手續費_網頁(標準化)": web_fee_normalized,
                            "手續費_API(標準化)": api_fee_normalized,
                        }
                    )

                comparison_df = pd.DataFrame(comparison_data)
                vip_fee_result["comparison_df"] = comparison_df

                inconsistent_vip = comparison_df[
                    ~(comparison_df["等級一致"] & comparison_df["交易量一致"] & comparison_df["手續費一致"])
                ]
                vip_fee_result["inconsistent_vip"] = inconsistent_vip

                # 更新統計數據 - 每個True/False算一筆case
                # VIP等級一致性檢查
                level_checks = len(comparison_df)
                level_passed = comparison_df["等級一致"].sum()
                self.total_checks += level_checks
                self.passed_checks += level_passed
                self.failed_checks += level_checks - level_passed

                # 交易量一致性檢查
                volume_checks = len(comparison_df)
                volume_passed = comparison_df["交易量一致"].sum()
                self.total_checks += volume_checks
                self.passed_checks += volume_passed
                self.failed_checks += volume_checks - volume_passed

                # 手續費一致性檢查
                fee_checks = len(comparison_df)
                fee_passed = comparison_df["手續費一致"].sum()
                self.total_checks += fee_checks
                self.passed_checks += fee_passed
                self.failed_checks += fee_checks - fee_passed

                if len(inconsistent_vip) > 0:
                    print(f"\n發現 {len(inconsistent_vip)} 個不一致項:")
                    print(inconsistent_vip)
                else:
                    print("\n所有 VIP 等級數據一致!")

            except Exception as e:
                print(f"\n比較過程中發生錯誤: {str(e)}")
                print("\n由於表格結構可能不同，無法進行詳細比較。請手動檢查表格內容。")
                vip_fee_result["error"] = str(e)
                self.total_checks += 1
                self.failed_checks += 1

            # 保存比較結果
            self.comparison_results["vip_fee"] = vip_fee_result
        else:
            print("未找到可比較的 VIP 費用等級表數據")
            self.total_checks += 1
            self.failed_checks += 1

    def generate_report(self):
        """
        生成比較報告
        """
        print("\n3. 數據一致性總結")
        print("-" * 50)
        print(f"總檢查項目: {self.total_checks}")
        print(f"通過項目: {self.passed_checks} ({self.passed_checks / self.total_checks * 100:.1f}%)")
        print(f"失敗項目: {self.failed_checks} ({self.failed_checks / self.total_checks * 100:.1f}%)")
        print(f"網頁表格數量: {self.web_table_count}")

        # 準備統計數據
        statistics = {
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "web_table_count": self.web_table_count,
        }

        # 生成HTML報告
        html_report = BitoProReportGenerator.generate_html_report(self.comparison_results, statistics)

        # 保存 HTML 報告
        report_path = f"bito_front/report/{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_report)
        self.report_path = report_path
        print(f"\nHTML 報告已保存至: {report_path}")

    async def run(self):
        """
        執行完整比較流程
        """
        await self.fetch_data()
        self.compare_order_limits()
        self.compare_vip_fee()
        self.generate_report()
        return self.comparison_results


async def main():
    comparer = BitoProDataComparer()
    await comparer.run()


if __name__ == "__main__":
    start_time = datetime.now()
    asyncio.run(main())
    end_time = datetime.now()
    print(f"\n執行總時間: {(end_time - start_time).total_seconds():.2f} 秒")
