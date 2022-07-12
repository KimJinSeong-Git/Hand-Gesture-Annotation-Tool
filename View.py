from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys

from ViewModel.Canvas import Canvas
from ViewModel.LabelList import LabelList
from ViewModel.ObjectList import ObjectList
import Model

mainUI_dir = 'Resource/UI/Main GUI.ui'
main_form_class = uic.loadUiType(mainUI_dir)[0]

class HandAnnot(QMainWindow, main_form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.model = Model.Model()

        canvas_widget = [
                            self.action_Open,
                            self.menu_Edit,
                            self.menu_Zoom,
                            self.action_Save,
                            
                            self.action_Line,
                            self.statusBar
                        ]

        self.canvas_viewmodel = Canvas(canvas_widget, self.model)

        self.scrollArea_Canvas.setWidget(self.canvas_viewmodel)

if __name__=='__main__':
    app = QApplication(sys.argv)
    view = HandAnnot()
    view.show()
    app.exec_()