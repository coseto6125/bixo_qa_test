# BitoPro 測試自動化框架

這是一個用於測試 BitoPro 交易所的自動化測試框架，包含 API 測試和前端數據比較功能。

## 功能特點

- **API 測試**：使用 aiohttp、pytest 和 allure 測試 BitoPro 的 API
- **前端數據比較**：使用 Playwright 自動化瀏覽器獲取網頁數據並與 API 數據比較
- **自動報告生成**：生成詳細的 HTML 和 Allure 報告
- **Slack 通知**：自動發送測試結果到 Slack 頻道
- **Google Sheets 整合**：將測試結果自動更新到 Google Sheets

## 專案結構

.
├── bito_api_test/ # API 測試模組
│ ├── api/ # API 客戶端類
│ ├── tests/ # 測試用例
│ ├── allure-results/ # Allure 測試結果
│ ├── allure-report/ # 生成的 Allure 報告
│ └── conftest.py # Pytest 配置文件
├── bito_front/ # 前端測試模組
│ ├── report/ # 生成的報告
│ ├── compare_bitopro_data.py # 數據比較邏輯
│ └── bitopro_report_generator.py # 報告生成器
├── alert_module.py # Slack 通知模組
├── update_module.py # Google Sheets 更新模組
├── test_main.py # 主測試執行腳本
└── requirements.txt # 依賴項列表

## 安裝

1. 安裝所需的依賴項：

```bash
pip install -r requirements.txt
```

2. 安裝 Allure 命令行工具：

對於 Windows 用戶，可以使用 Scoop 安裝：

```bash
scoop install allure
```

或者使用 Chocolatey：

```bash
choco install allure-commandline
```

3. 安裝 Playwright 瀏覽器：

```bash
playwright install chromium
```

## 配置

1. **Slack 通知**：

   - 在 Slack 中創建一個 Webhook URL
   - 在 `alert_module.py` 中更新 `webhook_url` 變數
2. **Google Sheets 整合**：

   - 準備 Google 服務帳號憑證 JSON 文件
   - 將文件命名為 `service_account_credentials.json` 並放在專案根目錄

## 使用方法

### 執行 API 測試

```bash
python test_main.py
```

或直接使用 pytest：

```bash
cd bito_api_test
pytest tests/ --alluredir=./allure-results
allure serve ./allure-results
```

### 執行前端數據比較測試

```bash
python -c "import asyncio; from test_main import run_front_tests; asyncio.run(run_front_tests())"
```

### 查看測試報告

- API 測試報告：`bito_api_test/allure-report/index.html`
- 前端比較報告：`bito/report/{date}_{hhmmss}.html`

## 自動化通知

測試完成後，系統會：

1. 自動發送測試結果到配置的 Slack 頻道
2. 自動更新測試結果到 Google Sheets
3. 生成詳細的測試報告

## 注意事項

- 確保網絡連接以訪問 BitoPro 網站和 API
- 如果網站結構發生變化，可能需要更新腳本中的選擇器
