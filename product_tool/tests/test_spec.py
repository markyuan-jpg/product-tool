"""
规格解析测试
"""
import sys
sys.path.insert(0, r'C:\Users\marky\Desktop\production tool\product_tool')

from src.core import parse_spec


def test_voltage():
    result = parse_spec('电压: 220V')
    assert result.get('voltage') == 220.0


def test_power():
    result = parse_spec('功率: 1500W')
    assert result.get('power') == 1500.0


def test_dimensions():
    result = parse_spec('尺寸: 100x200x300mm')
    assert result.get('length') == 100.0
    assert result.get('width') == 200.0
    assert result.get('height') == 300.0


def test_all():
    test_voltage()
    test_power()
    test_dimensions()
    print('Spec tests: PASSED')


if __name__ == '__main__':
    test_all()