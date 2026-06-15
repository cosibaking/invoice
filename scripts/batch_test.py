#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Batch regression: run OCR on fixture samples and compare with expected.json.

Usage:
    python scripts/batch_test.py --dir test/fixtures/vat_e
    python scripts/batch_test.py --dir test/fixtures/vat_e --url http://127.0.0.1:11111/invoice-ocr
"""
from __future__ import print_function

import argparse
import json
import os
import sys
import time

try:
    import requests
except ImportError:
    requests = None

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

SAMPLE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf'}
SKIP_FILES = {'expected.json'}
SKIP_PREFIXES = ('RedThresh_',)


def _load_json(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def _list_samples(fixture_dir):
    samples = []
    for name in sorted(os.listdir(fixture_dir)):
        if name in SKIP_FILES or name.startswith('.'):
            continue
        if name.startswith(SKIP_PREFIXES):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext in SAMPLE_EXTENSIONS:
            samples.append(name)
    return samples


def _resolve_expected(expected, filename):
    """Resolve per-file expected block from expected.json."""
    if not isinstance(expected, dict):
        return {}

    if filename in expected:
        block = expected[filename]
        return block if isinstance(block, dict) else {}

    samples = expected.get('samples')
    if isinstance(samples, dict) and filename in samples:
        block = samples[filename]
        return block if isinstance(block, dict) else {}

    if isinstance(samples, list):
        for item in samples:
            if isinstance(item, dict) and item.get('file') == filename:
                return item

    defaults = expected.get('defaults')
    if isinstance(defaults, dict):
        return defaults

    shared_keys = {'docType', 'docTypeName', 'code', 'fields', 'message'}
    if shared_keys.intersection(expected.keys()):
        return expected

    return {}


def _extract_result(payload):
    """Normalize API / pipeline payload to {code, docType, fields}."""
    if not isinstance(payload, dict):
        return {'code': None, 'docType': None, 'fields': {}}

    code = payload.get('code')
    data = payload.get('data')
    if not isinstance(data, dict):
        data = {}

    doc_type = data.get('docType')
    fields = data.get('fields')
    if fields is None:
        fields = {}
        for key, value in data.items():
            if key not in ('docType', 'docTypeName', 'rawLines', 'fields'):
                fields[key] = value
    if not isinstance(fields, dict):
        fields = {}

    return {
        'code': code,
        'docType': doc_type,
        'fields': fields,
    }


def _recognize_via_pipeline(path):
    try:
        from app import recognize_document  # noqa: WPS433
    except ImportError:
        return None

    try:
        result = recognize_document(path)
    except Exception as exc:
        return {'code': 105, 'message': str(exc), 'data': {}}
    if isinstance(result, dict):
        return result
    return {'code': 100, 'data': result}


def _recognize_via_http(path, url):
    if requests is None:
        raise RuntimeError('requests is required for HTTP mode')
    with open(path, 'rb') as fh:
        files = {'file': (os.path.basename(path), fh)}
        resp = requests.post(url, files=files, timeout=600)
    resp.raise_for_status()
    return resp.json()


def _compare_fields(actual, expected_fields):
    if not expected_fields:
        return True, []
    mismatches = []
    for key, expected_value in expected_fields.items():
        actual_value = actual.get(key)
        if str(actual_value) != str(expected_value):
            mismatches.append({
                'field': key,
                'expected': expected_value,
                'actual': actual_value,
            })
    return len(mismatches) == 0, mismatches


def _evaluate_sample(actual, expected_block):
    issues = []
    passed = True

    if 'code' in expected_block:
        if actual['code'] != expected_block['code']:
            passed = False
            issues.append(
                'code expected {0}, got {1}'.format(expected_block['code'], actual['code'])
            )

    if 'docType' in expected_block:
        if actual['docType'] != expected_block['docType']:
            passed = False
            issues.append(
                'docType expected {0}, got {1}'.format(
                    expected_block['docType'], actual['docType']
                )
            )

    fields_ok, field_mismatches = _compare_fields(
        actual['fields'],
        expected_block.get('fields') or {},
    )
    if not fields_ok:
        passed = False
        for item in field_mismatches:
            issues.append(
                'field {field}: expected {expected!r}, got {actual!r}'.format(**item)
            )

    return passed, issues


def run_batch(fixture_dir, url=None):
    expected_path = os.path.join(fixture_dir, 'expected.json')
    if not os.path.isdir(fixture_dir):
        raise SystemExit('Fixture directory not found: {0}'.format(fixture_dir))
    if not os.path.isfile(expected_path):
        raise SystemExit('Missing expected.json in {0}'.format(fixture_dir))

    expected = _load_json(expected_path)
    samples = _list_samples(fixture_dir)
    if not samples:
        raise SystemExit('No sample files found in {0}'.format(fixture_dir))

    url = url or os.environ.get(
        'INVOICE_OCR_URL',
        'http://127.0.0.1:11111/invoice-ocr',
    )

    results = []
    passed_count = 0
    total_elapsed = 0.0
    code_counts = {}

    print('Fixture dir: {0}'.format(fixture_dir))
    print('Samples: {0}'.format(len(samples)))
    print('-' * 60)

    for filename in samples:
        sample_path = os.path.join(fixture_dir, filename)
        expected_block = _resolve_expected(expected, filename)
        started = time.time()

        payload = _recognize_via_pipeline(sample_path)
        if payload is None:
            payload = _recognize_via_http(sample_path, url)

        elapsed = time.time() - started
        total_elapsed += elapsed
        actual = _extract_result(payload)
        code = actual['code']
        code_counts[code] = code_counts.get(code, 0) + 1

        passed, issues = _evaluate_sample(actual, expected_block)
        if passed:
            passed_count += 1
            status = 'PASS'
        else:
            status = 'FAIL'

        print('[{0}] {1} ({2:.2f}s) code={3}'.format(
            status, filename, elapsed, code
        ))
        for issue in issues:
            print('       - {0}'.format(issue))

        results.append({
            'file': filename,
            'passed': passed,
            'elapsed': elapsed,
            'actual': actual,
            'issues': issues,
        })

    total = len(samples)
    match_rate = (float(passed_count) / total * 100.0) if total else 0.0
    avg_elapsed = (total_elapsed / total) if total else 0.0

    print('-' * 60)
    print('Passed: {0}/{1} ({2:.1f}%)'.format(passed_count, total, match_rate))
    print('Average time: {0:.2f}s'.format(avg_elapsed))
    print('Code distribution: {0}'.format(code_counts))

    return 0 if passed_count == total else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description='Batch OCR regression against expected.json')
    parser.add_argument(
        '--dir',
        dest='fixture_dir',
        required=True,
        help='Fixture directory, e.g. test/fixtures/vat_e',
    )
    parser.add_argument(
        '--url',
        default=None,
        help='Invoice OCR HTTP endpoint (default: http://127.0.0.1:11111/invoice-ocr)',
    )
    args = parser.parse_args(argv)

    fixture_dir = args.fixture_dir
    if not os.path.isabs(fixture_dir):
        fixture_dir = os.path.join(_PROJECT_ROOT, fixture_dir)

    return run_batch(fixture_dir, url=args.url)


if __name__ == '__main__':
    sys.exit(main())
