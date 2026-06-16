"""
解析器基类
"""

_DIGIT_OCR_MAP = (
    ('O', '0'), ('o', '0'),
    ('l', '1'), ('I', '1'), ('i', '1'),
    ('S', '5'), ('s', '5'),
    ('B', '8'), ('b', '8'),
)


def normalize_digits(text):
    """
    数字字段 OCR 纠错：将常见误识字符映射为数字，仅用于数字提取上下文。
    """
    for old, new in _DIGIT_OCR_MAP:
        text = text.replace(old, new)
    return text


class BaseParser:
    def __init__(self, ocr_lines):
        """
        ocr_lines: [{'text': str, 'cx': float, 'cy': float, ...}, ...]
        """
        self.lines = ocr_lines
        self.res = {}

    def parse(self):
        """返回 fields 字典"""
        raise NotImplementedError
