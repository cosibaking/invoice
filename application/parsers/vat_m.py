"""
增值税机打发票解析
"""
from apphelper.image import union_rbox
import re

from application.parsers.base import BaseParser, normalize_digits


class VatMParser(BaseParser):
    """
    增值税机打发票结构化识别
    """
    def __init__(self, ocr_lines):
        self.lines = union_rbox(ocr_lines, 0.2)
        self.res = {}

    def parse(self):
        self.code()
        self.number()
        self.date()
        self.price()
        self.check_code()
        return self.res

    def code(self):
        """
        发票代码识别
        """
        No = {}
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            txt_norm = normalize_digits(txt)
            res1 = re.findall(r'(?:(?<!\d)\d{10}(?!\d))', txt_norm)
            res1 += re.findall(r'(?:(?<!\d)\d{12}(?!\d))', txt_norm)
            if len(res1) > 0:
                No['发票代码'] = res1[0]
                self.res.update(No)
                break

    def number(self):
        """
        识别发票号码
        """
        nu = {}
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            txt_norm = normalize_digits(txt)
            res1 = re.findall(r'(?:(?<!\d)\d{8}(?!\d))', txt_norm)
            if len(res1) > 0:
                nu["发票号码"] = res1[0]
                self.res.update(nu)
                break

    def date(self):
        """
        识别开票日期
        """
        da = {}
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res1 = re.findall(
                r'日期[:：]?[0-9]{1,4}年[0-9]{1,2}月[0-9]{1,2}日', txt
            )
            res1 += re.findall(r'日期[:：]?[0-9]{8}', txt)
            res1 += re.findall(r'[0-9]{1,4}年[0-9]{1,2}月[0-9]{1,2}日', txt)
            if len(res1) > 0:
                val = res1[0]
                val = val.replace('日期:', '').replace('日期：', '').replace('日期', '')
                da["开票日期"] = val
                self.res.update(da)
                break

    def price(self):
        """
        识别税后价格（小写）
        """
        pri = {}
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res1 = re.findall(r'[￥¥]([0-9]{1,8}\.[0-9]{1,2})', txt)
            if len(res1) > 0:
                pri["税后价格"] = res1[0]
                self.res.update(pri)
                break

    def check_code(self):
        """
        校验码识别
        """
        check = {}
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            txt_norm = normalize_digits(txt)
            res = re.findall(r'校验码[:：]?([0-9]{1,20})', txt_norm)
            res += re.findall(r'校验码\s*([0-9]{1,20})', txt_norm)
            res += re.findall(r'码([0-9]{1,20})', txt_norm)
            if len(res) > 0:
                check['校验码'] = res[0]
                self.res.update(check)
                break
