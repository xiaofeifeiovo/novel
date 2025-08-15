#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json
import argparse
import os
from urllib.parse import urljoin

def get_page_content(url):
    """获取网页内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = response.apparent_encoding
        return response.text
    except Exception as e:
        print(f"获取页面内容失败: {e}")
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
    content = '\n'.join([p.get_text() for p in content_elements])
    
    # 如果没有找到内容，尝试其他选择器
    if not content:
        content_elements = soup.select('#novel_honbun p')
        content = '\n'.join([p.get_text() for p in content_elements])
    
    # 如果仍然没有找到内容，获取所有可能的文本
    if not content:
        content_elements = soup.find_all('p')
        content = '\n'.join([p.get_text() for p in content_elements])
    
    return title, content

def generate_batch_requests(catalog_url, output_file):
    """生成批处理请求文件"""
    print("正在提取章节链接...")
    chapter_links = extract_chapter_links(catalog_url)
    
    if not chapter_links:
        print("未找到章节链接")
        return
    
    print(f"找到 {len(chapter_links)} 个章节")
    
    batch_requests = []
    
    for i, (title, link) in enumerate(chapter_links):
        print(f"正在处理第 {i+1} 章: {title}")
        chapter_title, content = extract_chapter_content(link)
        
        if content:
            # 创建翻译请求
            request = {
                "action": "TranslateToChinese",
                "id": f"chapter_{i+1}",
                "params": {
                    "text": content,
                    "source_lang": "ja",
                    "target_lang": "zh"
                }
            }
            batch_requests.append(request)
        else:
            print(f"无法提取第 {i+1} 章的内容: {title}")
    
    # 保存批处理请求到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(batch_requests, f, ensure_ascii=False, indent=2)
    
    print(f"批处理请求已保存到 {output_file}")

def main():
    parser = argparse.ArgumentParser(description='生成小说章节翻译的批处理请求')
    parser.add_argument('url', help='小说的目录页URL')
    parser.add_argument('--output', '-o', default='batch_requests.json', help='输出批处理请求文件名')
    args = parser.parse_args()
    
    generate_batch_requests(args.url, args.output)

if __name__ == "__main__":
    main()