"""
增值税电子普通发票解析
"""
from apphelper.image import union_rbox
import re

from application.parsers.base import BaseParser, normalize_digits


class VatEParser(BaseParser):
    """
    增值税电子发票结构化识别
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
            res = re.findall(r'代码[:：]?\s*(\d+)', txt_norm)
            res += re.findall(r'代码\s*(\d+)', txt_norm)
            if len(res) > 0:
                No['发票代码'] = res[0]
                self.res.update(No)
                break
            if re.search(r'代码', txt) and i + 1 < N:
                next_txt = normalize_digits(
                    self.lines[i + 1]['text'].replace(' ', '')
                )
                m = re.search(r'(?:(?<!\d)\d{10,12}(?!\d))', next_txt)
                if m:
                    No['发票代码'] = m.group(0)
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
            res = re.findall(r'号码[:：]?\s*(\d+)', txt_norm)
            res += re.findall(r'号码\s*(\d+)', txt_norm)
            if len(res) > 0:
                nu["发票号码"] = res[0]
                self.res.update(nu)
                break
            if re.search(r'号码', txt) and i + 1 < N:
                next_txt = normalize_digits(
                    self.lines[i + 1]['text'].replace(' ', '')
                )
                m = re.search(r'(?:(?<!\d)\d{8}(?!\d))', next_txt)
                if m:
                    nu["发票号码"] = m.group(0)
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
            res = re.findall(
                r'日期[:：]?\s*[0-9]{1,4}年[0-9]{1,2}月[0-9]{1,2}日', txt
            )
            res += re.findall(r'日期[:：]?\s*[0-9]{8}', txt)
            res += re.findall(
                r'日期\s*[0-9]{1,4}年[0-9]{1,2}月[0-9]{1,2}日', txt
            )
            res += re.findall(r'日期\s*[0-9]{8}', txt)
            if len(res) > 0:
                val = res[0]
                val = val.replace('日期:', '').replace('日期：', '').replace('日期', '')
                da["开票日期"] = val
                self.res.update(da)
                break

    def price(self):
        """
        识别税后金额（小写）
        """
        pri = {}
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res5 = re.findall(r'[￥¥]([0-9]{1,8}\.[0-9]{1,2})', txt)
            if len(res5) > 0:
                pri["税后金额"] = res5[0]
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
            res = re.findall(r'校验码[:：]?\s*([0-9]{1,20})', txt_norm)
            res += re.findall(r'校验码\s*([0-9]{1,20})', txt_norm)
            if len(res) > 0:
                check['校验码'] = res[0]
                self.res.update(check)
                break
            if re.search(r'校验码', txt) and i + 1 < N:
                next_txt = normalize_digits(
                    self.lines[i + 1]['text'].replace(' ', '')
                )
                m = re.search(r'(?:(?<!\d)\d{1,20}(?!\d))', next_txt)
                if m:
                    check['校验码'] = m.group(0)
                    self.res.update(check)
                    break
