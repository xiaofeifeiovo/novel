# 小说下载和翻译工具

这是一个从网页中下载小说并翻译为中文的工具集。

## 功能

1. 输入一个小说的目录网址或者章节网址
2. 如果是目录网址，从页面中提取各个章节的链接，如果是章节网址，跳到第3步
3. 从章节链接网页中提取并下载小说章节的标题和内容
4. 如果整合到一个.txt文件中
5. 检查小说的语言，如果不是中文，使用qwen翻译为中文

## 新增功能

### 批量翻译

为了提高翻译效率，我们新增了两个脚本用于批量翻译：

1. `generate_batch_requests.py` - 生成批处理请求文件
2. `send_batch_request.py` - 向阿里云百炼平台发送批处理请求

## 使用方法

### 1. 下载并翻译单个小说

```bash
python novel_downloader.py <小说目录页或章节页URL> [--output OUTPUT_FILE] [--range RANGE]
```

参数说明：

- `url`: 小说的目录页或章节页URL
- `--output`, `-o`: 输出文件名（可选）
- `--range`, `-r`: 章节范围，例如 "1-10" 表示第1到第10章，"5" 表示第5章
- `--model`, `-m`: 选择翻译模型，可选值为 `qwen-turbo-latest` 或 `qwen-mt-plus`（默认）

示例：

```bash
python novel_downloader.py https://example.com/novel/catalog
python novel_downloader.py https://example.com/novel/catalog --range 1-10
python novel_downloader.py https://example.com/novel/chapter/1
python novel_downloader.py https://example.com/novel/catalog --model qwen-turbo-latest
python novel_downloader.py https://example.com/novel/catalog --model qwen-mt-plus
```

### 2. 生成批处理请求文件

```bash
python generate_batch_requests.py <小说目录页URL> [--output OUTPUT_FILE]
```

参数说明：

- `url`: 小说的目录页URL
- `--output`, `-o`: 输出批处理请求文件名（默认为batch_requests.json）

示例：

```bash
python generate_batch_requests.py https://example.com/novel/catalog
python generate_batch_requests.py https://example.com/novel/catalog --output my_novel_requests.json
```

### 3. 发送批处理请求到阿里云百炼平台

```bash
python send_batch_request.py <批处理请求文件> [--output OUTPUT_FILE]
```

参数说明：

- `batch_file`: 批处理请求文件
- `--output`, `-o`: 输出响应结果文件名（默认为batch_response.json）

示例：

```bash
python send_batch_request.py batch_requests.json
python send_batch_request.py my_novel_requests.json --output my_novel_response.json
```

## 环境变量

为了使用翻译功能，需要设置阿里云百炼平台的API密钥：

```bash
export DASHSCOPE_API_KEY=your_api_key_here
```

在Windows上：

```cmd
set DASHSCOPE_API_KEY=your_api_key_here
```

## 依赖

- requests
- beautifulsoup4
- dashscope
- openai

安装依赖：

```bash
pip install requests beautifulsoup4 dashscope openai
```
