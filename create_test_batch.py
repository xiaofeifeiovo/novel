#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

# 创建一个简单的测试用批处理请求文件
test_requests = [
    {
        "action": "TranslateToChinese",
        "id": "test_chapter_1",
        "params": {
            "text": "これはテスト用の日本語テキストです。翻訳が正しく動作することを確認してください。",
            "source_lang": "ja",
            "target_lang": "zh"
        }
    },
    {
        "action": "TranslateToChinese",
        "id": "test_chapter_2",
        "params": {
            "text": "もう一つのテスト用テキストです。長めの文章も正しく翻訳できるか確認します。",
            "source_lang": "ja",
            "target_lang": "zh"
        }
    }
]

# 保存到文件
with open('test_batch_requests.json', 'w', encoding='utf-8') as f:
    json.dump(test_requests, f, ensure_ascii=False, indent=2)

print("测试用批处理请求文件已创建: test_batch_requests.json")