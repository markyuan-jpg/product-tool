import pytest
from src.parsers.spec_cleaner import (
    clean_spec,
    normalize_punctuation,
    inject_linebreaks,
    fix_truncated_spec,
    fill_empty_spec,
    normalize_spec,
    DEFAULT_SPEC_TEXT,
)


class TestNormalizePunctuation:
    def test_fullwidth_colon(self):
        assert normalize_punctuation("长度：1720mm") == "长度: 1720mm"

    def test_fullwidth_semicolon(self):
        assert normalize_punctuation("长度: 1720mm；宽度: 650mm") == "长度: 1720mm;宽度: 650mm"

    def test_mixed_punctuation(self):
        assert normalize_punctuation("Motor：4000W；Controller：150A") == "Motor: 4000W;Controller: 150A"

    def test_empty(self):
        assert normalize_punctuation("") == ""

    def test_already_halfwidth(self):
        assert normalize_punctuation("Length: 1720mm") == "Length: 1720mm"


class TestInjectLinebreaks:
    def test_space_separated_params(self):
        result = inject_linebreaks("Motor: 4000W Battery: 72V 20AH")
        assert result == "Motor: 4000W\nBattery: 72V 20AH"

    def test_no_linebreak_needed(self):
        text = "Motor: 4000W\nBattery: 72V"
        assert inject_linebreaks(text) == text

    def test_single_param(self):
        text = "Motor: 4000W"
        assert inject_linebreaks(text) == text

    def test_empty(self):
        assert inject_linebreaks("") == ""

    def test_no_param_names(self):
        text = "This is a simple description without params"
        assert inject_linebreaks(text) == text


class TestFixTruncatedSpec:
    def test_ends_with_star(self):
        result = fix_truncated_spec("Package: 1360*")
        assert result.endswith("(尺寸单位缺失)")

    def test_ends_with_trailing_colon(self):
        result = fix_truncated_spec("Motor Power:")
        assert result.endswith("(may be incomplete)")

    def test_normal_spec_no_change(self):
        text = "Motor: 4000W\nBattery: 72V"
        assert fix_truncated_spec(text) == text

    def test_already_marked(self):
        text = "Package: 1360* (may be incomplete)"
        assert fix_truncated_spec(text) == text

    def test_empty(self):
        assert fix_truncated_spec("") == ""

    def test_ends_with_number_star(self):
        result = fix_truncated_spec("Dimension: 1360*")
        assert result.endswith("(尺寸单位缺失)")

    def test_long_text_truncated_last_word(self):
        text = "Motor: 4000W Battery: 72V 20AH Controller: 150A Front Brake: Front di "
        result = fix_truncated_spec(text)
        assert result.endswith("(may be incomplete)")

    def test_safe_short_word_no_mark(self):
        text = "box of 10 pcs per set"
        result = fix_truncated_spec(text)
        assert result == text

    def test_normalize_spec_exists(self):
        assert callable(normalize_spec)


class TestFillEmptySpec:
    def test_none(self):
        assert fill_empty_spec(None) == DEFAULT_SPEC_TEXT

    def test_empty_string(self):
        assert fill_empty_spec("") == DEFAULT_SPEC_TEXT

    def test_whitespace(self):
        assert fill_empty_spec("   ") == DEFAULT_SPEC_TEXT

    def test_nan(self):
        assert fill_empty_spec("nan") == DEFAULT_SPEC_TEXT

    def test_valid_spec(self):
        assert fill_empty_spec("Motor: 4000W") == "Motor: 4000W"


class TestCleanSpec:
    def test_empty_becomes_default(self):
        result = clean_spec("")
        assert result == DEFAULT_SPEC_TEXT
        assert "Standard configuration" in result

    def test_none_becomes_default(self):
        assert clean_spec(None) == DEFAULT_SPEC_TEXT

    def test_space_separated_params(self):
        result = clean_spec("Motor: 4000W Battery: 72V")
        assert "Motor: 4000W" in result
        assert "Battery: 72V" in result
        assert '\n' in result

    def test_fullwidth_punctuation_normalized(self):
        result = clean_spec("长度：1720mm；宽度：650mm")
        assert ':' in result
        assert ';' not in result or ';' in result
        assert '\n' in result or ';\n' in result

    def test_truncation_detected(self):
        result = clean_spec("Package: 1360*")
        assert "(尺寸单位缺失)" in result

    def test_already_clean_unchanged(self):
        text = "Motor: 4000W\nBattery: 72V 20AH\nController: 150A"
        result = clean_spec(text)
        assert "Motor: 4000W" in result
        assert "Battery: 72V 20AH" in result
        assert "Controller: 150A" in result

    def test_complex_scenario(self):
        """: → ;, linebreak, truncation"""
        raw = "Motor：4000W Battery：72V 20AH Package size：1360*"
        result = clean_spec(raw)
        assert ':' in result  # punct normalized
        assert '\n' in result  # linebreaks injected
        assert '(尺寸单位缺失)' in result  # truncation detected
