#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import argparse
import time
import os

# 阿里云百炼平台的API配置
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
API_URL = "https://dashscope.aliyuncs.com/api/v1/services/translateto/chinese"

def send_batch_request(batch_file, output_file, model_name='qwen-mt-plus'):
    """发送批处理请求到阿里云百炼平台"""
    if not DASHSCOPE_API_KEY:
        print("错误: 未设置DASHSCOPE_API_KEY环境变量")
        return
    
    # 读取批处理请求文件
    try:
        with open(batch_file, 'r', encoding='utf-8') as f:
            batch_requests = json.load(f)
    except Exception as e:
        print(f"无法读取批处理请求文件: {e}")
        return
    
    print(f"读取到 {len(batch_requests)} 个请求")
    
    # 准备API请求
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 根据模型类型构建批处理请求体
    if model_name == 'qwen-mt-plus':
        # qwen-mt-plus 模型不需要系统提示词
        payload = {
            "model": "qwen-mt-plus",
            "input": {},
            "parameters": {
                "batch": batch_requests,
                "source_lang": "auto",
                "target_lang": "Chinese"
            }
        }
    else:
        # qwen-turbo-latest 模型需要系统提示词
        payload = {
            "model": "qwen-turbo-latest",
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的日文小说翻译者，请将以下日文小说内容翻译成中文，保持原文的语气和风格。"
                    }
                ]
            },
            "parameters": {
                "batch": batch_requests
            }
        }
    
    print("正在发送批处理请求...")
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("批处理请求发送成功")
            
            # 保存响应结果
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"响应结果已保存到 {output_file}")
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"发送请求时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description='向阿里云百炼平台发送批处理翻译请求')
    parser.add_argument('batch_file', help='批处理请求文件')
    parser.add_argument('--output', '-o', default='batch_response.json', help='输出响应结果文件名')
    parser.add_argument('--model', '-m', default='qwen-mt-plus', choices=['qwen-turbo-latest', 'qwen-mt-plus'], help='选择翻译模型')
    args = parser.parse_args()
    
    send_batch_request(args.batch_file, args.output, args.model)

if __name__ == "__main__":
    main()