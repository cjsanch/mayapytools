import maya.cmds as mc
from PySide6.QtWidgets import QWidget, QMainWindow
from PySide6.QtCore import Qt
import maya.OpenMayaUI as omui
from shiboken6 import wrapInstance

def GetMayaMainWindow()->QMainWindow:
      mayaMainWindow = omui.MQtUtil.mainWindow()
      return wrapInstance(int(mayaMainWindow), QMainWindow)

def RemoveWidgetWithName(objectname):
    for widget in GetMayaMainWindow().findChildren(QWidget, objectname):
        widget.deleteLater()

class MayaWidget(QWidget):
    def __init__(self):
        super().__init__(parent=GetMayaMainWindow())
        self.setWindowFlag(Qt.WindowType.Window)
        RemoveWidgetWithName(self.GetWidgetHash())
        self.setObjectName(self.GetWidgetHash())
        # self.setWindowTitle("chingaso")

    def GetWidgetHash(self):
         return "91a1c5e3685995442e93cea9db5a98c7"
