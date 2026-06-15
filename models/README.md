# 模型文件说明

本目录下的权重文件体积较大（部分超过 GitHub 单文件 100MB 限制），**未纳入 Git 仓库**。

## 下载方式

请从原项目提供的网盘下载完整 `models` 文件夹，并放置于项目根目录：

- 链接：https://pan.baidu.com/s/1bjtd3ueiUj3rt16p2_YQ2w

## 所需文件清单

| 文件 | 用途 |
|------|------|
| `text_type.h5` | 发票类型文字检测 |
| `text_electronic.h5` | 电子普票文字检测 |
| `text_machine.h5` | 机打发票文字检测 |
| `ocr-lstm.pth` | 中文 CRNN 识别（默认） |
| `Angle-model.pb` / `Angle-model.pbtxt` | 文字方向检测 |
| `text.cfg` / `text.data` / `text.names` / `text.weights` | Darknet 检测（可选） |
| `ocr-dense.pth` / `ocr-english.pth` 等 | 备选识别模型 |

仓库中已保留 `text.cfg`、`text.data`、`text.names`、`Angle-model.pbtxt` 等小体积配置文件。
