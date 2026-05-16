"""
NLP Filter Parser using Phi-3 LLM

Converts natural language queries to pandas filter expressions.

Usage:
    # With model (if downloaded):
    from src.nlp.filter_parser import parse_filter
    query = parse_filter("价格大于100且小于500", df.columns.tolist())

    # Without model (using basic parser):
    from src.nlp.filter_parser import parse_filter_safe
    query = parse_filter_safe("价格大于100且小于500", columns)
"""
import os
import re
from pathlib import Path
from typing import Optional, List

# Model configuration
MODEL_DIR = Path("models")
MODEL_FILENAME = "Phi-3-mini-4k-instruct-q4_k_M.gguf"
MODEL_PATH = MODEL_DIR / MODEL_FILENAME

# Fallback model files to try
MODEL_VARIANTS = [
    "Phi-3-mini-4k-instruct-q4_k_M.gguf",
    "phi-3-mini-q4.gguf",
    "Phi-3-mini-4k-instruct.gguf",
]


def find_model() -> Optional[Path]:
    """Find the Phi-3 model file."""
    # Check main path
    if MODEL_PATH.exists():
        return MODEL_PATH

    # Try variants
    for variant in MODEL_VARIANTS:
        path = MODEL_DIR / variant
        if path.exists():
            return path

    # List any .gguf in models/
    for f in MODEL_DIR.glob("*.gguf"):
        if f.stat().st_size > 100_000_000:  # > 100MB
            return f

    return None


def load_model():
    """Load the Phi-3 model."""
    model_path = find_model()

    if not model_path:
        return None

    print(f"  Loading model from {model_path.name}...")

    try:
        from ctransformers import LLM

        llm = LLM(
            model_path=str(model_path),
            model_type="phi",
            config={'max_tokens': 256},
        )

        print("  Model loaded!")
        return llm

    except Exception as e:
        print(f"  Error loading model: {e}")
        return None


_llm_instance = None


def get_llm():
    """Get or load the LLM instance (singleton)."""
    global _llm_instance

    if _llm_instance is None:
        _llm_instance = load_model()

    return _llm_instance


def build_prompt(user_input: str, df_columns: List[str]) -> str:
    """Build the prompt for filter conversion."""

    columns_str = ", ".join(df_columns)

    prompt = f"""你是一个pandas查询生成器。根据用户的自然语言描述，生成pandas DataFrame查询表达式。

可用列名: {columns_str}
只输出查询表达式，不要有其他解释。不要使用中文。

示例:
用户输入: 价格大于100美元的产品
输出: price_usd > 100

用户输入: 价格小于1000或者颜色是红色的
输出: (price_usd < 1000) | (color == '红色')

用户输入: 名称包含"电动"且价格不超过500
输出: name_zh.str.contains('电动', na=False) & (price_usd <= 500)

现在：
用户输入: {user_input}
输出:"""

    return prompt


def _clean_output(text: str) -> str:
    """Clean the model output."""
    # Remove whitespace
    text = text.strip()

    # Remove common prefixes/suffixes
    for prefix in ["```python", "```", "```py"]:
        text = text.replace(prefix, "")

    text = text.strip()

    # Remove trailing ) if unmatched
    while text.startswith("(") and text.endswith(")"):
        # Check if parenthesis are balanced
        count = text.count("(") - text.count(")")
        if count == 0:
            text = text[1:-1]
        else:
            break

    return text.strip()


def parse_filter(user_input: str, df_columns: List[str]) -> Optional[str]:
    """
    Convert user input to pandas filter expression.

    Args:
        user_input: Natural language query (e.g., "价格大于10美元小于100美元")
        df_columns: Available DataFrame columns

    Returns:
        pandas query string, or None if failed
    """
    if not user_input or not df_columns:
        return None

    # Get LLM
    llm = get_llm()

    if llm is None:
        print("  警告: 模型未加载，无法解析过滤条件")
        return None

    # Build prompt
    prompt = build_prompt(user_input, df_columns)

    try:
        # Generate
        result = llm(prompt, max_new_tokens=128)

        # Extract output
        if hasattr(result, "strip"):
            output = result.strip()
        elif isinstance(result, list) and len(result) > 0:
            output = result[0].get("text", "").strip()
        else:
            output = str(result)

        # Clean
        output = _clean_output(output)

        # Basic validation
        if not output or len(output) < 3:
            return None

        # Must contain column names
        has_column = any(col in output for col in df_columns)
        if not has_column:
            print(f"  警告: 输出不包含有效列名: {output}")
            return None

        print(f"  解析: {output}")
        return output

    except Exception as e:
        print(f"  错误: {e}")
        return None


def parse_filter_safe(user_input: str, df_columns: List[str]) -> str:
    """
    Safe wrapper that returns user_input as-is if parsing fails.

    For testing/demo when no model is available.
    """
    result = parse_filter(user_input, df_columns)

    if result is None:
        # Fallback: create basic filter
        print("  使用基础解析 (无模型)")
        return _basic_parse(user_input, df_columns)

    return result


def _basic_parse(user_input: str, df_columns: List[str]) -> str:
    """Basic parsing without LLM (keyword matching)."""

    user_lower = user_input.lower()
    parts = []

    # Price keywords
    if "价格" in user_input or "price" in user_lower:
        price_col = "price_usd" if "price_usd" in df_columns else "price_rmb"

        if ">" in user_input or "大于" in user_input or "高于" in user_input:
            # Try extract number
            import re
            nums = re.findall(r"\d+", user_input)
            if nums:
                parts.append(f"{price_col} > {nums[0]}")

        if "<" in user_input or "小于" in user_input or "低于" in user_input:
            import re
            nums = re.findall(r"\d+", user_input)
            if nums:
                parts.append(f"{price_col} < {nums[-1]}")

    if not parts:
        return "True"  # No filter

    return " & ".join(parts)


if __name__ == "__main__":
    # Fix encoding for Windows console
    import sys
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # Test basic filter parser
    print("=" * 40)
    print("测试过滤解析")
    print("=" * 40)

    columns = [
        "model", "name_zh", "name_en", "spec_zh", "spec_en",
        "color", "package", "price_rmb", "price_usd"
    ]

    # Test cases
    test_cases = [
        "价格大于100且小于500",
        "价格小于1000或者颜色是红色",
        "显示所有产品",
    ]

    for test in test_cases:
        result = parse_filter_safe(test, columns)
        print(f"\n输入: {test}")
        print(f"输出: {result}")