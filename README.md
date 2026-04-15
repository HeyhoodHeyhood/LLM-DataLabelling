# 数据自动标注工具

**[English](#english) | 中文**

基于 OpenAI Vision API 的轻量级命令行图片自动标注工具。配置驱动，无需改代码。

## 功能特点

- 批量标注一个文件夹内的所有图片
- 支持多个 API Key 自动轮询，均摊请求压力
- 输出格式可配置：内置 **default / COCO / YOLO** 三种预设，支持完全自定义
- JSON 解析失败时自动 fallback 到原始文本，不中断整体流程

## 环境要求

- Python 3.10+
- 有访问 Vision 模型权限的 OpenAI API Key（`gpt-4o-mini` 或更高）

## 安装

```bash
pip install -r requirements.txt
```

设置 API Key（支持多个，逗号分隔）：

```bash
export OPENAI_API_KEY="sk-key1,sk-key2,sk-key3"
```

## 快速开始

```bash
python -m annotool.cli --config configs/image.yaml
```

查看结果：

```bash
cat outputs/annotations.json
```

## 配置文件说明

### 主配置 `configs/image.yaml`

```yaml
input_dir: examples               # 待标注图片目录
output: outputs/annotations.json  # 结果输出路径
model: gpt-4o-mini                # 使用的模型

# 多 API Key（也可通过环境变量 OPENAI_API_KEY 逗号分隔传入）
# api_keys:
#   - sk-key1
#   - sk-key2

# 指定输出格式（不填则使用 default 预设）
# task_schema: configs/task_schema.yaml
```

### 输出格式配置 `configs/task_schema.yaml`

通过 `preset` 字段选择内置预设，或设置 `preset: custom` 完全自定义。

| 预设 | 说明 |
|------|------|
| `default` | 通用标注：objects 列表 + caption |
| `coco` | COCO 风格：categories + bbox（归一化 xywh）+ caption |
| `yolo` | YOLO 风格：class_id + bbox（归一化 xywh） |
| `custom` | 自定义标签列表和输出字段 |

**使用预设：**

```yaml
preset: coco
```

**完全自定义：**

```yaml
preset: custom
labels:
  - car
  - person
  - traffic_light
output_fields:
  - label
  - confidence
  - description
```

## 输出格式示例

<details>
<summary><b>default</b></summary>

```json
[
  {
    "image": "sample.jpg",
    "annotation": {
      "objects": [
        {"label": "house", "description": "a small house with red roof"},
        {"label": "tree",  "description": "a green tree on the left"}
      ],
      "caption": "A simple house beside a tree under blue sky."
    }
  }
]
```
</details>

<details>
<summary><b>coco</b></summary>

```json
[
  {
    "image": "sample.jpg",
    "annotation": {
      "categories": ["house", "tree"],
      "objects": [
        {"label": "house", "bbox": [0.31, 0.46, 0.38, 0.25]},
        {"label": "tree",  "bbox": [0.07, 0.40, 0.15, 0.29]}
      ],
      "caption": "A simple house beside a tree."
    }
  }
]
```

bbox 格式：`[x_center, y_center, width, height]`，均归一化到 0–1。
</details>

<details>
<summary><b>yolo</b></summary>

```json
[
  {
    "image": "sample.jpg",
    "annotation": {
      "labels": ["house", "tree"],
      "objects": [
        {"class_id": 0, "bbox": [0.31, 0.46, 0.38, 0.25]},
        {"class_id": 1, "bbox": [0.07, 0.40, 0.15, 0.29]}
      ]
    }
  }
]
```
</details>

## 错误处理

| 情况 | 行为 |
|------|------|
| API 返回非 JSON 文本 | fallback 到 `{"raw": "..."}` 并打印警告，继续处理 |
| API 调用抛出异常 | 记录 `{"annotation": null, "error": "..."}` 并继续 |

## 项目结构

```
├── README.md
├── requirements.txt
├── annotool/
│   ├── cli.py          # 命令行入口
│   ├── pipeline.py     # 主流程：收集 → 标注 → 保存
│   ├── api.py          # OpenAI Vision API + 多 Key 轮询
│   ├── schema.py       # 数据类与配置定义
│   └── utils.py        # 图片编码、JSON 解析、文件 I/O
├── configs/
│   ├── image.yaml      # 主配置
│   └── task_schema.yaml  # 输出格式定义
├── examples/
│   └── sample.jpg
└── outputs/
```

---

## English

**[中文](#数据自动标注工具) | English**

A minimal, config-driven CLI tool for automatic image annotation using the OpenAI Vision API.

### Features

- Batch-annotates a folder of images with a single command
- Supports multiple API keys with round-robin rotation
- Built-in output presets: **default**, **COCO**, **YOLO** — or fully custom
- JSON parse failures fall back to raw text; processing never stops mid-run

### Requirements

- Python 3.10+
- OpenAI API key with access to a vision-capable model (`gpt-4o-mini` or better)

### Installation

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="sk-key1,sk-key2"   # comma-separate for multiple keys
```

### Usage

```bash
python -m annotool.cli --config configs/image.yaml
```

### Config — `configs/image.yaml`

```yaml
input_dir: examples
output: outputs/annotations.json
model: gpt-4o-mini

# optional multi-key rotation (or set via OPENAI_API_KEY env var)
# api_keys:
#   - sk-key1
#   - sk-key2

# optional output format definition
# task_schema: configs/task_schema.yaml
```

### Output format — `configs/task_schema.yaml`

| Preset | Description |
|--------|-------------|
| `default` | Generic: objects list + caption |
| `coco` | COCO-style: categories + normalized bbox + caption |
| `yolo` | YOLO-style: class_id + normalized bbox |
| `custom` | User-defined labels and output fields |

See [configs/task_schema.yaml](configs/task_schema.yaml) for full documentation.
