from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Utils.ConvertAnnotation import *

import math, copy

def img2QPixmap(img, w, h, c):
    qImg = QImage(img.data, w, h, w * c, QImage.Format_RGB888)
    qPixmap = QPixmap.fromImage(qImg)

    return qPixmap

def loadQImg(model):
    img, w, h, c = model.getImgData()
    scaled_w, scaled_h, scaled_c = model.getImgScaled(no_img=True)
    annot_info = model.getAnnotInfo()
    point_scale = model.getClickPointRange()

    qimg = img2QPixmap(img, w, h, c)
    qimg = qimg.scaled(scaled_w, scaled_h)

    annot_info = denormalization(annot_info, scaled_w, scaled_h)

    return qimg, annot_info, point_scale, 

def setDisplayAnnotInfo(qimg, annot_info, point_scale):
    painter = QPainter(qimg)

    painter.setPen(QPen(Qt.red, point_scale, Qt.SolidLine))
    for shape in annot_info['shapes']:
        shape_type = shape['shape_type']
        points = copy.deepcopy(shape['points'])
                    
        if shape_type == 'Polygon':
            pre = points[0]
            painter.setPen(QPen(Qt.magenta, 3, Qt.SolidLine))

            for point in points:
                cur = point
                painter.drawLine(pre[0], pre[1], cur[0], cur[1])

                painter.setPen(QPen(Qt.red, point_scale, Qt.SolidLine))
                painter.drawPoint(cur[0], cur[1])
                painter.drawPoint(pre[0], pre[1])

                painter.setPen(QPen(Qt.magenta, 3, Qt.SolidLine))
                pre = point

            painter.drawLine(points[0][0], points[0][1], pre[0], pre[1])

            painter.setPen(QPen(Qt.red, point_scale, Qt.SolidLine))
            painter.drawPoint(points[0][0], points[0][1])
            painter.drawPoint(pre[0], pre[1])


        elif shape_type == 'Gesture Polygon':
            painter.setPen(QPen(Qt.cyan, 3, Qt.SolidLine))
            nb_points = 21
            for idx in range(1, nb_points):
                if idx%4 == 1:
                    src_pos = points[idx]
                    continue
                dst_pos = points[idx]
                painter.drawLine(src_pos[0], src_pos[1], dst_pos[0], dst_pos[1])

                painter.setPen(QPen(Qt.red, point_scale, Qt.SolidLine))
                painter.drawPoint(src_pos[0], src_pos[1])
                painter.drawPoint(dst_pos[0], dst_pos[1])

                painter.setPen(QPen(Qt.cyan, 3, Qt.SolidLine))
                src_pos = dst_pos

            list_hand = [(0, 1), (0, 5), (0, 17), (5, 9), (9, 13), (13, 17)]

            for idx in list_hand:
                src = idx[0]
                dst = idx[1]
                painter.setPen(QPen(Qt.cyan, 3, Qt.SolidLine))
                painter.drawLine(points[src][0], points[src][1], points[dst][0], points[dst][1])

                painter.setPen(QPen(Qt.red, point_scale, Qt.SolidLine))
                painter.drawPoint(points[src][0], points[src][1])
                painter.drawPoint(points[dst][0], points[dst][1])
    
        elif shape_type == 'Rectangle':
            width = (points[1][0] - points[0][0])
            height = (points[1][1] - points[0][1])

            color = QPen(Qt.blue, 3, Qt.SolidLine)
            painter.setPen(color)
            painter.drawRect(points[0][0], points[0][1], width, height)
            painter.setPen(QPen(Qt.red, point_scale, Qt.SolidLine))
            painter.drawPoint(points[0][0], points[0][1])
            painter.drawPoint(points[1][0], points[1][1])

        elif shape_type == 'Circle':
            rad = math.sqrt(math.pow(points[0][0]-points[1][0], 2) + math.pow(points[0][1]-points[1][1], 2))

            color = QPen(Qt.red, 3, Qt.SolidLine)
            painter.setPen(color)
            painter.drawEllipse(points[0][0]-rad, points[0][1]-rad, rad*2, rad*2)
            painter.setPen(QPen(Qt.red, point_scale, Qt.SolidLine))
            painter.drawPoint(points[0][0], points[0][1])
            painter.drawPoint(points[1][0], points[1][1])


        elif shape_type == 'Line':
            color = QPen(Qt.yellow, 3, Qt.SolidLine)
            painter.setPen(color)
            painter.drawLine(points[0][0], points[0][1], points[1][0], points[1][1])
            painter.setPen(QPen(Qt.red, point_scale, Qt.SolidLine))
            painter.drawPoint(points[0][0], points[0][1])
            painter.drawPoint(points[1][0], points[1][1])


        elif shape_type == 'Dot':
            painter.drawPoint(points[0][0], points[0][1])

    painter.end()
    
    return qimg

def displaySelectedObject(idx, qimg, denorm_annot):
    clicked_shape = denorm_annot['shapes'][idx]
    shape_type = clicked_shape['shape_type']
    points = clicked_shape['points']

    painter = QPainter(qimg)
    painter.setPen(QPen(Qt.darkBlue, 10, Qt.SolidLine))

    if shape_type == 'Polygon':
        pre = points[0]

        for point in points:
            cur = point
            painter.drawLine(pre[0], pre[1], cur[0], cur[1])
            pre = point
        painter.drawLine(points[0][0], points[0][1], pre[0], pre[1])

    elif shape_type == 'Gesture Polygon':
        nb_points = 21
        for idx in range(1, nb_points):
            if idx%4 == 1:
                src_pos = points[idx]
                continue
            dst_pos = points[idx]
            painter.drawLine(src_pos[0], src_pos[1], dst_pos[0], dst_pos[1])
            src_pos = dst_pos

        list_hand = [(0, 1), (0, 5), (0, 17), (5, 9), (9, 13), (13, 17)]

        for idx in list_hand:
            src = idx[0]
            dst = idx[1]
            painter.drawLine(points[src][0], points[src][1], points[dst][0], points[dst][1])

    elif shape_type == 'Rectangle':
        width = (points[1][0] - points[0][0])
        height = (points[1][1] - points[0][1])

        painter.drawRect(points[0][0], points[0][1], width, height)

    elif shape_type == 'Circle':
        rad = math.sqrt(math.pow(points[0][0]-points[1][0], 2) + math.pow(points[0][1]-points[1][1], 2))

        painter.drawEllipse(points[0][0]-rad, points[0][1]-rad, rad*2, rad*2)

    elif shape_type == 'Line':
        painter.drawLine(points[0][0], points[0][1], points[1][0], points[1][1])

    painter.end()
    
    return qimg

def displayImage( canvas, img, w, h):
    canvas = canvas
    canvas.clear()

    canvas.setGeometry(0, 0, w, h)
    canvas.setPixmap(img)