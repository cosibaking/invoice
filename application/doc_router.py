# -*- coding: utf-8 -*-
import re

from apphelper.image import union_rbox

KEYWORD_ROUTES = [
    ('digital_vat', ['数电', '电子发票（', '全面数字']),
    ('itinerary', ['电子行程单', '行程单', 'ITINERARY']),
    ('train', ['铁路电子客票', '火车票']),
    ('taxi', ['出租车', '出租汽车']),
]


def _normalize_text(txt):
    return txt.replace(' ', '')



def _detect_digital_vat_by_pattern(ocr_lines):
    combined = ''.join(_normalize_text(line.get('text', '')) for line in ocr_lines)
    if re.search(r'\d{20}', combined):
        return 'digital_vat'
    if re.search(r'号码[:\uFF1A]\d{12,20}', combined):
        return 'digital_vat'
    return None

def route_by_keywords(ocr_lines):
    """
    在原图 OCR 结果上按关键词路由新票种。
    返回 docType 或 None。
    """
    if not ocr_lines:
        return None
    for line in ocr_lines:
        txt = _normalize_text(line.get('text', ''))
        for doc_type, keywords in KEYWORD_ROUTES:
            for kw in keywords:
                if re.findall(re.escape(kw), txt):
                    return doc_type
    doc_type = _detect_digital_vat_by_pattern(ocr_lines)
    if doc_type:
        return doc_type
    return None


def legacy_vat_type(redthresh_ocr_lines):
    """
    保留 Recognition_invoice 逻辑：在去红章 RedThresh 图 OCR 结果上区分 vat_e / vat_m。
    """
    result_type = union_rbox(redthresh_ocr_lines, 0.2)
    if len(result_type) > 0:
        type_1 = []
        type_2 = []
        type_3 = []
        for i in range(len(result_type)):
            txt = result_type[i]['text'].replace(' ', '')
            type_1 = re.findall('电子普通', txt)
            type_2 = re.findall('普通发票', txt)
            type_3 = re.findall('专用发票', txt)
        if len(type_1) > 0:
            return 'vat_e'
        else:
            return 'vat_m'
    elif len(result_type) == 0:
        return 'vat_m'


def route(original_lines, redthresh_lines=None):
    """
    组合路由：先原图关键词匹配新票种，再走 legacy 增值税分支，否则 unknown。
    """
    doc_type = route_by_keywords(original_lines)
    if doc_type:
        return doc_type
    if redthresh_lines is not None:
        return legacy_vat_type(redthresh_lines)
    return 'unknown'
