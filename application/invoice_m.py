"""
增值税机打发票识别
"""
from application.parsers.vat_m import VatMParser


class invoice_m:
    """
    增值税机打发票结构化识别
    """
    def __init__(self, result):
        parser = VatMParser(result)
        self.res = parser.parse()
