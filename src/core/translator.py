"""
Product translator using Argos Translate for Chinese to English translation.

Requires: argostranslate package and Chinese->English language pack.
"""
import pandas as pd


class ProductTranslator:
    """Translate product data from Chinese to English"""
    
    def __init__(self):
        """Initialize translator."""
        self._offline = False
        self._cache = {}
        self.available = False
        
        try:
            import argostranslate.package
            import argostranslate.translate
        except ImportError:
            print("[ProductTranslator] ERROR: argostranslate not installed")
            print("  Run: pip install argostranslate")
            self._offline = True
            return
        
        # Check if zh->en package is installed
        try:
            installed = argostranslate.package.get_installed_packages()
            for pkg in installed:
                if pkg.from_code == "zh" and pkg.to_code == "en":
                    self.available = True
                    print("[ProductTranslator] Ready: Chinese -> English")
                    break
            
            if not self.available:
                print("[ProductTranslator] WARNING: zh->en language pack not installed")
                print("  Run: python download_translate_package.py")
                self._offline = True
        except Exception as e:
            print(f"[ProductTranslator] ERROR: {e}")
            self._offline = True

    def translate_text(self, text: str) -> str:
        """Translate a single text from Chinese to English."""
        if not text or pd.isna(text):
            return text
        
        text_str = str(text).strip()
        if not text_str:
            return text
        
        # Check if already English
        if self._is_english(text_str):
            return text_str
        
        # Check cache
        if text_str in self._cache:
            return self._cache[text_str]
        
        if not self.available:
            return text_str
        
        try:
            import argostranslate.translate
            result = argostranslate.translate.translate(text_str, "zh", "en")
            self._cache[text_str] = result
            return result
        except Exception:
            return text_str

    def _is_english(self, text: str) -> bool:
        """Check if text is mostly English."""
        if not text:
            return False
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        total_chars = len(text.replace(" ", ""))
        if total_chars == 0:
            return True
        return chinese_chars / total_chars < 0.2

    def _translate_spec_dict(self, spec_dict) -> dict:
        """
        Translate spec_dict - only translate keys to English, discard Chinese keys.
        
        FIX: Only keep translated English keys, discard Chinese keys.
        
        Returns:
            Translated dictionary with English keys only
        """
        if not spec_dict or pd.isna(spec_dict):
            return {} if isinstance(spec_dict, dict) else {}
        
        if isinstance(spec_dict, str):
            return {}
        
        if not isinstance(spec_dict, dict):
            return {}
        
        # Translate only keys to English, keep values unchanged
        # Build NEW dict with only translated English keys
        translated = {}
        for key, value in spec_dict.items():
            key_en = self.translate_text(str(key))
            # Only add if key was successfully translated to English
            if key_en and key_en != str(key):
                translated[key_en] = str(value)
            # Skip Chinese keys (discard them)
        
        return translated

    def _dict_to_string(self, spec_dict) -> str:
        """
        Convert spec_dict to formatted string.
        
        FIX: Use single colon format: "Length: 1720; Width: 690"
        """
        if not spec_dict or pd.isna(spec_dict):
            return ""
        
        if isinstance(spec_dict, str):
            return spec_dict
        
        if not isinstance(spec_dict, dict) or not spec_dict:
            return ""
        
        # Use single colon format: "Length: 1720; Width: 690"
        return "; ".join(f"{k}: {v}" for k, v in spec_dict.items())

    def translate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Translate DataFrame columns from Chinese to English."""
        if df is None or df.empty:
            return df
        
        if not self.available:
            print("[ProductTranslator] Translation not available. Skipping.")
            return df
        
        result = df.copy()

        # Translate name_zh -> name_en
        if "name_zh" in df.columns:
            print("Translating name_zh...")
            result["name_en"] = df["name_zh"].apply(self.translate_text)

        # Translate spec_zh -> spec_en (string)
        if "spec_zh" in df.columns:
            print("Translating spec_zh...")
            result["spec_en"] = df["spec_zh"].apply(self.translate_text)
        
        # Translate spec_dict -> spec_dict_en (translate keys only)
        if "spec_dict" in df.columns:
            print("Translating spec_dict (keys only)...")
            result["spec_dict_en"] = df["spec_dict"].apply(self._translate_spec_dict)
            # Generate spec_en from spec_dict_en with single colon format
            result["spec_en"] = result["spec_dict_en"].apply(self._dict_to_string)

        return result


# ==================== MAIN ====================

if __name__ == "__main__":
    import sys
    sys.path.append(".")
    from src.core.parser import load_excel_files
    
    print("Loading data...")
    df = load_excel_files("./data")
    print(f"Loaded {len(df)} products")
    
    print("\nInitializing translator...")
    translator = ProductTranslator()
    
    print("\nTranslating...")
    df_translated = translator.translate_dataframe(df)
    
    print("\nResults (first 3):")
    for i in range(min(3, len(df_translated))):
        row = df_translated.iloc[i]
        print(f"\n{i+1}. {row.get('name_zh', 'N/A')}")
        if translator.available:
            print(f"   -> {row.get('name_en', 'N/A')}")
            sd = row.get('spec_dict', {})
            sd_en = row.get('spec_dict_en', {})
            if sd and sd_en:
                print(f"   Spec keys: {list(sd_en.keys())[:3]}")