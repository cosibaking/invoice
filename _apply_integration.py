import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent
path = root / "application" / "doc_router.py"
content = path.read_text(encoding="utf-8")

extra_kws = ["\u5168\u9762\u6570\u5b57", "\u7535\u5b50\u53d1\u7968"]
m = re.search(r"\('digital_vat', \[([^\]]+)\]\)", content)
if not m:
    raise SystemExit("digital_vat route not found")
inner = m.group(1)
for kw in extra_kws:
    if kw not in inner:
        inner = inner.rstrip() + ", %r" % (kw,)
content = content[: m.start(1)] + inner + content[m.end(1) :]

if "_detect_digital_vat_by_pattern" not in content:
    fn = """

def _detect_digital_vat_by_pattern(ocr_lines):
    combined = ''.join(_normalize_text(line.get('text', '')) for line in ocr_lines)
    if re.search(r'\\d{20}', combined):
        return 'digital_vat'
    if re.search(r'\u53f7\u7801[:\\uFF1A]\\d{12,20}', combined):
        return 'digital_vat'
    return None
"""
    content = content.replace(
        "\ndef route_by_keywords(ocr_lines):",
        fn + "\ndef route_by_keywords(ocr_lines):",
        1,
    )
    old_tail = "                    return doc_type\n    return None"
    new_tail = (
        "                    return doc_type\n"
        "    doc_type = _detect_digital_vat_by_pattern(ocr_lines)\n"
        "    if doc_type:\n"
        "        return doc_type\n"
        "    return None"
    )
    if old_tail not in content:
        raise SystemExit("route_by_keywords tail not found")
    content = content.replace(old_tail, new_tail, 1)

path.write_text(content, encoding="utf-8")
print("doc_router.py updated")

expected = {
    "samples": {
        "sample.jpg": {"code": 104, "docType": "vat_m", "fields": {}}
    }
}
(root / "test" / "fixtures" / "unknown" / "expected.json").write_text(
    json.dumps(expected, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print("expected.json updated")

doc_path = root / "docs" / "\u6280\u672f\u6587\u6863.md"
text = doc_path.read_text(encoding="utf-8")
insertions = [
    ("| `config.py` |", "| `model_post.py` | \u7edf\u4e00\u8bc6\u522b\u7f16\u6392\u5165\u53e3 |"),
    ("| `model_post_type.py` |", "| `application/doc_router.py` | \u7968\u79cd\u5173\u952e\u8bcd\u4e0e\u6a21\u5f0f\u8def\u7531 |"),
    ("| `application/doc_router.py` |", "| `application/parsers/*` | \u5404\u7968\u79cd\u7ed3\u6784\u5316\u89e3\u6790\u5668 |"),
    ("| `application/parsers/*` |", "| `application/config_loader.py` | YAML \u914d\u7f6e\u52a0\u8f7d |"),
    ("| `application/config_loader.py` |", "| `application/llm_fallback.py` | LLM \u515c\u5e95\u89e3\u6790 |"),
    ("| `application/invoice_m.py` |", "| `config/settings.yaml` | \u9ed8\u8ba4\u53ef\u8fd0\u884c\u914d\u7f6e |"),
    ("| `config/settings.yaml` |", "| `scripts/batch_test.py` | fixtures \u6279\u91cf\u56de\u5f52 |"),
]
for anchor, row in insertions:
    if row not in text:
        idx = text.find(anchor)
        if idx == -1:
            raise SystemExit("anchor not found: " + anchor)
        line_end = text.find("\n", idx)
        text = text[: line_end + 1] + row + "\n" + text[line_end + 1 :]
doc_path.write_text(text, encoding="utf-8")
print("docs updated")
