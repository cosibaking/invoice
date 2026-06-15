# 说明
- 该项目基于chineseocr https://github.com/chineseocr/chineseocr
- 商业版本（多模态）合作请联系微信：w1003617636
- 支持其他的卡证及票据类的高精度识别
- 支持行业内的数据相关合作，欢迎联系

# 增值税发票识别 
  增值税发票OCR识别，使用flask微服务架构，识别type：增值税电子普通发票，增值税普通发票，增值税专用发票；识别字段为：发票代码、发票号码、开票日期、校验码、税后金额等。
  
  识别type：增值税电子普通发票，增值税普通发票，增值税专用发票；识别字段为：发票代码、发票号码、开票日期、校验码、税后金额等
## 环境
   1. python3.5/3.6
   2. 依赖项安装：pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple 
   3. 有GPU环境的可修改安装requirements.txt对应版本的tensorflow-gpu，config.py文件中控制GPU的开关
## 模型架构
    YOLOv3 + CRNN + CTC
   
## 模型
   1. 模型下载地址：链接：https://pan.baidu.com/s/1bjtd3ueiUj3rt16p2_YQ2w
   2. 将下载完毕的模型文件夹models放置于项目根目录下
## 服务启动
   1. python3 app.py
   2. 端口可自行修改
   3. 服务调用地址：http://*.*.*.*: [端口号]/invoice-ocr，例：http://127.0.0.1:11111/invoice-ocr
## 测试demo
   1. 测试工具：postman，可自行下载安装
   2. 增值税电子普票测试结果
   
![Image text](https://github.com/guanshuicheng/invoice/blob/master/test-invoice/%E7%94%B5%E5%AD%90%E5%8F%91%E7%A5%A8-test.png)
   
   3. 增值税专用普票测试结果
   
![Image text](https://github.com/guanshuicheng/invoice/blob/master/test-invoice/%E5%A2%9E%E5%80%BC%E7%A8%8E%E4%B8%93%E7%94%A8%E5%8F%91%E7%A5%A8-test.png)

   4. 增值税普通普票测试结果

![Image text](https://github.com/guanshuicheng/invoice/blob/master/test-invoice/%E5%A2%9E%E5%80%BC%E7%A8%8E%E6%99%AE%E9%80%9A%E5%8F%91%E7%A5%A8-test.jpg)
## 支持的票种（docType）

| docType | 说明 |
|---------|------|
| vat_e | 增值税电子普通发票 |
| vat_m | 增值税普通/专用发票（机打） |
| digital_vat | 数电票 |
| itinerary | 电子行程单 |
| train | 铁路电子客票 |
| taxi | 出租车发票 |
| unknown | 未匹配票种（仅返回 OCR 行） |

票种路由与检测模型见 config.py 中的 DOC_TYPES。

## API 响应格式

主接口 `POST /invoice-ocr` 成功时 `data` 包含：

- `docType`：票种标识
- `docTypeName`：票种中文名
- `fields`：结构化字段（解析器或 LLM 兜底填充）
- `rawLines`：OCR 原始行列表（含坐标与文本）

示例：

```json
{
  "code": 100,
  "message": "识别成功",
  "data": {
    "docType": "vat_e",
    "docTypeName": "增值税电子普通发票",
    "fields": {},
    "rawLines": []
  },
  "FileName": "invoice.jpg",
  "ocrIdentifyTime": "2026-06-15 16:00:00"
}
```

## 调试接口

`POST /ocr-raw`：仅对上传图片做 OCR，返回 `data.rawLines`，不做票种路由与字段解析，便于标注新票种。

## LLM 兜底配置

复制 `config/settings.local.yaml.example` 为 `config/settings.local.yaml`（可选），或在 `config/settings.yaml` 中配置 `llm_fallback`：

- `enabled`：是否启用
- `api_url` / `api_key` / `model`：兼容 OpenAI 的 HTTP API
- `timeout_seconds` / `max_retries`

当结构化解析结果为空且 docType 非 unknown 时，可调用 LLM 补全 `fields`。

## 批量回归测试

```bash
python scripts/batch_test.py --dir test/fixtures/digital_vat
python scripts/batch_test.py --dir test/fixtures/unknown
python scripts/batch_test.py --dir test/fixtures/vat_e   # 需先放入样本
python scripts/batch_test.py --dir test/fixtures/vat_m   # 需先放入样本
```

各 fixture 目录放置样本图片与 `expected.json`（期望 `code`、`docType`、`fields`）。可按文件名在 `expected.json` 的 `samples` 中配置期望值，例如 `sample.jpg`。
