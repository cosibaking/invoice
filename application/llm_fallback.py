"""
Optional LLM fallback: structure OCR lines via OpenAI-compatible chat API.
"""
import json
import re

import requests

_DOC_TYPE_HINTS = {
    'vat_e': '增值税电子普通发票',
    'vat_m': '增值税机打发票',
    'digital_vat': '数电票（电子发票）',
    'itinerary': '电子行程单',
    'train': '铁路电子客票',
    'taxi': '出租车发票',
}


def _cfg_value(cfg, key, default=None):
    if isinstance(cfg, dict):
        return cfg.get(key, default)
    return getattr(cfg, key, default)


def _ocr_lines_to_text(ocr_lines):
    parts = []
    for line in ocr_lines or []:
        if isinstance(line, dict):
            text = line.get('text', '')
        else:
            text = str(line)
        text = (text or '').strip()
        if text:
            parts.append(text)
    return '\n'.join(parts)


def _build_messages(doc_type, ocr_text):
    doc_name = _DOC_TYPE_HINTS.get(doc_type, doc_type)
    system = (
        '你是票据 OCR 结构化助手。根据 OCR 文本提取字段，'
        '仅返回 JSON 对象，键为字段名、值为字符串，无法确定的字段省略。'
    )
    user = '票种：{doc_name}（{doc_type}）\n\nOCR 文本：\n{ocr_text}'.format(
        doc_name=doc_name,
        doc_type=doc_type,
        ocr_text=ocr_text,
    )
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]


def _parse_json_content(content):
    if not content:
        return {}
    content = content.strip()
    try:
        data = json.loads(content)
        return data if isinstance(data, dict) else {}
    except (TypeError, ValueError):
        pass
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            return data if isinstance(data, dict) else {}
        except (TypeError, ValueError):
            pass
    return {}


def _call_api(doc_type, ocr_text, cfg):
    api_url = _cfg_value(cfg, 'api_url', '')
    if not api_url:
        return {}

    headers = {'Content-Type': 'application/json'}
    api_key = _cfg_value(cfg, 'api_key', '')
    if api_key:
        headers['Authorization'] = 'Bearer {0}'.format(api_key)

    payload = {
        'model': _cfg_value(cfg, 'model', 'gpt-4o-mini'),
        'messages': _build_messages(doc_type, ocr_text),
        'temperature': 0,
    }

    timeout = _cfg_value(cfg, 'timeout_seconds', 30)
    max_retries = max(0, int(_cfg_value(cfg, 'max_retries', 1) or 0))
    attempts = max_retries + 1

    for _ in range(attempts):
        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
            resp.raise_for_status()
            body = resp.json()
            choices = body.get('choices') or []
            if not choices:
                continue
            message = choices[0].get('message') or {}
            content = message.get('content', '')
            fields = _parse_json_content(content)
            if fields:
                return {k: str(v) for k, v in fields.items() if v is not None and str(v).strip()}
        except (requests.RequestException, ValueError, TypeError, KeyError):
            continue
    return {}


def fallback(doc_type, ocr_lines, cfg):
    """
    Call LLM to extract fields from OCR lines when enabled in cfg.
    Returns {} when disabled, on failure, or when OCR text is empty.
    """
    if not _cfg_value(cfg, 'enabled', False):
        return {}

    ocr_text = _ocr_lines_to_text(ocr_lines)
    if not ocr_text:
        return {}

    return _call_api(doc_type, ocr_text, cfg)
