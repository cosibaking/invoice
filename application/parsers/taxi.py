"""
出租车票解析
"""
import re

from application.parsers.base import BaseParser


class TaxiParser(BaseParser):
    """
    出租车票结构化识别：车号、日期、金额、里程
    """
    def parse(self):
        self.plate_number()
        self.date()
        self.price()
        self.mileage()
        return self.res

    def plate_number(self):
        """
        识别车号（车牌）
        """
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res = re.findall('车号[:：]?([^\s]{5,10})', txt)
            res += re.findall('车牌[:：]?([^\s]{5,10})', txt)
            res += re.findall('[\u4e00-\u9fff][A-Z0-9]{5,6}', txt)
            if len(res) > 0:
                self.res['车号'] = res[0]
                break

    def date(self):
        """
        识别日期
        """
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res = re.findall('[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日', txt)
            res += re.findall('[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}', txt)
            res += re.findall('[0-9]{4}/[0-9]{1,2}/[0-9]{1,2}', txt)
            res += re.findall('[0-9]{4}\.[0-9]{1,2}\.[0-9]{1,2}', txt)
            if len(res) > 0:
                self.res['日期'] = res[0]
                break

    def price(self):
        """
        识别金额
        """
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res = re.findall('(?:金额|实收|合计)[^0-9￥¥]*[￥¥]?([0-9]{1,8}\.[0-9]{1,2})', txt)
            res += re.findall('[￥¥]([0-9]{1,8}\.[0-9]{1,2})', txt)
            if len(res) > 0:
                self.res['金额'] = res[0]
                break

    def mileage(self):
        """
        识别里程
        """
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res = re.findall('里程[:：]?([0-9]{1,6}\.[0-9]{1,2})', txt)
            res += re.findall('([0-9]{1,6}\.[0-9]{1,2})公里', txt)
            res += re.findall('([0-9]{1,6}\.[0-9]{1,2})km', txt, re.IGNORECASE)
            if len(res) > 0:
                self.res['里程'] = res[0]
                break
