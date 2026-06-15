# -*- coding: utf-8 -*-
from model_post import ocr as _ocr


def ocr(img):
    return _ocr(img, detector='electronic')
