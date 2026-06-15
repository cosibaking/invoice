"""
增值税电子普通发票解析
"""
from apphelper.image import union_rbox
import re

from application.parsers.base import BaseParser


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
            txt = txt.replace(' ', '')
            res = re.findall('代码:\d*', txt)
            res += re.findall('代码\d*', txt)
            if len(res) > 0:
                No['发票代码'] = res[0].replace('代码:', '').replace('代码','')
                self.res.update(No)
                break

    def number(self):
        """
        识别发票号码
        """
        nu = {}
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ','')
            txt = txt.replace(' ','')
            res = re.findall('号码:\d*',txt)
            res += re.findall('号码\d*',txt)
            if len(res) > 0:
                nu["发票号码"] = res[0].replace('号码:','').replace('号码','')
                self.res.update(nu)
                break

    def date(self):
        """
        识别开票日期
        """
        da = {}
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ','')
            txt = txt.replace(' ','')
            res = re.findall('日期:[0-9]{1,4}年[0-9]{1,2}月[0-9]{1,2}日',txt)
            res += re.findall('日期:[0-9]{8}', txt)
            res += re.findall('日期[0-9]{1,4}年[0-9]{1,2}月[0-9]{1,2}日',txt)
            res += re.findall('日期[0-9]{8}', txt)
            if len(res) > 0:
                da["开票日期"] = res[0].replace('日期:','').replace('日期','')
                self.res.update(da)
                break

    def price(self):
        """
        识别税后金额（小写）
        """
        pri = {}
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ','')
            txt = txt.replace(' ','')
            res5 = re.findall('￥[0-9]{1,8}.[0-9]{1,2}',txt)
            if len(res5) > 0:
                pri["税后金额"] = res5[0].replace('￥','')
                self.res.update(pri)
                break

    def check_code(self):
        """
        校验码识别
        """
        check = {}
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ','')
            txt = txt.replace(' ','')
            res = re.findall('校验码:[0-9]{1,20}',txt)
            res += re.findall('校验码[0-9]{1,20}', txt)
            if len(res) > 0:
                check['校验码'] = res[0].replace('校验码:','').replace('校验码','')
                self.res.update(check)
                break
