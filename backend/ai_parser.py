"""
ai_parser.py — AI 列映射解析
支持 Gemini（免费 API）和 Ollama（本地）
"""
import os, json, hashlib
from pathlib import Path
import pandas as pd

CACHE_PATH = Path(__file__).parent / "column_cache.json"

def load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH) as f:
            return json.load(f)
    return {}

def save_cache(cache: dict):
    with open(CACHE_PATH, 'w') as f:
        json.dump(cache, f, indent=2)

def get_cache_key(headers: list) -> str:
    header_text = '|'.join(str(h) for h in headers if h)
    return hashlib.md5(header_text.encode()).hexdigest()[:12]

def call_gemini(prompt: str) -> str:
    """调 Google Gemini API"""
    import google.generativeai as genai
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY 未设置")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    resp = model.generate_content(prompt)
    return resp.text.strip()

def call_ollama(prompt: str) -> str:
    """调本地 Ollama"""
    import requests
    try:
        r = requests.post('http://localhost:11434/api/chat', json={
            'model': 'qwen2.5:7b',
            'messages': [{'role': 'user', 'content': prompt}],
            'stream': False
        }, timeout=30)
        return r.json()['message']['content'].strip()
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Ollama 未运行。先启动: ollama run qwen2.5:7b")

def build_prompt(md_table: str) -> str:
    return f"""你是一个外贸产品数据提取助手。分析以下产品表格的列结构。

{md_table}

返回 JSON：
{{
  "name_col": 0,
  "price_col": 3,
  "spec_col": 2,
  "model_col": null,
  "qty_col": 1
}}
- name_col: 产品名称列（索引从0开始），没有就null
- price_col: 价格列
- spec_col: 规格/参数列
- model_col: 型号列（与name合并时为null）
- qty_col: 数量/包装列

只返回 JSON，不要其他文字。"""

def ai_detect_columns(md_table: str, backend='gemini') -> dict:
    """AI 分析列映射"""
    prompt = build_prompt(md_table)
    try:
        if backend == 'gemini':
            text = call_gemini(prompt)
        else:
            text = call_ollama(prompt)
        # Clean response (remove markdown code blocks if any)
        text = text.strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[-1]
            text = text.rsplit('\n', 1)[0] if text.endswith('```') else text
        return json.loads(text)
    except Exception as e:
        raise RuntimeError(f"AI 列映射失败: {str(e)}")
