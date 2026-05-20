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


def call_deepseek(prompt: str, model="deepseek-chat") -> str:
    """调 DeepSeek 官方 API（OpenAI 兼容）"""
    import requests
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 未设置")
    try:
        resp = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一个外贸产品数据提取助手。从用户提供的文本中提取所有产品信息，返回 JSON。"},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
            },
            timeout=45,
        )
        if not resp.ok:
            raise RuntimeError(f"DeepSeek API error: {resp.status_code} {resp.text[:300]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        raise ConnectionError("无法连接 DeepSeek API")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise RuntimeError(f"DeepSeek 返回格式异常: {e}")


def call_openrouter(prompt: str, model="deepseek/deepseek-v4-flash") -> str:
    """调 OpenRouter API（兼容 OpenAI 格式）"""
    import requests
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY 未设置")
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://localhost:3000",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一个外贸产品数据提取助手。从用户提供的文本中提取所有产品信息，返回 JSON。"},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
            },
            timeout=45,
        )
        if not resp.ok:
            raise RuntimeError(f"OpenRouter API error: {resp.status_code} {resp.text[:200]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        raise ConnectionError("无法连接 OpenRouter API")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise RuntimeError(f"OpenRouter 返回格式异常: {e}")

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

TEXT_TO_PRODUCTS_PROMPT = """你是一个外贸产品数据提取助手。从用户提供的自由格式文本中提取所有产品信息。

文本内容：
{text}

要求：
1. 找出所有产品，每个产品提取：型号(model)、品名(name_zh)、规格(spec)、价格(price_rmb，单位人民币元)、数量(quantity)、原始币种(currency)
2. 如果文本中有价格但不是人民币，按 1 USD = 7.2 CNY 换算为 price_rmb
3. 如果文本中没明确价格，price_rmb 设为 null
4. 如果文本中没明确数量，quantity 设为 1
5. 中英混杂也没关系，尽力提取
6. 没找到任何产品时返回 {{"products": []}}

只返回 JSON：{{"products": [{{"model": "", "name_zh": "", "spec": "", "price_rmb": null, "quantity": 1, "currency": "CNY"}}]}}"""


def parse_text_to_products(text: str, backend='deepseek') -> list:
    """用 LLM 从自由文本提取结构化产品列表"""
    if not text or not text.strip():
        return []
    prompt = TEXT_TO_PRODUCTS_PROMPT.format(text=text[:6000])
    try:
        if backend == 'deepseek':
            raw = call_deepseek(prompt)
        elif backend == 'openrouter':
            raw = call_openrouter(prompt)
        elif backend == 'gemini':
            raw = call_gemini(prompt)
        else:
            raw = call_ollama(prompt)
        raw = raw.strip()
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[-1]
            raw = raw.rsplit('\n', 1)[0] if raw.endswith('```') else raw
        result = json.loads(raw)
        products = result.get('products', [])
        return products
    except Exception as e:
        raise RuntimeError(f"文本解析失败: {str(e)}")


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
