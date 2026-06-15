"""
火车票解析
"""
import re

from application.parsers.base import BaseParser


class TrainParser(BaseParser):
    """
    火车票结构化识别：车次、日期、站点、票价
    """
    def parse(self):
        self.train_number()
        self.date()
        self.stations()
        self.price()
        return self.res

    def train_number(self):
        """
        识别车次
        """
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res = re.findall('车次[:：]?([GDKCTZSYL]\d{1,4})', txt)
            res += re.findall('(?<![A-Z])([GDKCTZSYL]\d{1,4})(?!\d)', txt)
            if len(res) > 0:
                self.res['车次'] = res[0]
                break

    def date(self):
        """
        识别乘车日期
        """
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res = re.findall('(?:乘车|开车|发车)?日期[:：]?[0-9]{1,4}年[0-9]{1,2}月[0-9]{1,2}日', txt)
            res += re.findall('[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日', txt)
            res += re.findall('[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}', txt)
            if len(res) > 0:
                val = res[0]
                val = re.sub(r'^(?:乘车|开车|发车)?日期[:：]?', '', val)
                self.res['日期'] = val
                break

    def stations(self):
        """
        识别出发站 / 到达站
        """
        dep = None
        arr = None
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            if dep is None:
                res = re.findall('(?:出发|始发|发站)[:：]?(\S+?)(?:站|$)', txt)
                if len(res) > 0:
                    dep = res[0].replace('站', '')
            if arr is None:
                res = re.findall('(?:到达|目的|到站)[:：]?(\S+?)(?:站|$)', txt)
                if len(res) > 0:
                    arr = res[0].replace('站', '')
        if dep and arr:
            self.res['站点'] = dep + '-' + arr
        elif dep:
            self.res['站点'] = dep
        elif arr:
            self.res['站点'] = arr

    def price(self):
        """
        识别票价
        """
        N = len(self.lines)
        for i in range(N):
            txt = self.lines[i]['text'].replace(' ', '')
            res = re.findall('(?:票价|金额|合计)[^0-9￥¥]*[￥¥]?([0-9]{1,8}\.[0-9]{1,2})', txt)
            res += re.findall('[￥¥]([0-9]{1,8}\.[0-9]{1,2})', txt)
            if len(res) > 0:
                self.res['票价'] = res[0]
                break
