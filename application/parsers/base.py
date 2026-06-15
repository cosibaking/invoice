"""
解析器基类
"""


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
