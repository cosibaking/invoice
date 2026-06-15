from flask import Flask, jsonify, request, render_template, make_response
from flask_cors import CORS
import time
import os
import sys
import cv2
import uuid
import numpy as np
from datetime import datetime
import pytz

from model_post import ocr
from config import DOC_TYPES
from application.doc_router import route
from application.parsers import get_parser
from application.config_loader import get_settings
from application.llm_fallback import fallback

port = 11111
allowed_extension = ['jpg', 'png', 'jpeg', 'JPG', 'pdf']
UPLOAD_PATH = 'test'


def _find_poppler_path():
    """查找 poppler 可执行文件目录（Windows 需单独安装或 conda install poppler）。"""
    env_path = os.environ.get('POPPLER_PATH', '').strip()
    if env_path and os.path.isdir(env_path):
        return env_path
    candidates = []
    conda_prefix = os.environ.get('CONDA_PREFIX')
    if conda_prefix:
        candidates.append(os.path.join(conda_prefix, 'Library', 'bin'))
    python_prefix = os.path.dirname(sys.executable)
    candidates.append(os.path.join(python_prefix, 'Library', 'bin'))
    candidates.append(os.path.join(python_prefix, 'Scripts'))
    for folder in candidates:
        if os.path.isfile(os.path.join(folder, 'pdftoppm.exe')):
            return folder
    return None


def pdf_to_jpg(pdf_path, jpg_path, dpi=200):
    """将 PDF 第一页转为 JPG，供 OCR 识别使用。"""
    from pdf2image import convert_from_path
    poppler_path = _find_poppler_path()
    kwargs = {'first_page': 1, 'last_page': 1, 'dpi': dpi}
    if poppler_path:
        kwargs['poppler_path'] = poppler_path
    images = convert_from_path(pdf_path, **kwargs)
    if not images:
        return None
    images[0].save(jpg_path, 'JPEG')
    return jpg_path


def imread_unicode(path):
    """OpenCV 在 Windows 上无法直接读取含中文等非 ASCII 路径，需用 imdecode。"""
    data = np.fromfile(path, dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def imwrite_unicode(path, img):
    ext = os.path.splitext(path)[1] or '.jpg'
    ok, buf = cv2.imencode(ext, img)
    if ok:
        buf.tofile(path)
    return ok


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extension


def remove_stamp(path, stamp_id, upload_path):
    """去红章，生成 RedThresh 图供增值税票种路由使用。"""
    img = imread_unicode(path)
    if img is None:
        raise ValueError('无法读取图片文件')
    _, _, r_channel = cv2.split(img)
    _, red_thresh = cv2.threshold(r_channel, 170, 355, cv2.THRESH_BINARY)
    red_path = os.path.join(upload_path, 'RedThresh_{}.jpg'.format(stamp_id))
    imwrite_unicode(red_path, red_thresh)
    return red_path


def process_upload(file, upload_path=UPLOAD_PATH):
    """
    保存上传文件并处理 PDF 转换。
    返回 (img_path, file_name, error_code, error_message)。
    error_code 为 None 表示成功。
    """
    if file is None or not getattr(file, 'filename', None):
        return None, None, 101, '请求参数错误'

    invoice_file_name = file.filename
    if not allowed_file(invoice_file_name):
        return None, None, 102, '失败，文件格式问题'

    os.makedirs(upload_path, exist_ok=True)
    ext = invoice_file_name.rsplit('.', 1)[1].lower()
    safe_name = uuid.uuid4().hex + '.' + ext
    whole_path = os.path.join(upload_path, safe_name)
    file.save(whole_path)

    if ext == 'pdf':
        jpg_path = os.path.join(upload_path, uuid.uuid4().hex + '.jpg')
        try:
            if pdf_to_jpg(whole_path, jpg_path) is None:
                return None, invoice_file_name, 103, 'PDF 转换失败，未读取到页面'
        except Exception as exc:
            return None, invoice_file_name, 103, 'PDF 转换失败，请确认已安装 poppler: {}'.format(str(exc))
        whole_path = jpg_path

    return whole_path, invoice_file_name, None, None


def _ocr_identify_time():
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.fromtimestamp(int(time.time()), tz).strftime('%Y-%m-%d %H:%M:%S')


def recognize_document(img_path, file_name=None):
    """
    票据识别主流程，供 HTTP 接口与 batch_test 调用。
    返回与 build_api_result 相同结构的字典（非 Flask Response）。
    """
    if file_name is None:
        file_name = os.path.basename(img_path)

    img = imread_unicode(img_path)
    if img is None:
        return {
            'code': 105,
            'message': '无法读取图片文件',
            'data': {},
            'FileName': file_name,
            'ocrIdentifyTime': {},
        }

    upload_path = os.path.dirname(img_path) or UPLOAD_PATH
    stamp_id = uuid.uuid4().hex

    route_lines = ocr(img, detector='electronic')

    redthresh_lines = None
    try:
        red_path = remove_stamp(img_path, stamp_id, upload_path)
        red_img = imread_unicode(red_path)
        if red_img is not None:
            redthresh_lines = ocr(red_img, detector='type')
    except ValueError:
        pass

    doc_type = route(route_lines, redthresh_lines)
    doc_cfg = DOC_TYPES.get(doc_type, DOC_TYPES['unknown'])
    main_detector = doc_cfg['detector']
    raw_lines = ocr(img, detector=main_detector)

    parser_result = get_parser(doc_type, raw_lines)
    fields = parser_result if parser_result else {}

    if not fields:
        settings = get_settings()
        llm_cfg = settings.get('llm_fallback', {})
        if llm_cfg.get('enabled') and doc_type != 'unknown':
            fields = fallback(doc_type, raw_lines, llm_cfg) or {}

    data = {
        'docType': doc_type,
        'docTypeName': doc_cfg['name'],
        'fields': fields,
        'rawLines': raw_lines,
    }

    if fields or (doc_type == 'unknown' and raw_lines):
        return {
            'code': 100,
            'message': '识别成功',
            'data': data,
            'FileName': file_name,
            'ocrIdentifyTime': _ocr_identify_time(),
        }

    if not raw_lines:
        return {
            'code': 104,
            'message': '识别为空！',
            'data': data,
            'FileName': file_name,
            'ocrIdentifyTime': {},
        }

    return {
        'code': 100,
        'message': '识别成功',
        'data': data,
        'FileName': file_name,
        'ocrIdentifyTime': _ocr_identify_time(),
    }


# Flask
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
CORS(app, resources=r'/*')


def build_api_result(code, message, data, file_name, ocr_identify_time):
    result = {
        'code': code,
        'message': message,
        'data': data,
        'FileName': file_name,
        'ocrIdentifyTime': ocr_identify_time,
    }
    return jsonify(result)


@app.route('/', methods=['GET'])
def index():
    resp = make_response(render_template('index.html'))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return resp


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/invoice-ocr', methods=['POST'])
def invoice_ocr():
    if 'file' not in request.files:
        return build_api_result(101, '请求参数错误', {}, {}, {})

    file = request.files['file']
    img_path, file_name, err_code, err_msg = process_upload(file)
    if err_code is not None:
        return build_api_result(err_code, err_msg, {}, file_name or {}, {})

    try:
        result = recognize_document(img_path, file_name)
        return build_api_result(
            result['code'],
            result['message'],
            result['data'],
            result['FileName'],
            result['ocrIdentifyTime'],
        )
    except Exception as exc:
        return build_api_result(105, '识别失败: {}'.format(str(exc)), {}, file_name, {})


@app.route('/ocr-raw', methods=['POST'])
def ocr_raw():
    if 'file' not in request.files:
        return build_api_result(101, '请求参数错误', {}, {}, {})

    file = request.files['file']
    img_path, file_name, err_code, err_msg = process_upload(file)
    if err_code is not None:
        return build_api_result(err_code, err_msg, {}, file_name or {}, {})

    try:
        img = imread_unicode(img_path)
        if img is None:
            return build_api_result(105, '无法读取图片文件', {}, file_name, {})

        raw_lines = ocr(img, detector='electronic')
        if raw_lines:
            return build_api_result(
                100,
                '识别成功',
                {'rawLines': raw_lines},
                file_name,
                _ocr_identify_time(),
            )
        return build_api_result(104, '识别为空！', {'rawLines': []}, file_name, {})
    except Exception as exc:
        return build_api_result(105, '识别失败: {}'.format(str(exc)), {}, file_name, {})


if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
