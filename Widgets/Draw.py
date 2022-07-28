from PyQt5.QtWidgets import *
# from PyQt5.QtCore import *
# from PyQt5.QtGui import *
import math

from Widgets.Display import *
from Widgets.AddObjectDialog import *

class Draw(QWidget):
    def __init__(self, view, Model):
        super().__init__()

        self.Model = Model

        self.canvas = QLabel(self)
        self.scroll_area = view[0]
        self.label_list = view[1]
        self.object_list = view[2]

        # Init Display Class
        self.Display = Display(self.canvas, self.scroll_area, self.Model)


    # ----- Set View -----
    def setCanvas(self):
        self.Display.setDisplayAnnotInfo()
        img, w, h, c = self.Model.getImgScaled()

        self.setMinimumSize(w, h)
        self.setMaximumSize(w, h)

        self.Display.displayImage(img, w, h)
        self.scroll_area.setWidget(self)


    # ----- Context Menu Event -----
    def contextMenuEvent(self, event):
        pass    
    
    
    # ----- Mouse Event -----
    def mousePressEvent(self, event):
        pass

    def mouseMoveEvent(self, event):
        pos = [event.x(), event.y()]
        self.Model.setCurPos(pos)

        draw_flag = self.Model.getDrawFlag()
        retouch_flag = self.Model.getRetouchFlag()
    
        if draw_flag is True:
            self.draw()
        elif retouch_flag is True:
            self.movePoint()

    def mouseReleaseEvent(self, event):
        # Draw 활성화 되었을 때만 기능 작동
        if self.Model.getDrawFlag() is False:
            return

        # 마우스 뗏을 때 좌표 저장
        pos = [event.x(), event.y()]

        img, w, h, c = self.Model.getImgScaled()
        points = self.Model.getCurPoints()

        # 초기화된 상태라면 첫 클릭 시 좌표를 시작 좌표로 입력
        if points == [] and self.Model.getCurShapeType() is not 'Dot':
            self.Model.addCurPoint(pos)

        # 플래그 상태 확인
        tracking_flag = self.Model.isTracking()
        keep_tracking_flag = self.Model.isKeepTracking()
        
        # 그리기 시작
        if tracking_flag is False:
            self.Model.setPrePos(pos)
            self.setTracking(tracking = True)

        # 그리기 완료 시
        else:
            # Polygon일 때
            if keep_tracking_flag is True:
                # 시작점을 클릭하면 그리기 종료하는 코드
                start_pos = points[0].copy()
                start_pos[0] = int(start_pos[0]*w)
                start_pos[1] = int(start_pos[1]*h)

                if start_pos == self.Model.getCurPos():
                    self.setTracking(tracking = False)
                    self.Model.setKeepTracking(False)
                    self.Model.setDrawFlag(False)

                # 시작점이 아니라면 그리기 계속
                else:
                    self.Model.addCurPoint(pos)

            # Rect, Circle, Line, Dot일 때
            else:
                self.setTracking(tracking = False)
                self.Model.setDrawFlag(False)
                self.Model.addCurPoint(pos)

            # 그리기 종료 후 Object 추가
            keep_tracking_flag = self.Model.isKeepTracking()
            if keep_tracking_flag is False:
                self.addObject()

    def setTracking(self, tracking):
        self.Model.setTracking(tracking)
        self.setMouseTracking(tracking)
        self.canvas.setMouseTracking(tracking)


    # ----- Draw -----
    def draw(self):
        draw_type = self.Model.getCurShapeType()
        img, w, h, c = self.Model.getImgScaled()

        pre_pos = self.Model.getPrePos()
        cur_pos = self.Model.getCurPos()

        cur_points = self.Model.getCurPoints()

        # 정규화 해제
        for point in cur_points:
            point[0] *= w
            point[1] *= h

        point_scale = self.Model.getClickPointRange()

        draw_img = img.copy()
        painter = QPainter(draw_img)
        painter.setPen(QPen(Qt.green, 3, Qt.SolidLine))

        if draw_type == 'Polygon':
            if cur_points == []:
                painter.end()
                return

            # 시작점 저장
            start_point = cur_points[0]
            start_point[0] = int(start_point[0])
            start_point[1] = int(start_point[1])

            # click_range에 따라 start_point에 현재 좌표 세팅
            if cur_pos[0] < start_point[0]+point_scale and cur_pos[0] > start_point[0]-point_scale:
                if cur_pos[1] < start_point[1]+point_scale and cur_pos[1] > start_point[1]-point_scale:
                    cur_pos[0] = start_point[0]
                    cur_pos[1] = start_point[1]
                    self.Model.setCurPos(cur_pos)

            # 이전까지 그린 선들 표시
            pre = cur_points[0]
            for point in cur_points:
                cur = point
                painter.setPen(QPen(Qt.green, 3, Qt.SolidLine))
                painter.drawLine(pre[0], pre[1], cur[0], cur[1])
                painter.setPen(QPen(Qt.red, point_scale, Qt.SolidLine))
                painter.drawPoint(pre[0], pre[1])
                painter.drawPoint(cur[0], cur[1])
                pre = point

            # 현재 그리려고 하는 선 Draw
            src_x = cur_points[-1][0]
            src_y = cur_points[-1][1]
            dst_x = cur_pos[0]
            dst_y = cur_pos[1]

            painter.setPen(QPen(Qt.green, 3, Qt.SolidLine))
            painter.drawLine(src_x, src_y, dst_x, dst_y)
            painter.setPen(QPen(Qt.red, point_scale, Qt.SolidLine))
            painter.drawPoint(src_x, src_y)
            painter.drawPoint(start_point[0], start_point[1])

        elif draw_type == 'Rectangle':
            width = cur_pos[0] - pre_pos[0]
            height = cur_pos[1] - pre_pos[1]
            painter.drawRect(pre_pos[0], pre_pos[1], width, height)

        elif draw_type == 'Circle':
            try:
                rad = math.sqrt(math.pow(pre_pos[0]-cur_pos[0], 2) + math.pow(pre_pos[1]-cur_pos[1], 2))
            except:
                rad = 0
            x_pos = pre_pos[0] - rad
            y_pos = pre_pos[1] - rad
            painter.drawEllipse(x_pos, y_pos, rad*2, rad*2)

        elif draw_type == 'Line':
            painter.drawLine(pre_pos[0], pre_pos[1], cur_pos[0], cur_pos[1])
            
        elif draw_type == 'Dot':
            painter.drawPoint(cur_pos[0], cur_pos[1])

        # 시작점, 끝점 빨간 점으로 표시
        painter.setPen(QPen(Qt.red, point_scale, Qt.SolidLine))
        painter.drawPoint(pre_pos[0], pre_pos[1])
        painter.drawPoint(cur_pos[0], cur_pos[1])

        painter.end()

        self.canvas.setPixmap(draw_img)
    
    def addObject(self):
        dlg = AddObjectDialog([self.label_list, self.object_list], self.Model)
        dlg.exec_()

        if self.Model.getCurLabel() != '':
            self.Model.setCurShapeToDict()

        self.Model.setCurLabel('')
        self.setCanvas()


    # ----- Retouch -----
    def movePoint(self):
        pass

    
    # ----- Object List Click Event -----
    def objectClicked(self):
        pass

    def objectDoubleClicked(self):
        pass


    # ----- Delete -----
    def deleteObject(self):
        pass