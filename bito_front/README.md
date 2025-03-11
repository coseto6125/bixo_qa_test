# BitoPro 數據比較工具

這個工具用於比較 BitoPro 交易所網頁上的表格數據與其 API 提供的數據，以確保兩者之間的一致性。

## 功能特點

- 使用 Playwright 自動化瀏覽器獲取網頁數據
- 直接從 API 獲取最新數據
- 比較網頁表格和 API 數據的一致性
- 生成詳細的 HTML 報告，包含：
  - 網頁截圖
  - 表格數據比較結果
  - 數據統計分析和視覺化圖表
  - 一致性總結

## 安裝依賴

```bash
pip install pandas orjson playwright matplotlib
playwright install chromium
```

## 使用方法

```bash
python compare_bitopro_data.py
```

執行後，腳本將：
1. 自動訪問 BitoPro 費用頁面
2. 獲取網頁表格數據
3. 獲取 API 數據
4. 比較兩者的一致性
5. 生成 HTML 報告 (`bitopro_data_comparison_report.html`)

## 報告內容

生成的 HTML 報告包含以下部分：

1. **BitoPro 費用頁面截圖** - 顯示網頁的實際內容
2. **下單限制表比較** - 比較網頁和 API 中的下單限制數據
3. **VIP 費用等級表比較** - 比較網頁和 API 中的 VIP 費用等級數據（如果存在）
4. **API 數據統計分析** - 提供 API 數據的統計信息和視覺化圖表
5. **數據一致性總結** - 總結比較結果

## 注意事項

- 腳本需要網絡連接以訪問 BitoPro 網站和 API
- 如果網站結構發生變化，可能需要更新腳本中的選擇器
- 中文字符在圖表中可能無法正確顯示，這是由於 matplotlib 的字體限制

## 技術細節

- 使用 Playwright 進行網頁自動化
- 使用 pandas 處理表格數據
- 使用 orjson 處理 JSON 數據
- 使用 matplotlib 生成數據視覺化圖表
- 使用 base64 編碼將圖片嵌入 HTML 報告

## 結果示例

執行腳本後，將生成一個名為 `bitopro_data_comparison_report.html` 的報告文件，可以在瀏覽器中打開查看詳細結果。 