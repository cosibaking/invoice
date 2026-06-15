# -*- coding: utf-8 -*-
from config import opencvFlag, GPU, IMGSIZE, ocrFlag

if not GPU:
    import os

    os.environ["CUDA_VISIBLE_DEVICES"] = ''  ##不启用GPU

if ocrFlag == 'torch':
    from crnn.crnn_torch import crnnOcr as crnnOcr  ##torch版本ocr
elif ocrFlag == 'keras':
    from crnn.crnn_keras import crnnOcr as crnnOcr  ##keras版本OCR

import cv2
import numpy as np
from PIL import Image

from text.detector.detectors import TextDetector
from apphelper.image import get_boxes, letterbox_image

from text.opencv_dnn_detect import angle_detect  ##文字方向检测,支持dnn/tensorflow
from apphelper.image import rotate_cut_img, sort_box, solve

print("Text detect engine:{}".format(opencvFlag))

DEFAULT_DETECT_PARAMS = dict(
    MAX_HORIZONTAL_GAP=50,  ##字符之间的最大间隔，用于文本行的合并
    MIN_V_OVERLAPS=0.6,
    MIN_SIZE_SIM=0.6,
    TEXT_PROPOSALS_MIN_SCORE=0.1,
    TEXT_PROPOSALS_NMS_THRESH=0.3,
    TEXT_LINE_NMS_THRESH=0.7,  ##文本行之间测iou值
)

DETECTOR_ALPH = {
    'electronic': 0.1,
    'machine': 0.01,
    'type': 0.01,
}

DETECTOR_TEXT_DETECT_GAP = {
    'electronic': 50,
    'machine': 30,
    'type': 30,
}

_detect_modules = {}


def _get_detect_module(detector):
    if opencvFlag == 'opencv':
        from text import opencv_dnn_detect as detect
        return detect
    elif opencvFlag == 'darknet':
        from text import darknet_detect as detect
        return detect
    if detector not in _detect_modules:
        if detector == 'electronic':
            from text import keras_detectE_invoice as detect
        elif detector == 'machine':
            from text import keras_detectM_invoice as detect
        elif detector == 'type':
            from text import keras_detect_type as detect
        else:
            raise ValueError("unknown detector: {}".format(detector))
        _detect_modules[detector] = detect
    return _detect_modules[detector]


def text_detect(img,
                detector='electronic',
                MAX_HORIZONTAL_GAP=None,
                MIN_V_OVERLAPS=0.6,
                MIN_SIZE_SIM=0.6,
                TEXT_PROPOSALS_MIN_SCORE=0.7,
                TEXT_PROPOSALS_NMS_THRESH=0.3,
                TEXT_LINE_NMS_THRESH=0.3,
                ):
    if MAX_HORIZONTAL_GAP is None:
        MAX_HORIZONTAL_GAP = DETECTOR_TEXT_DETECT_GAP.get(detector, 50)
    detect = _get_detect_module(detector)
    boxes, scores = detect.text_detect(np.array(img))
    boxes = np.array(boxes, dtype=np.float32)
    scores = np.array(scores, dtype=np.float32)
    textdetector = TextDetector(MAX_HORIZONTAL_GAP, MIN_V_OVERLAPS, MIN_SIZE_SIM)
    shape = img.shape[:2]
    boxes = textdetector.detect(boxes,
                                scores[:, np.newaxis],
                                shape,
                                TEXT_PROPOSALS_MIN_SCORE,
                                TEXT_PROPOSALS_NMS_THRESH,
                                TEXT_LINE_NMS_THRESH,
                                )

    text_recs = get_boxes(boxes)
    newBox = []
    rx = 1
    ry = 1
    for box in text_recs:
        x1, y1 = (box[0], box[1])
        x2, y2 = (box[2], box[3])
        x3, y3 = (box[6], box[7])
        x4, y4 = (box[4], box[5])
        newBox.append([x1 * rx, y1 * ry, x2 * rx, y2 * ry, x3 * rx, y3 * ry, x4 * rx, y4 * ry])
    return newBox


def crnnRec(im, boxes, leftAdjust=False, rightAdjust=False, alph=0.2, f=1.0):
    """
    crnn模型，ocr识别
    leftAdjust,rightAdjust 是否左右调整box 边界误差，解决文字漏检
    """
    results = []
    im = Image.fromarray(im)
    for index, box in enumerate(boxes):
        degree, w, h, cx, cy = solve(box)
        partImg, newW, newH = rotate_cut_img(im, degree, box, w, h, leftAdjust, rightAdjust, alph)
        text = crnnOcr(partImg.convert('L'))
        if text.strip() != u'':
            results.append({'cx': cx * f, 'cy': cy * f, 'text': text, 'w': newW * f, 'h': newH * f,
                            'degree': degree * 180.0 / np.pi})

    return results


def eval_angle(im, detectAngle=False):
    """
    估计图片偏移角度
    @@param:im
    @@param:detectAngle 是否检测文字朝向
    """
    angle = 0
    img = np.array(im)
    if detectAngle:
        angle = angle_detect(img=np.copy(img))  ##文字朝向检测
        if angle == 90:
            im = Image.fromarray(im).transpose(Image.ROTATE_90)
        elif angle == 180:
            im = Image.fromarray(im).transpose(Image.ROTATE_180)
        elif angle == 270:
            im = Image.fromarray(im).transpose(Image.ROTATE_270)
        img = np.array(im)

    return angle, img


def model(img, detector='electronic', detectAngle=False, config={}, leftAdjust=False, rightAdjust=False, alph=0.2):
    """
    @@param:img,
    @@param:ifadjustDegree 调整文字识别倾斜角度
    @@param:detectAngle,是否检测文字朝向
    """
    angle, img = eval_angle(img, detectAngle=detectAngle)  ##文字方向检测
    if opencvFlag != 'keras':
        img, f = letterbox_image(Image.fromarray(img), IMGSIZE)  ## pad
        img = np.array(img)
    else:
        f = 1.0  ##解决box在原图坐标不一致问题

    config['img'] = img
    config['detector'] = detector
    text_recs = text_detect(**config)  ##文字检测
    newBox = sort_box(text_recs)  ##行文本识别
    result = crnnRec(np.array(img), newBox, leftAdjust, rightAdjust, alph, 1.0 / f)
    return img, result, angle

####################################################################################################

sess = None
if GPU:
    import tensorflow as tf

    os.environ["CUDA_VISIBLE_DEVICES"] = '0'   #指定第一块GPU可用
    _tf_config = tf.ConfigProto()
    _tf_config.gpu_options.per_process_gpu_memory_fraction = 0.3  # 程序最多只能占用指定gpu30%的显存
    sess = tf.Session(config=_tf_config)


def ocr(img, detector='electronic'):
    alph = DETECTOR_ALPH.get(detector, 0.1)
    _, result, angle = model(img,
                             detector=detector,
                             detectAngle=True,  ##是否进行文字方向检测
                             config=dict(DEFAULT_DETECT_PARAMS),
                             leftAdjust=True,  ##对检测的文本行进行向左延伸
                             rightAdjust=True,  ##对检测的文本行进行向右延伸
                             alph=alph,  ##对检测的文本行进行向右、左延伸的倍数
                             )
    return result
