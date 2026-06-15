from flask import Flask, jsonify, request, redirect, render_template, make_response
from flask_cors import CORS
import re
import time
from glob import glob
from PIL import Image
import numpy as np
import os
import sys
import cv2
import uuid
import json
from PIL import Image
from datetime import datetime
from model_post_type import ocr as OCR
from model_postE_invoice import ocr as ocr_E
from model_postM_invoice import ocr as ocr_M
from apphelper.image import union_rbox
from application.invoice_e import invoice_e
from application.invoice_m import invoice_m
import pytz
port = 11111
allowed_extension = ['jpg', 'png', 'jpeg', 'JPG', 'pdf']

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

# Flask
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
CORS(app, resources=r'/*')

# 构建接口返回结果
def build_api_result(code, message, data,file_name,ocr_identify_time):
    result = {
        "code": code,
        "message": message,
        "data": data,
        "FileName": file_name,
        "ocrIdentifyTime": ocr_identify_time
    }
    return jsonify(result)

# 检查文件扩展名
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extension


# 首页：测试上传页面
@app.route('/', methods=['GET'])
def index():
    resp = make_response(render_template('index.html'))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return resp

# 健康检查
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

# 增值税发票OCR识别接口
@app.route('/invoice-ocr', methods=['POST'])
def invoice_ocr():
    # 校验请求参数
    if 'file' not in request.files:
        return build_api_result(101, "请求参数错误", {},{},{})

    # 获取请求参数
    file = request.files['file']
    invoice_file_name = file.filename
    
    # 检查文件扩展名
    if not allowed_file(invoice_file_name):
        return build_api_result(102, "失败，文件格式问题", {},{},{})
   
    upload_path = "test"
    os.makedirs(upload_path, exist_ok=True)
    ext = invoice_file_name.rsplit('.', 1)[1].lower()
    safe_name = uuid.uuid4().hex + '.' + ext
    whole_path = os.path.join(upload_path, safe_name)
    file.save(whole_path)

    if ext == 'pdf':
        jpg_path = os.path.join(upload_path, uuid.uuid4().hex + '.jpg')
        try:
            if pdf_to_jpg(whole_path, jpg_path) is None:
                return build_api_result(103, "PDF 转换失败，未读取到页面", {}, {}, {})
        except Exception as e:
            return build_api_result(103, "PDF 转换失败，请确认已安装 poppler: {}".format(str(e)), {}, {}, {})
        whole_path = jpg_path

    stamp_id = uuid.uuid4().hex

    #去章处理方法
    def remove_stamp(path, stamp_id):
        img = imread_unicode(path)
        if img is None:
            raise ValueError("无法读取图片文件")
        B_channel, G_channel, R_channel = cv2.split(img)
        _, RedThresh = cv2.threshold(R_channel, 170, 355, cv2.THRESH_BINARY)
        imwrite_unicode(os.path.join(upload_path, 'RedThresh_{}.jpg'.format(stamp_id)), RedThresh)
    
    def Recognition_invoice(path, stamp_id):
        '''
        识别发票类别
        :param none:
        :return: 发票类别
        '''
        remove_stamp(path, stamp_id)
        img1 = imread_unicode(os.path.join(upload_path, 'RedThresh_{}.jpg'.format(stamp_id)))
        if img1 is None:
            return 2
        result_type = OCR(img1)
        result_type = union_rbox(result_type, 0.2)
        
        print(result_type)
        
        if len(result_type) > 0:
            N = len(result_type)
            for i in range(N):
                txt = result_type[i]['text'].replace(' ', '')
                txt = txt.replace(' ', '')
                type_1 = re.findall('电子普通',txt)
                type_2 = re.findall('普通发票',txt)
                type_3 = re.findall('专用发票',txt)
                if type_1 == None:
                    type_1 = []
                if type_2 == None:
                    type_2 = []
                if type_3 == None:
                    type_3 = []
            print(type_1)
            print(type_2)
            print(type_3)
            if len(type_1) > 0:
                return 1
            else:
                return 2
        elif len(result_type)==0:
            return 2
    
    try:
        Recognition_invoice = Recognition_invoice(whole_path, stamp_id)
        img = imread_unicode(whole_path)
        if img is None:
            return build_api_result(105, "无法读取图片文件", {}, invoice_file_name, {})
        h, w = img.shape[:2]
        if Recognition_invoice == 1:
            result = ocr_E(img)
            res = invoice_e(result)
            res = res.res
        elif Recognition_invoice == 2:
            result = ocr_M(img)
            res = invoice_m(result)
            res = res.res
        else:
            res = []
        if len(res) > 0:
            tz = pytz.timezone('Asia/Shanghai') #东八区
            ocr_identify_time = datetime.fromtimestamp(int(time.time()),pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
            return build_api_result(100, "识别成功" , res, invoice_file_name,ocr_identify_time)
        elif len(res) == 0:
            return build_api_result(104, "识别为空！" ,{},{},{})
    except Exception as e:
        return build_api_result(105, "识别失败: {}".format(str(e)), {}, invoice_file_name, {})
        
if __name__ == "__main__":
    # Run
    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
