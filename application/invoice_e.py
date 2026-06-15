"""
增值税电子发票识别
"""
from application.parsers.vat_e import VatEParser


class invoice_e:
    """
    增值税电子发票结构化识别
    """
    def __init__(self, result):
        parser = VatEParser(result)
        self.res = parser.parse()
