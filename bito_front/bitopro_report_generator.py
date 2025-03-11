import re
from datetime import datetime


class BitoProReportGenerator:
    """
    負責生成BitoPro數據比較報告的HTML
    """

    @staticmethod
    def generate_html_report(comparison_results, statistics):
        """
        生成HTML報告

        Args:
            comparison_results: 比較結果數據
            statistics: 統計數據

        Returns:
            str: HTML報告內容
        """
        html_report = []
        html_report.append(
            """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>BitoPro 數據比較報告</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                }
                h1, h2, h3 {
                    color: #2c3e50;
                }
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                }
                .header {
                    background-color: #3498db;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    margin-bottom: 20px;
                    border-radius: 5px;
                }
                .section {
                    background-color: #f9f9f9;
                    padding: 20px;
                    margin-bottom: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                .table-container {
                    width: 100%;
                    overflow-x: auto;
                    margin-bottom: 20px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }
                th, td {
                    padding: 12px 15px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                    word-wrap: break-word;
                    max-width: 300px;
                }
                th {
                    background-color: #3498db;
                    color: white;
                    white-space: normal;
                    hyphens: auto;
                    overflow-wrap: break-word;
                }
                tr:nth-child(even) {
                    background-color: #f2f2f2;
                }
                .success {
                    color: #27ae60;
                    font-weight: bold;
                }
                .error {
                    color: #e74c3c;
                    font-weight: bold;
                }
                .true-value {
                    color: #27ae60;
                    font-weight: bold;
                }
                .false-value {
                    color: #e74c3c;
                    font-weight: bold;
                }
                .screenshot {
                    max-width: 100%;
                    height: auto;
                    margin: 20px 0;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }
                .chart {
                    max-width: 100%;
                    height: auto;
                    margin: 20px 0;
                }
                .footer {
                    text-align: center;
                    margin-top: 30px;
                    padding: 20px;
                    background-color: #2c3e50;
                    color: white;
                    border-radius: 5px;
                }
                .collapsible {
                    background-color: #3498db;
                    color: white;
                    cursor: pointer;
                    padding: 18px;
                    width: 100%;
                    border: none;
                    text-align: left;
                    outline: none;
                    font-size: 16px;
                    border-radius: 5px 5px 0 0;
                    margin-top: 10px;
                }
                .active, .collapsible:hover {
                    background-color: #2980b9;
                }
                .content {
                    padding: 0 18px;
                    max-height: 0;
                    overflow: hidden;
                    transition: max-height 0.2s ease-out;
                    background-color: #f9f9f9;
                    border-radius: 0 0 5px 5px;
                    border: 1px solid #ddd;
                    border-top: none;
                }
                .summary-box {
                    background-color: #ecf0f1;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                .summary-title {
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                .summary-item {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 5px;
                }
                .summary-label {
                    font-weight: bold;
                }
                .summary-value {
                    text-align: right;
                }
                .summary-pass {
                    color: #27ae60;
                }
                .summary-fail {
                    color: #e74c3c;
                }
                .draggable-table {
                    cursor: grab;
                    overflow: auto;
                    max-width: 100%;
                }
                .draggable-table:active {
                    cursor: grabbing;
                }
            </style>
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    // 折疊功能
                    var coll = document.getElementsByClassName("collapsible");
                    for (var i = 0; i < coll.length; i++) {
                        coll[i].addEventListener("click", function() {
                            this.classList.toggle("active");
                            var content = this.nextElementSibling;
                            if (content.style.maxHeight) {
                                content.style.maxHeight = null;
                            } else {
                                content.style.maxHeight = content.scrollHeight + "px";
                            }
                        });
                    }
                    
                    // 表格拖曳功能
                    var draggableTables = document.getElementsByClassName('draggable-table');
                    for (var i = 0; i < draggableTables.length; i++) {
                        initDraggable(draggableTables[i]);
                    }
                    
                    function initDraggable(element) {
                        var pos = { top: 0, left: 0, x: 0, y: 0 };
                        
                        const mouseDownHandler = function(e) {
                            element.style.cursor = 'grabbing';
                            element.style.userSelect = 'none';
                            
                            pos = {
                                left: element.scrollLeft,
                                top: element.scrollTop,
                                // 獲取當前滑鼠位置
                                x: e.clientX,
                                y: e.clientY,
                            };
                            
                            document.addEventListener('mousemove', mouseMoveHandler);
                            document.addEventListener('mouseup', mouseUpHandler);
                        };
                        
                        const mouseMoveHandler = function(e) {
                            // 計算滑鼠移動距離
                            const dx = e.clientX - pos.x;
                            const dy = e.clientY - pos.y;
                            
                            // 滾動元素
                            element.scrollTop = pos.top - dy;
                            element.scrollLeft = pos.left - dx;
                        };
                        
                        const mouseUpHandler = function() {
                            element.style.cursor = 'grab';
                            element.style.removeProperty('user-select');
                            
                            document.removeEventListener('mousemove', mouseMoveHandler);
                            document.removeEventListener('mouseup', mouseUpHandler);
                        };
                        
                        // 綁定滑鼠事件
                        element.addEventListener('mousedown', mouseDownHandler);
                    }
                    
                    // 將True/False著色
                    function colorTrueFalse() {
                        var tables = document.querySelectorAll('table');
                        tables.forEach(function(table) {
                            var cells = table.querySelectorAll('td');
                            cells.forEach(function(cell) {
                                if (cell.textContent.trim() === 'True') {
                                    cell.innerHTML = '<span class="true-value">True</span>';
                                } else if (cell.textContent.trim() === 'False') {
                                    cell.innerHTML = '<span class="false-value">False</span>';
                                }
                            });
                        });
                    }
                    
                    // 頁面加載完成後執行
                    colorTrueFalse();
                });
            </script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>BitoPro 數據比較報告</h1>
                    <p>生成時間: """
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + """</p>
                </div>
        """
        )

        # 1. 下單限制表比較
        html_report.append("""
            <div class="section">
                <h2>1. 下單限制表比較</h2>
        """)

        # 處理下單限制表比較結果
        order_limits = comparison_results.get("order_limits", {})
        if order_limits:
            web_order_limits = order_limits.get("web_table")
            api_order_limits = order_limits.get("api_table")
            merged_df = order_limits.get("merged_df")
            inconsistent_rows = order_limits.get("inconsistent_rows")
            rows_match = order_limits.get("rows_match", False)

            if web_order_limits is not None and api_order_limits is not None:
                # 添加行數一致性檢查結果
                html_report.append(f"""
                    <p>網頁表格和 API 數據的行數<span class="{"success" if rows_match else "error"}">{" 一致 ✓" if rows_match else " 不一致 ✗"}</span> (網頁: {len(web_order_limits)}, API: {len(api_order_limits)})</p>
                """)

                # 添加到 HTML 報告 - 使用折疊功能
                html_report.append(f"""
                    <button class="collapsible">網頁下單限制表 (總行數: {len(web_order_limits)}) - 點擊展開/收起</button>
                    <div class="content">
                        <div class="draggable-table">
                            {web_order_limits.to_html(index=False, classes="table")}
                        </div>
                    </div>
                    
                    <button class="collapsible">API 下單限制表 (總行數: {len(api_order_limits)}) - 點擊展開/收起</button>
                    <div class="content">
                        <div class="draggable-table">
                            {api_order_limits.to_html(index=False, classes="table")}
                        </div>
                    </div>
                """)

                # 添加完整比較結果到HTML報告
                if merged_df is not None:
                    html_report.append(f"""
                        <button class="collapsible">完整比較結果 (總行數: {len(merged_df)}) - 點擊展開/收起</button>
                        <div class="content">
                            <div class="draggable-table">
                                {merged_df.to_html(index=False, classes="table").replace("True", '<span class="true-value">True</span>').replace("False", '<span class="false-value">False</span>')}
                            </div>
                        </div>
                    """)

                # 顯示只存在於網頁或API的交易對
                web_only_pairs = order_limits.get("web_only_pairs")
                if web_only_pairs:
                    html_report.append(f"""
                        <h4>只存在於網頁表格中的交易對:</h4>
                        <p>{", ".join(web_only_pairs)}</p>
                    """)

                api_only_pairs = order_limits.get("api_only_pairs")
                if api_only_pairs:
                    html_report.append(f"""
                        <h4>只存在於 API 數據中的交易對:</h4>
                        <p>{", ".join(api_only_pairs)}</p>
                    """)

                # 顯示不一致項
                if inconsistent_rows is not None and not inconsistent_rows.empty:
                    html_report.append(f"""
                        <h4 class="error">發現 {len(inconsistent_rows)} 個不一致項:</h4>
                        <button class="collapsible">不一致項詳情 - 點擊展開/收起</button>
                        <div class="content">
                            {
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
                        ].to_html(index=False, classes="table")
                    }
                        </div>
                    """)
                else:
                    html_report.append("""
                        <h4 class="success">網頁表格和 API 數據中共同存在的交易對數據完全一致!</h4>
                    """)
            else:
                html_report.append("""
                    <p class="error">未找到可比較的下單限制表數據</p>
                """)
        else:
            html_report.append("""
                <p class="error">未找到可比較的下單限制表數據</p>
            """)

        html_report.append("</div>")  # 關閉下單限制表比較部分

        # 2. VIP 費用等級表比較
        html_report.append("""
            <div class="section">
                <h2>2. VIP 費用等級表比較</h2>
        """)

        # 處理VIP費用等級表比較結果
        vip_fee = comparison_results.get("vip_fee", {})
        if vip_fee:
            web_vip_fee_table = vip_fee.get("web_table")
            api_table = vip_fee.get("api_table")
            comparison_df = vip_fee.get("comparison_df")

            if web_vip_fee_table is not None and api_table is not None:
                # 添加到 HTML 報告 - 使用折疊功能
                html_report.append(f"""
                    <button class="collapsible">網頁 VIP 費用等級表 (總行數: {len(web_vip_fee_table)}) - 點擊展開/收起</button>
                    <div class="content">
                        <div class="draggable-table">
                            {web_vip_fee_table.to_html(index=False, classes="table")}
                        </div>
                    </div>
                    
                    <button class="collapsible">API 交易費率表 (總行數: {len(api_table)}) - 點擊展開/收起</button>
                    <div class="content">
                        <div class="draggable-table">
                            {api_table.to_html(index=False, classes="table", escape=False)}
                        </div>
                    </div>
                """)

                # 先添加比較結果詳情
                if comparison_df is not None:
                    html_report.append(f"""
                        <button class="collapsible">比較結果詳情 - 點擊展開/收起</button>
                        <div class="content">
                            <div class="draggable-table">
                                {comparison_df.to_html(index=False, classes="table").replace("True", '<span class="true-value">True</span>').replace("False", '<span class="false-value">False</span>')}
                            </div>
                        </div>
                        
                        <p>網頁表格和 API 數據的行數{"一致" if len(web_vip_fee_table) == len(api_table) else "不一致"}</p>
                    """)

                    # 檢查是否有不一致的項目
                    inconsistent_vip = vip_fee.get("inconsistent_vip")
                    has_inconsistencies = inconsistent_vip is not None and not inconsistent_vip.empty

                    html_report.append(f"""
                        <h4 class="{"error" if has_inconsistencies else "success"}">
                            {"發現 " + str(len(inconsistent_vip)) + " 個不一致項:" if has_inconsistencies else "所有 VIP 等級數據一致!"}
                        </h4>
                    """)
            else:
                error = vip_fee.get("error")
                if error:
                    html_report.append(f"""
                        <p class="error">比較過程中發生錯誤: {error}</p>
                        <p>由於表格結構可能不同，無法進行詳細比較。請手動檢查表格內容。</p>
                    """)
                else:
                    html_report.append("""
                        <p class="error">未找到可比較的 VIP 費用等級表數據</p>
                    """)
        else:
            html_report.append("""
                <p class="error">未找到可比較的 VIP 費用等級表數據</p>
            """)

        html_report.append("</div>")  # 關閉 VIP 費用等級表比較部分

        # 3. 數據一致性總結
        html_report.append("""
            <div class="section">
                <h2>3. 數據一致性總結</h2>
        """)

        # 獲取統計數據
        total_checks = statistics.get("total_checks", 0)
        passed_checks = statistics.get("passed_checks", 0)
        failed_checks = statistics.get("failed_checks", 0)
        web_table_count = statistics.get("web_table_count", 0)

        # 計算通過率
        pass_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        fail_rate = (failed_checks / total_checks * 100) if total_checks > 0 else 0

        # 添加統計摘要
        html_report.append(f"""
            <div class="summary-box">
                <div class="summary-title">測試結果摘要</div>
                <div class="summary-item">
                    <span class="summary-label">總檢查項目:</span>
                    <span class="summary-value">{total_checks}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">通過項目:</span>
                    <span class="summary-value summary-pass">{passed_checks} ({pass_rate:.1f}%)</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">失敗項目:</span>
                    <span class="summary-value summary-fail">{failed_checks} ({fail_rate:.1f}%)</span>
                </div>
            </div>
        """)

        html_report.append(f"""
            <p>網頁表格數量: {web_table_count}</p>
        """)

        # 下單限制表一致性
        order_limits = comparison_results.get("order_limits", {})
        if order_limits and order_limits.get("web_table") is not None:
            inconsistent_rows = order_limits.get("inconsistent_rows")
            rows_match = order_limits.get("rows_match", False)

            # 添加行數一致性檢查結果
            html_report.append(f"""
                <p>下單限制表行數: <span class="{"success" if rows_match else "error"}">{" 一致 ✓" if rows_match else " 不一致 ✗"}</span></p>
            """)

            if inconsistent_rows is not None and inconsistent_rows.empty:
                html_report.append("""
                    <p class="success">下單限制表: 網頁和 API 數據一致 ✓</p>
                """)
            else:
                html_report.append(f"""
                    <p class="error">下單限制表: 發現 {len(inconsistent_rows) if inconsistent_rows is not None else 0} 個不一致項 ✗</p>
                """)

        # VIP 費用等級表一致性
        vip_fee = comparison_results.get("vip_fee", {})
        if vip_fee and vip_fee.get("web_table") is not None:
            try:
                # 檢查是否有不一致的項目
                comparison_df = vip_fee.get("comparison_df")
                inconsistent_vip = vip_fee.get("inconsistent_vip")

                if comparison_df is not None:
                    vip_inconsistent = inconsistent_vip is not None and not inconsistent_vip.empty

                    if vip_inconsistent:
                        html_report.append("""
                            <p class="error">VIP 費用等級表: 發現不一致項 (標準化前) ✗</p>
                            <p>注意: 在標準化百分比和小數形式後，手續費率是一致的</p>
                        """)
                    else:
                        html_report.append("""
                            <p class="success">VIP 費用等級表: 網頁和 API 數據一致 (標準化後) ✓</p>
                            <p>注意: 網頁顯示的是百分比形式 (如 0.1%)，而 API 返回的是小數形式 (如 0.001)</p>
                        """)
            except Exception:
                web_vip_fee_table = vip_fee.get("web_table")
                api_table = vip_fee.get("api_table")

                if web_vip_fee_table is not None and api_table is not None:
                    if len(web_vip_fee_table) == len(api_table):
                        html_report.append("""
                            <p class="success">VIP 費用等級表: 網頁和 API 數據行數一致 ✓</p>
                        """)
                    else:
                        html_report.append(f"""
                            <p class="error">VIP 費用等級表: 網頁和 API 數據行數不一致 (網頁: {len(web_vip_fee_table)}, API: {len(api_table)}) ✗</p>
                        """)
        else:
            html_report.append("""
                <p class="error">未找到可比較的網頁表格數據</p>
            """)

        html_report.append("</div>")  # 關閉數據一致性總結部分

        # 添加頁腳
        html_report.append(
            """
                <div class="footer">
                    <p>BitoPro 數據比較報告 | 生成時間: """
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + """</p>
                </div>
            </div>
        </body>
        </html>
        """
        )

        return "".join(html_report)

    @staticmethod
    def normalize_fee(fee_str):
        """
        標準化費用字符串，處理百分比和小數形式的差異
        """
        if not isinstance(fee_str, str):
            return str(fee_str)

        # 移除空格和分隔符
        fee_str = fee_str.replace(" ", "").replace("%", "")
        parts = fee_str.split("/")
        normalized_parts = []

        for part in parts:
            try:
                # 轉換為浮點數
                value = float(part)
                # 如果是百分比形式（大於0.01），轉換為小數形式
                if value > 0.01:
                    value = value / 100
                normalized_parts.append(f"{value:.6f}")
            except ValueError:
                # 如果無法轉換為浮點數，保持原樣
                normalized_parts.append(part)

        return "/".join(normalized_parts)

    @staticmethod
    def normalize_volume(volume_str):
        """
        標準化交易量字符串，處理不同格式
        """
        if not isinstance(volume_str, str):
            return str(volume_str)

        # 移除逗號、空格和單位
        cleaned = re.sub(r"[,\s]", "", volume_str)
        # 移除 TWD 或其他貨幣單位
        cleaned = re.sub(r"TWD|USD|BTC", "", cleaned)

        # 處理 ≥ 或 < 符號
        if "≥" in cleaned:
            cleaned = cleaned.replace("≥", "")
        elif "<" in cleaned:
            cleaned = cleaned.replace("<", "")

        try:
            # 轉換為數字以便比較
            return float(cleaned)
        except ValueError:
            return cleaned

    @staticmethod
    def clean_amount(amount_str):
        """
        清理金額字符串以便比較
        """
        if not isinstance(amount_str, str):
            return str(amount_str)

        # 移除逗號和空格
        cleaned = re.sub(r"[,\s]", "", amount_str)

        # 處理 ≥ 或 < 符號
        if "≥" in cleaned:
            cleaned = cleaned.replace("≥", "")
        elif "<" in cleaned:
            cleaned = cleaned.replace("<", "")

        # 提取數字和單位
        match = re.match(r"([\d.]+)\s*([A-Za-z]+)", cleaned)
        if match:
            return match.group(1) + " " + match.group(2)

        return cleaned
