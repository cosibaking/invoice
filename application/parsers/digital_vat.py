"""
数电票（全面数字化电子发票）解析
"""
import re

from application.parsers.base import BaseParser


class DigitalVatParser(BaseParser):
    """
    数电票结构化识别：发票号码（20位）、开票日期、价税合计
    """
    def parse(self):
        self.number()
        self.date()
        self.price()
        return self.res

    def number(self):
        """
        识别20位发票号码
        """
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res = re.findall('号码[:：]?\s*(\d{20})', txt)
            res += re.findall('发票号码[:：]?\s*(\d{20})', txt)
            res += re.findall('(?:(?<!\d)\d{20}(?!\d))', txt)
            if len(res) > 0:
                self.res['发票号码'] = res[0]
                break

    def date(self):
        """
        识别开票日期
        """
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res = re.findall('开票日期[:：]?[0-9]{1,4}年[0-9]{1,2}月[0-9]{1,2}日', txt)
            res += re.findall('日期[:：]?[0-9]{1,4}年[0-9]{1,2}月[0-9]{1,2}日', txt)
            res += re.findall('日期[:：]?[0-9]{8}', txt)
            res += re.findall('[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日', txt)
            if len(res) > 0:
                val = res[0]
                val = val.replace('开票日期:', '').replace('开票日期：', '').replace('开票日期', '')
                val = val.replace('日期:', '').replace('日期：', '').replace('日期', '')
                self.res['开票日期'] = val
                break

    def price(self):
        """
        识别价税合计 / 金额
        """
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res = re.findall('价税合计[^0-9￥¥]*[￥¥]?([0-9]{1,8}\.[0-9]{1,2})', txt)
            res += re.findall('(?:小写|合计|金额)[^0-9￥¥]*[￥¥]?([0-9]{1,8}\.[0-9]{1,2})', txt)
            res += re.findall('[￥¥]([0-9]{1,8}\.[0-9]{1,2})', txt)
            if len(res) > 0:
                self.res['价税合计'] = res[0]
                break
