# BitoPro API 測試框架

這是一個使用 aiohttp、pytest 和 allure 的 API 測試框架，用於測試 BitoPro 的 OHLC 數據 API。

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

## 運行測試

運行測試並生成 Allure 報告：

```bash
pytest tests/ --alluredir=./allure-results
```

查看 Allure 報告：

```bash
allure serve ./allure-results
```

## 項目結構

- `api/` - API 客戶端類
- `tests/` - 測試用例
- `conftest.py` - Pytest 配置文件
- `requirements.txt` - 依賴項列表 