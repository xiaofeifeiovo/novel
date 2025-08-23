#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import time
import os
from urllib.parse import urljoin, urlparse
import argparse
import json
from openai import OpenAI

# 阿里云百炼平台的API密钥和模型名称
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')  # 从环境变量读取API密钥
DEFAULT_MODEL = "qwen-mt-plus"  # 默认使用qwen-mt-plus模型

# 初始化OpenAI客户端用于qwen-mt-plus模型
client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def is_chinese(text):
    """检查文本是否包含中文字符"""
    if not text:
        return False
    # 匹配中文汉字（不包括日文假名）
    chinese_pattern = re.compile(r'[\\u4e00-\\u9fff]+')
    return bool(chinese_pattern.search(text))

def is_japanese(text):
    """检查文本是否包含日文字符（包括假名）"""
    if not text:
        return False
    # 匹配日文假名
    japanese_pattern = re.compile(r'[\\u3040-\\u309f\\u30a0-\\u30ff]+')
    return bool(japanese_pattern.search(text))

def is_likely_japanese(text):
    """通过更复杂的规则判断是否可能是日文文本"""
    if not text:
        return False
    
    # 检查是否包含日文假名
    if is_japanese(text):
        return True
    
    # 检查是否包含日文特征标点符号
    japanese_punct = re.compile(r'[「」『』（）｛｝［］]')
    if japanese_punct.search(text):
        return True
    
    # 检查是否包含片假名（常用于外来语）
    katakana_pattern = re.compile(r'[\\u30a0-\\u30ff]+')
    if katakana_pattern.search(text):
        return True
    
    # 计算中文和日文字符的数量
    chinese_chars = re.findall(r'[\\u4e00-\\u9fff]', text)
    hiragana_chars = re.findall(r'[\\u3040-\\u309f]', text)
    katakana_chars = re.findall(r'[\\u30a0-\\u30ff]', text)
    
    # 计算中日文字符总数
    total_cjk_chars = len(chinese_chars) + len(hiragana_chars) + len(katakana_chars)
    
    # 如果总字符数为0，返回False
    if total_cjk_chars == 0:
        return False
    
    # 如果包含假名，肯定是日文
    if len(hiragana_chars) + len(katakana_chars) > 0:
        return True
    
    # 如果中文字符占总中日文字符比例小于70%，则认为是日文
    if total_cjk_chars > 0 and len(chinese_chars) / total_cjk_chars < 0.7:
        return True
    
    return False

def translate_to_chinese(text, model_name=DEFAULT_MODEL):
    """使用阿里云百炼平台的Qwen模型将文本翻译为中文"""
    if not text:
        return text
        
    # 使用更复杂的规则判断是否需要翻译
    likely_japanese = is_likely_japanese(text)
    has_chinese = is_chinese(text)
    has_japanese = is_japanese(text)
    
    print(f"语言检测结果 - 中文: {has_chinese}, 日文: {has_japanese}, 可能是日文: {likely_japanese}")
    
    # 如果明显是中文且不包含日文特征，则不需要翻译
    if has_chinese and not likely_japanese:
        print("内容已为中文，无需翻译")
        return text
    
    # 如果可能是日文，则进行翻译
    if likely_japanese or not has_chinese:
        print("开始翻译...")
        
        # 检查文本长度，如果超过4k则按换行符截断
        max_length = 4000  # 4k限制
        if len(text) > max_length:
            print(f"文本长度 {len(text)} 超过4k限制，将按换行符截断到 {max_length} 字符以内")
            # 按换行符截断，避免破坏文本结构
            lines = text.split('\n')
            truncated_text = ""
            for line in lines:
                if len(truncated_text) + len(line) + 1 <= max_length:
                    truncated_text += line + "\n"
                else:
                    break
            text = truncated_text.rstrip('\n')  # 移除末尾的换行符
        
        # 只取前1000个字符进行测试
        test_text = text[:1000] + "..." if len(text) > 1000 else text
        print(f"待翻译文本示例: {test_text}")
        
        # 根据模型名称选择不同的调用方法
        if model_name == "qwen-mt-plus":
            return translate_with_qwen_mt_plus(text)
        else:
            return translate_with_qwen_turbo(text, model_name)
    else:
        # 已经是中文或混合文本
        print("内容已为中文，无需翻译")
        return text


def translate_with_qwen_mt_plus(text):
    """使用qwen-mt-plus模型翻译文本"""
    try:
        # 使用翻译选项而不是系统提示词
        translation_options = {
            "source_lang": "auto",
            "target_lang": "Chinese"
        }
        
        # 增加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                completion = client.chat.completions.create(
                    model="qwen-mt-plus",
                    messages=[
                        {
                            "role": "user",
                            "content": text
                        }
                    ],
                    extra_body={
                        "translation_options": translation_options
                    },
                    # 增加超时时间
                    timeout=60
                )
                
                if completion.choices and completion.choices[0].message.content:
                    print("翻译完成")
                    return completion.choices[0].message.content
                else:
                    error_msg = "未知错误"
                    print(f"翻译失败: {error_msg}")
                    # 如果不是最后一次尝试，等待后重试
                    if attempt < max_retries - 1:
                        print(f"第{attempt + 1}次尝试失败，等待5秒后重试...")
                        time.sleep(5)
                    else:
                        print("所有重试都失败了，返回原文")
                        return text
            except Exception as e:
                print(f"第{attempt + 1}次翻译请求出错: {e}")
                if attempt < max_retries - 1:
                    print("等待5秒后重试...")
                    time.sleep(5)
                else:
                    print("所有重试都失败了，返回原文")
                    return text
    except Exception as e:
        print(f"翻译过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return text


def translate_with_qwen_turbo(text, model_name):
    """使用qwen-turbo模型翻译文本"""
    try:
        import dashscope
        dashscope.api_key = DASHSCOPE_API_KEY
        
        # 使用标准Generation接口
        prompt = f"请将以下日文小说内容翻译成中文，保持原文的语气和风格：\n\n{text}"
        
        # 增加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = dashscope.Generation.call(
                    model=model_name,
                    prompt=prompt,
                    # 增加超时时间
                    timeout=60
                )
                
                if response.status_code == 200 and response.output and response.output.text:
                    print("翻译完成")
                    return response.output.text
                else:
                    error_msg = response.message if response and response.message else "未知错误"
                    print(f"翻译失败: {error_msg}")
                    # 打印响应详情用于调试
                    if hasattr(response, '__dict__'):
                        print(f"响应详情: {response.__dict__}")
                    # 如果不是最后一次尝试，等待后重试
                    if attempt < max_retries - 1:
                        print(f"第{attempt + 1}次尝试失败，等待5秒后重试...")
                        time.sleep(5)
                    else:
                        print("所有重试都失败了，返回原文")
                        return text
            except Exception as e:
                print(f"第{attempt + 1}次翻译请求出错: {e}")
                if attempt < max_retries - 1:
                    print("等待5秒后重试...")
                    time.sleep(5)
                else:
                    print("所有重试都失败了，返回原文")
                    return text
    except ImportError:
        print("未安装dashscope库，无法进行翻译")
        return text
    except Exception as e:
        print(f"翻译过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return text

def get_page_content(url):
    """获取网页内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)  # 增加超时时间
        response.encoding = response.apparent_encoding
        return response.text
    except Exception as e:
        print(f"获取页面内容失败: {e}")
        return None

def extract_novel_title(catalog_url):
    """从目录页提取小说标题"""
    html_content = get_page_content(catalog_url)
    if not html_content:
        return None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    title_element = soup.select_one('.p-novel__title')
    if title_element:
        return title_element.get_text(strip=True)
    return None

def extract_chapter_links(catalog_url):
    """从目录页提取章节链接"""
    html_content = get_page_content(catalog_url)
    if not html_content:
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    chapter_links = []
    
    # 查找所有章节链接
    for link in soup.select('.p-eplist__sublist a'):
        href = link.get('href')
        title = link.get_text(strip=True)
        if href:
            full_url = urljoin(catalog_url, href)
            chapter_links.append((title, full_url))
    
    return chapter_links

def extract_chapter_content(chapter_url):
    """从章节页提取标题和内容"""
    html_content = get_page_content(chapter_url)
    if not html_content:
        return None, None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 提取标题
    title_element = soup.select_one('.p-novel__title')
    title = title_element.get_text(strip=True) if title_element else "未知章节"
    
    # 提取内容
    content_elements = soup.select('.p-novel__text p')
    content = '\\n'.join([p.get_text() for p in content_elements])
    
    # 如果没有找到内容，尝试其他选择器
    if not content:
        content_elements = soup.select('#novel_honbun p')
        content = '\\n'.join([p.get_text() for p in content_elements])
    
    # 如果仍然没有找到内容，获取所有可能的文本
    if not content:
        content_elements = soup.find_all('p')
        content = '\\n'.join([p.get_text() for p in content_elements])
    
    print(f"提取到章节内容，长度: {len(content)} 字符")
    return title, content

def save_to_txt(chapters, filename):
    """将章节内容保存到txt文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        for i, (title, content) in enumerate(chapters):
            # 在章节之间添加明确的分隔
            if i > 0:
                f.write("\n" + "="*50 + "\n\n")
            f.write(f"{title}\n\n{content}\n")
    print(f"小说已保存到 {filename}")

def parse_chapter_range(range_str):
    """解析章节范围字符串，例如 '1-10' 或 '5'"""
    if not range_str:
        return None, None
    
    try:
        if '-' in range_str:
            start, end = range_str.split('-')
            start = int(start) if start else None
            end = int(end) if end else None
            return start, end
        else:
            num = int(range_str)
            return num, num
    except ValueError:
        print(f"无效的章节范围格式: {range_str}，将下载所有章节")
        return None, None

def generate_default_filename(novel_title, start_chapter=None, end_chapter=None):
    """生成默认文件名"""
    import datetime
    
    if novel_title:
        filename = novel_title
    else:
        # 使用当前日期和时间作为文件名
        now = datetime.datetime.now()
        filename = now.strftime("%Y%m%d_%H%M%S")
    
    # 如果指定了章节范围，在文件名中添加范围信息
    if start_chapter is not None or end_chapter is not None:
        if start_chapter is not None and end_chapter is not None:
            filename += f"_第{start_chapter}到第{end_chapter}章"
        elif start_chapter is not None:
            filename += f"_从第{start_chapter}章开始"
        elif end_chapter is not None:
            filename += f"_到第{end_chapter}章结束"
    
    return filename + ".txt"

def main():
    parser = argparse.ArgumentParser(description='下载小说并翻译为中文')
    parser.add_argument('url', help='小说的目录页或章节页URL')
    parser.add_argument('--output', '-o', help='输出文件名')
    parser.add_argument('--range', '-r', help='章节范围，例如 "1-10" 表示第1到第10章，"5" 表示第5章')
    parser.add_argument('--model', '-m', default=DEFAULT_MODEL, choices=['qwen-turbo-latest', 'qwen-mt-plus'], help='选择翻译模型')
    args = parser.parse_args()
    
    url = args.url
    start_chapter, end_chapter = parse_chapter_range(args.range)
    
    # 检查是否设置了API密钥
    if not DASHSCOPE_API_KEY:
        print("警告: 未设置DASHSCOPE_API_KEY环境变量，将不会进行翻译")
    
    # 判断是目录页还是章节页
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip('/').split('/')
    
    if len(path_parts) >= 2 and path_parts[-1].isdigit():
        # 章节页
        print("检测到章节页URL，直接下载该章节...")
        title, content = extract_chapter_content(url)
        if title and content:
            print(f"检测到章节语言...")
            # 使用新的语言检测函数
            content = translate_to_chinese(content, args.model)
            
            # 生成默认文件名
            if args.output:
                output_file = args.output
            else:
                # 尝试从URL中提取小说标题
                catalog_url = "/".join(url.split("/")[:-2]) + "/"
                novel_title = extract_novel_title(catalog_url)
                output_file = generate_default_filename(novel_title)
            
            save_to_txt([(title, content)], output_file)
        else:
            print("无法提取章节内容")
    else:
        # 目录页
        print("检测到目录页URL，正在提取所有章节链接...")
        chapter_links = extract_chapter_links(url)
        
        if not chapter_links:
            print("未找到章节链接")
            return
        
        # 根据指定范围过滤章节
        if start_chapter is not None or end_chapter is not None:
            # 转换为0基索引
            start_idx = start_chapter - 1 if start_chapter is not None else 0
            end_idx = end_chapter if end_chapter is not None else len(chapter_links)
            
            # 确保索引在有效范围内
            start_idx = max(0, start_idx)
            end_idx = min(len(chapter_links), end_idx)
            
            chapter_links = chapter_links[start_idx:end_idx]
            print(f"根据指定范围 {args.range}，将下载第 {start_chapter if start_chapter else 1} 到第 {end_chapter if end_chapter else len(chapter_links)+start_idx} 章")
        else:
            print(f"找到 {len(chapter_links)} 个章节，开始下载...")
        
        if not chapter_links:
            print("指定的章节范围无效")
            return
        
        chapters = []
        
        for i, (title, link) in enumerate(chapter_links, start=1):
            # 计算实际章节号
            actual_chapter_num = start_chapter + i - 1 if start_chapter is not None else i
            print(f"正在下载第 {actual_chapter_num} 章: {title}")
            chapter_title, content = extract_chapter_content(link)
            
            if chapter_title and content:
                print(f"检测到章节语言...")
                # 使用新的语言检测函数
                content = translate_to_chinese(content, args.model)
                
                chapters.append((chapter_title, content))
                # 添加延时，避免请求过于频繁
                time.sleep(2)  # 增加延迟时间
            else:
                print(f"无法下载章节: {title}")
        
        if chapters:
            # 生成默认文件名
            if args.output:
                output_file = args.output
            else:
                # 提取小说标题
                novel_title = extract_novel_title(url)
                output_file = generate_default_filename(novel_title, start_chapter, end_chapter)
            
            save_to_txt(chapters, output_file)
        else:
            print("没有成功下载任何章节")

if __name__ == "__main__":
    main()