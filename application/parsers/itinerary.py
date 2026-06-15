"""
电子行程单解析
"""
import re

from application.parsers.base import BaseParser


class ItineraryParser(BaseParser):
    """
    电子行程单结构化识别：旅客姓名、航班号、客票号、金额
    """
    def parse(self):
        self.passenger_name()
        self.flight_number()
        self.ticket_number()
        self.price()
        return self.res

    def passenger_name(self):
        """
        识别旅客姓名
        """
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text']
            res = re.findall('旅客姓名[:：]\s*(\S+)', txt)
            if len(res) > 0:
                self.res['旅客姓名'] = res[0]
                break

    def flight_number(self):
        """
        识别航班号
        """
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res = re.findall('[A-Z]{2}\d{3,4}', txt)
            if len(res) > 0:
                self.res['航班号'] = res[0]
                break

    def ticket_number(self):
        """
        识别客票号
        """
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res = re.findall('客票号[:：]?\s*(\d{13,15})', txt)
            if len(res) > 0:
                self.res['客票号'] = res[0]
                break
            res = re.findall('(?:(?<!\d)\d{13,15}(?!\d))', txt)
            if len(res) > 0:
                self.res['客票号'] = res[0]
                break

    def price(self):
        """
        识别金额
        """
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res = re.findall('(?:合计|票价|金额)[^0-9￥¥]*[￥¥]?([0-9]{1,8}\.[0-9]{1,2})', txt)
            res += re.findall('[￥¥]([0-9]{1,8}\.[0-9]{1,2})', txt)
            if len(res) > 0:
                self.res['金额'] = res[0]
                break
