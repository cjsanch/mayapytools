from PySide6.QtWidgets import QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLabel
from core.MayaWidget import MayaWidget
import maya.cmds as mc

class MayaToUE:
    def __init__(self):
        self.meshes = []
        self.rootJnt = ""
        self.clips = []

    def SetSelectedAsMesh(self):
        selection = mc.ls(sl=True)
        if not selection:
            raise Exception("Please select the rig mesh(es)")
        
        for obj in selection:
            shapes = mc.listRelatives(obj, s=True)
            if not shapes or mc.objectType(shapes[0]) != "mesh":
                raise Exception(f"{obj} is not a mesh, please select the mesh(es) of the rig")

class MayaToUEWidget(MayaWidget):
    def __init__(self):
        super().__init__()
        self.mayaToUE = MayaToUE()
        self.setWindowTitle("Maya to Unreal Engine")

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        meshSelectLayout = QHBoxLayout()
        self.masterLayout.addLayout(meshSelectLayout)
        meshSelectLayout.addWidget(QLabel("Mesh:"))
        self.meshSelectLineEdit = QLineEdit()
        self.meshSelectLineEdit.setEnabled(False)
        meshSelectLayout.addWidget(self.meshSelectLineEdit)
        meshSelectBtn = QPushButton("<<<")
        meshSelectLayout.addWidget(meshSelectBtn)
        meshSelectBtn.clicked.connect(self.MeshSelectBtnClicked)

    def MeshSelectBtnClicked(self):
        self.mayaToUE.SetSelectedAsMesh()
        self.meshSelectLineEdit.setText(",".join(self.mayaToUE.meshes))



    def GetWidgetHash(self):
        return "27b17edf6728f4b84a6da62207131998364c649d69fd3a69ba1acef6c1f6f84e"
    
def Run():
    mayaToUEWidget = MayaToUEWidget()
    mayaToUEWidget.show()

Run()