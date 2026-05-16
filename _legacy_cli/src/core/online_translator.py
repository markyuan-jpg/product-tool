"""
Online translation API for English to Chinese fallback.
Uses MyMemory API (free 1000 chars/day)
"""
import requests
import re


def translate_en_to_zh(text: str) -> str:
    """
    Translate English text to Chinese using MyMemory API.
    Returns original if translation fails.
    """
    if not text or not text.strip():
        return text
    
    text = text.strip()
    if len(text) > 500:
        text = text[:500]
    
    # Skip if already contains Chinese
    if re.search(r'[\u4e00-\u9fff]', text):
        return text
    
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {
            "q": text,
            "langpair": "en|zh"
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("responseStatus") == 200:
            return data.get("responseData", {}).get("translatedText", text)
        
        return text
    except Exception:
        return text


def translate_zh_to_en(text: str) -> str:
    """
    Translate Chinese text to English using argos-translate or MyMemory.
    """
    if not text or not text.strip():
        return text
    
    text = text.strip()
    
    # Check if already English (mostly Latin chars)
    latin_ratio = sum(1 for c in text if c.isascii()) / max(len(text), 1)
    if latin_ratio > 0.8:
        return text
    
    # Try argos-translate first
    try:
        import argostranslate.translate
        result = argostranslate.translate.translate(text, "zh", "en")
        if result and result != text:
            return result
    except:
        pass
    
    # Fallback to MyMemory
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {
            "q": text,
            "langpair": "zh|en"
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("responseStatus") == 200:
            return data.get("responseData", {}).get("translatedText", text)
        
        return text
    except Exception:
        return text