from PyQt5 import uic
from PyQt5.QtWidgets import *
# from PyQt5.QtCore import *
# from PyQt5.QtGui import *

import sys
import os
from functools import partial

from Model import *
from Widgets.Draw import *
from Widgets.Zoom import *

from Utils.Display import *
from Utils.AutoAnnotation import *
from Utils.ConvertAnnotation import *
from Utils.ImageProc import *

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
Ui_MainWindow, QtBaseClass = uic.loadUiType(BASE_DIR + r'/Resource/UI/Main GUI.ui')

class HandAnnot(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.binding()
        self.actionConnect()

        self.menuRefresh()

    def binding(self):
        self.Model = Model()

        self.stacked_widget = QStackedWidget()
        self.Draw = Draw([self.listWidget_LabelList, self.listWidget_ObjectList], self.Model)
        self.Zoom = Zoom(self.stacked_widget, self.Model)

        self.stacked_widget.addWidget(self.Draw)
        self.stacked_widget.addWidget(self.Zoom)
        self.scrollArea_Canvas.setWidget(self.stacked_widget)

    def actionConnect(self):
        self.action_Open.triggered.connect(self.openFile)
        self.action_Save.triggered.connect(self.saveJson)
        self.action_Exit.triggered.connect(self.exit)

        self.action_Polygon.triggered.connect(partial(self.setDraw, 'Polygon', True))
        self.action_Right_Gesture.triggered.connect(partial(self.setGesture, 'right'))
        self.action_Left_Gesture.triggered.connect(partial(self.setGesture, 'left'))
        self.action_Rectangle.triggered.connect(partial(self.setDraw, 'Rectangle', True))
        self.action_Circle.triggered.connect(partial(self.setDraw, 'Circle', True))
        self.action_Line.triggered.connect(partial(self.setDraw, 'Line', True))
        self.action_Dot.triggered.connect(partial(self.setDraw, 'Dot', True))

        self.action_Retouch.triggered.connect(self.setRetouch)
        self.action_Auto_Annotation.triggered.connect(self.setAuto)
        self.action_Undo.triggered.connect(self.undo)

        self.action_Zoom_In.triggered.connect(partial(self.setZoom,'In'))
        self.action_Zoom_Out.triggered.connect(partial(self.setZoom,'Out'))

        # Connect Object List
        self.listWidget_ObjectList.itemClicked.connect(self.objectClicked)
        self.listWidget_ObjectList.itemDoubleClicked.connect(self.objectDoubleClicked)


    # ----- File Actions -----
    def openFile(self):
        # File Open by Dialog
        title = 'Open Image'
        filter = 'Images(*.jpg *.jpeg *.png)'
        file_path = QFileDialog.getOpenFileName(self, title, filter=filter)[0]

        # Exception Handling - Unavailable File Path
        if file_path == '': return

        # Initialize Data in Model
        self.initData()

        # Load Image From File Path
        img, w, h, c = loadImgData(file_path)

        if self.isExistJsonFile(file_path):
            # Json 파일이 존재할 경우 json 데이터 불러온 후 dict에 저장
            # Save Loaded Annotation Info to Model
            opened_annot_info = json2Dict(self.jsonPath)
            self.Model.setAnnotDict(opened_annot_info)

            cur_annot_info = self.Model.getAnnotInfo()
            normalized_annot_info = normalization(cur_annot_info, w, h)
            self.Model.setAnnotDict(normalized_annot_info)
            self.loadLabelList()
            self.loadObjectList()
        else:
            # 존재하지 않을 경우 이미지의 경로, width, height dict에 저장
            self.Model.setAnnotInfo(file_path, w, h)

        # Save Original Image to Model
        self.Model.setImgData(img, w, h, c)

        # Save Image for Display to Model
        img_QPixmap = img2QPixmap(img, w, h, c)
        self.Model.setImgScaled(img_QPixmap, w, h, c)

        self.Model.pushAnnot(self.Model.getAnnotInfo())
        # Activate Menu
        self.Model.setMenuFlag(True)
        self.menuRefresh()

        # Display Canvas
        self.Draw.setCanvas()
        self.Zoom.setCanvas()

    def isExistJsonFile(self, filePath):
        # 파일 이름과, 확장자 분리하여 변수에 저장
        fileName = os.path.splitext(os.path.basename(filePath))[0]
        # Json 경로명 넣기
        self.jsonPath = os.path.dirname(filePath) + '/' + fileName + '.json'

        # 이미지 파일에 json이 존재할 경우 True, 그렇지 않으면 False 반환
        return True if os.path.isfile(self.jsonPath) else False

    def loadLabelList(self):
        label_list = []
        shapes = self.Model.getAnnotInfo()['shapes']
        if not shapes: return

        for shape in shapes:
            label = shape['label']
            if label not in label_list:
                label_list.append(label)

        for label in label_list:
            self.listWidget_LabelList.addItem(QListWidgetItem(label))
            self.Model.setLabel(label)

    def loadObjectList(self):
        self.listWidget_ObjectList.clear()
        shapes = self.Model.getAnnotInfo(True)['shapes']
        if not shapes: return

        for shape in shapes:
            obj_type = shape['shape_type']
            obj_label = shape['label']
            self.listWidget_ObjectList.addItem(QListWidgetItem(obj_type + '_' + obj_label))

    def menuRefresh(self):
        # 메뉴 아이템 배열에 저장
        mItems = [self.menu_Edit, self.menu_Zoom, self.action_Save]
        for mItem in mItems:
            mItem.setEnabled(self.Model.getMenuFlag())

    def initData(self):
        self.Model.setImgData(None, None, None, None)
        self.Model.setImgScaled(None, None, None, None)
        self.Model.initAnnotStack()
        self.Model.initAnnotInfo()
        self.Model.initLabelList()
        self.listWidget_LabelList.clear()
        self.listWidget_ObjectList.clear()

    def saveJson(self):
        img, w, h = self.Model.getImgData()[:3]

        # 이미지 데이터가 없을 경우 return
        if img is None: return

        # dict형태의 annot_info를 정규화 해제 후 json 파일로 저장
        cur_annot_info = self.Model.getAnnotInfo()
        denormalized_annot_info = denormalization(cur_annot_info, w, h)
        dict2Json(denormalized_annot_info, self.jsonPath)

    def exit(self):
        self.close()


    # ----- Edit Actions -----
    def setGesture(self, hand_dir):
        self.setDraw('Gesture Polygon', draw=False)
        
        # 손목 Point
        self.Model.addCurPoint([0.5, 0.65], True)

        # 엄지손가락 시작점 설정
        if hand_dir == 'right':
            x_pos = 0.4
        elif hand_dir == 'left':
            x_pos = 0.6
        y_pos = 0.5

        # 점찍기 시작
        nb_points = 21
        for idx in range(1, nb_points):
            if idx%4 == 1:
                # 오른손은 왼쪽에서 오른쪽
                if hand_dir == 'right':
                    x_pos += 0.05
                # 왼손은 오른쪽에서 왼쪽
                elif hand_dir == 'left':
                    x_pos -= 0.05
                y_pos = 0.5
            pos = [round(x_pos, 2), round(y_pos, 2)]
            self.Model.addCurPoint(pos, True)
            y_pos -= 0.05

        self.Draw.addObject()

    def setDraw(self, shape, draw=True):
        self.Draw.setCanvas()
        self.Model.setDrawFlag(draw)
        self.Model.setCurShapeType(shape)
        if shape == 'Polygon' :
            self.Model.setKeepTracking(True)
        if shape == 'Dot' :
            self.Draw.setTracking(True)
        self.Model.resetCurPoints()
        self.statusBar.showMessage('Seleted Shape: {shape}'.format(shape=shape))
        
    def setRetouch(self):
        retouch_flag = self.Model.getRetouchFlag()
        if retouch_flag is True:
            self.Model.setRetouchFlag(False)
        else:
            self.Model.setRetouchFlag(True)

    def setAuto(self):
        self.Model.setCurShapeType('Gesture Polygon')

        img, w, h, c = self.Model.getImgData()
        landmarks = autoAnnotation(img)
        
        if len(landmarks) is 0:
            title = 'Error: 자동으로 좌표를 찾을 수 없습니다.' 
            text = 'Mediapipe Hands에서 손 좌표 찾기에 실패했습니다.'
            QMessageBox.about(self, title, text)
            return

        for landmark in landmarks:
            processed_landmark = landmarksToList(landmark)
            self.Model.setCurPoints(processed_landmark)
            self.Draw.addObject()

    def undo(self):
        if self.Model.getImgData() is None: return
        self.Model.setAnnotDict(self.Model.popAnnot())

        self.Draw.setCanvas()
        self.Zoom.setCanvas()
        self.loadObjectList()


    # ----- Zoom Actions -----
    def setZoom(self, type):
        self.Model.setZoomType(type)
        self.Zoom.resizeZoomInOut()
        self.Draw.setCanvas()


    # ----- Key Event -----
    def keyPressEvent(self, event):
        if self.Model.getImgData() is None:
            return

        if event.key() == Qt.Key_Control:
            self.Zoom.setCanvas()
            self.stacked_widget.setCurrentWidget(self.Zoom)

    def keyReleaseEvent(self, event):
        if self.Model.getImgData() is None:
            return
        
        if event.key() == Qt.Key_Control:
            self.Draw.setCanvas()
            self.stacked_widget.setCurrentWidget(self.Draw)


    # ----- Context Menu Event -----
    def contextMenuEvent(self, event):
        if self.Model.getImgData() is None: return

        menu = QMenu(self)
        action_Polygon = menu.addAction('Polygon')
        action_Right_Gesture_Polygon = menu.addAction('Right Gesture Polygon')
        action_Left_Gesture_Polygon = menu.addAction('Left Gesture Polygon')
        action_Rectangle = menu.addAction('Rectangle')
        action_Circle = menu.addAction('Circle')
        action_Line = menu.addAction('Line')
        action_Dot = menu.addAction('Dot')

        action = menu.exec(self.mapToGlobal(event.pos()))
        if action == action_Polygon: self.setDraw('Polygon')
        if action == action_Right_Gesture_Polygon: self.setGesture('right')
        if action == action_Left_Gesture_Polygon: self.setGesture('left')
        if action == action_Rectangle: self.setDraw('Rectangle')
        if action == action_Circle: self.setDraw('Circle')
        if action == action_Line: self.setDraw('Line')
        if action == action_Dot: self.setDraw('Dot')
        

    # ----- Delete -----
    def objectClicked(self):
        self.Draw.setCanvas()

        idx = self.listWidget_ObjectList.currentRow()        
        self.Model.setSelectedObjectIndex(idx)
        idx = self.Model.getSelectedObjectIndex()

        qimg, w, h, c = self.Model.getImgScaled()
        origin_annot = self.Model.getAnnotInfo()
        denorm_annot = denormalization(origin_annot, w, h)

        displaySelectedObject(idx, qimg, denorm_annot)
        self.Model.setImgScaled(qimg,w, h, c)

        self.Draw.setCanvas(reset_canvas=False)

    def objectDoubleClicked(self):
        self.Model.pushAnnot(self.Model.getAnnotInfo())
        idx = self.Model.getSelectedObjectIndex()

        self.deleteObject()
        self.listWidget_ObjectList.takeItem(idx)
        self.Draw.setCanvas(reset_canvas=False)

    def deleteObject(self):
        object_idx = self.Model.getSelectedObjectIndex()
        self.Model.deleteShape(object_idx)

        qimg, annot_info, point_scale = loadQImg(self.Model)
        qimg_add_info = setDisplayAnnotInfo(qimg, annot_info, point_scale)
        w, h, c = self.Model.getImgScaled(no_img=True)

        self.Model.setImgScaled(qimg_add_info, w, h, c)


if __name__=='__main__':
    app = QApplication(sys.argv)
    view = HandAnnot()
    view.show()
    app.exec_()