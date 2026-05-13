"""
价格处理单元测试
"""
import sys
sys.path.insert(0, r'C:\Users\marky\Desktop\production tool\product_tool')

from src.utils.price import clean_price_value


def test_basic_price():
    assert clean_price_value('123') == 123.0
    assert clean_price_value(123) == 123.0
    assert clean_price_value(123.5) == 123.5


def test_currency():
    assert clean_price_value('¥123') == 123.0
    assert clean_price_value('$100') == 100.0


def test_range():
    assert clean_price_value('100-200') == 150.0
    assert clean_price_value('100~200') == 150.0


def test_formula():
    # 简单加法应该工作
    assert clean_price_value('=100+50') == 150.0


def test_none():
    assert clean_price_value(None) is None
    assert clean_price_value('') is None


def test_all():
    test_basic_price()
    test_currency()
    test_range()
    test_formula()
    test_none()
    print('Price tests: PASSED')


if __name__ == '__main__':
    test_all()