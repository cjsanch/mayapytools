from core.MayaWidget import MayaWidget
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QLineEdit, QColorDialog
import maya.cmds as mc
from maya.OpenMaya import MVector # this is the same as the Vector3 in Unity, transform.position

import importlib
import core.MayaUtilities
importlib.reload(core.MayaUtilities)
from core.MayaUtilities import (CreateCircleControllerForJnt, 
                                CreateBoxControllerForJnt,
                                CreatePlusController,
                                ConfigureCtrlForJnt,
                                GetObjectPositionAsMVec
                                )
#class handling the rigging
class LimbRigger:
    #constructor that initializes the used attributes
    def __init__(self):
        self.nameBase = "" #the base name that is used to name the elements of the rig
        self.controllerSize = 10 #the size that the controllers spawn in
        self.blendControllerSize = 4 #the size for the ik/fk blend control
        self.controllerColorRGB = [1,1,1] #the color of the rig controls, defaulted to white

    def SetNameBase(self, newNameBase): #function that sets the new name base
        self.nameBase = newNameBase #changes the name base into the new one
        print(f"name base is set to: {self.nameBase}") #printing the confirmation of the name change

    def SetControllerSize(self, newControllerSize): #updates the size of the controllers
        self.controllerSize = newControllerSize #changes the controller size into the new one

    def SetBlendControllerSize(self, newBlendControllerSize): #updates the size of the ik/fk blend controller
        self.blendControllerSize = newBlendControllerSize #changes the controller size into the new one

    def RigLimb(self):
        print("Start Rigging!!") #print indication that the rigging process has begun
        rootJnt, midJnt, endJnt = mc.ls(sl=True) #to get the root, middle, end of the selected joints
        print(f"found root {rootJnt}, mid: {midJnt}, and end {endJnt}") #print confirmation of the joints that are currently selected

        rootCtrl, rootCtrlGrp = CreateCircleControllerForJnt(rootJnt, "fk_" + self.nameBase, self.controllerSize) #spawns a FK controller for the root joint
        midCtrl, midCtrlGrp = CreateCircleControllerForJnt(midJnt, "fk_" + self.nameBase, self.controllerSize) #spawns a FK controller for the middle joint
        endCtrl, endCtrlGrp = CreateCircleControllerForJnt(endJnt, "fk_" + self.nameBase, self.controllerSize) #spawns a FK controller for the ending joint

        print(f"parenting: {endCtrlGrp} to {midCtrl}") #prints indication of the parent operation
        mc.parent(endCtrlGrp, midCtrl) #parents the ending controller group to the middle controller
        print(f"parenting: {midCtrlGrp} to {rootCtrl}") #prints indication of the parent operation
        mc.parent(midCtrlGrp, rootCtrl) #parents the middle controller group to the root controller

        endIKCtrl, endIKCtrlGrp = CreateBoxControllerForJnt(endJnt, "ik_" + self.nameBase, self.controllerSize) #spawns a IK controller for the ending joint 

        ikFkBlendCtrlPrefix = self.nameBase+"_ikfkBlend" #the prefix used for the naming of the blend controller
        ikFkBlendController = CreatePlusController(ikFkBlendCtrlPrefix, self.blendControllerSize) #creates the controller for the ik/fk blending
        ikFkBlendController, ikFkBlendCtrlControllerGrp = ConfigureCtrlForJnt(rootJnt, ikFkBlendController, False) #positions the ik/fk blend controller at the root joint

        ikFkBlendAttrName = "ikfkBlend" #name of the blend attribute
        mc.addAttr(ikFkBlendController, ln=ikFkBlendAttrName, min = 0, max = 1, k=True) #adds the blending attribute, where 0 = FK and 1 = IK

        ikHandleName = "ikHandle_" + self.nameBase #name for the ik handle
        mc.ikHandle(n=ikHandleName, sj = rootJnt, ee=endJnt, sol="ikRPsolver") #creates a ik handle from the root joint to the end joint

        rootJntLoc = GetObjectPositionAsMVec(rootJnt) #gets the position of the root joint as a vector
        endJntLoc = GetObjectPositionAsMVec(endJnt) #gets the position of the root joint as a vector

        poleVectorVals = mc.getAttr(f"{ikHandleName}.poleVector")[0] #gets the direction of the pole vector from the ik handle
        poleVecDir = MVector(poleVectorVals[0], poleVectorVals[1], poleVectorVals[2]) #converts it to a vector object
        poleVecDir.normalize() #makes it a unit vector with a length of one

        rootToEndVec = endJntLoc - rootJntLoc #vector from the root joint to the end joint
        rootToEndDist = rootToEndVec.length() #distance from the root joint to the end joint

        poleVectorCtrlLoc = rootJntLoc + rootToEndVec /2.0 + poleVecDir * rootToEndDist #calculates the position of the pole vector controller

        poleVectorCtrlName = "ac_ik_" + self.nameBase + "poleVector" #name for the pole vector controller
        mc.spaceLocator(n=poleVectorCtrlName) #creates a locator for the pole vector

        poleVectorCtrlGrpName = poleVectorCtrlName + "_grp" #the name for the pole vector contoller group
        mc.group(poleVectorCtrlName, n = poleVectorCtrlGrpName) #groups the locator

        mc.setAttr(f"{poleVectorCtrlGrpName}.translate", poleVectorCtrlLoc.x, poleVectorCtrlLoc.y, poleVectorCtrlLoc.z, type="double3") #sets the position of the pole vector control
        mc.poleVectorConstraint(poleVectorCtrlName, ikHandleName) #constrains the ik handle to the pole vector

        mc.parent(ikHandleName, endIKCtrl) #parents the ik handle to the ik controller
        mc.setAttr(f"{ikHandleName}.v", 0) #sets the visibility to 0 (hides it)

        mc.connectAttr(f"{ikFkBlendController}. {ikFkBlendAttrName}", f"{ikHandleName}.ikBlend") #connects the blend attribute to the ik handle
        mc.connectAttr(f"{ikFkBlendController}. {ikFkBlendAttrName}", f"{endIKCtrlGrp}.v") #controls the ik controllers visibility
        mc.connectAttr(f"{ikFkBlendController}. {ikFkBlendAttrName}", f"{poleVectorCtrlGrpName}.v") #controls the pol vectors visibilty

        reverseNodeName = f"{self.nameBase}_reverse" #sets a name for the reverse node in the node editor
        mc.createNode("reverse", n=reverseNodeName) #creates the reverse node in the node editor

        mc.connectAttr(f"{ikFkBlendController}. {ikFkBlendAttrName}", f"{reverseNodeName}.inputX") #connects the blend attribute to the reverse node 
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{rootCtrlGrp}.v") #uses the reverse output to control the FK visibility

        orientConstraint = None #initializes the orient constraint variable
        wristConnections = mc.listConnections(endJnt) #lists all connectionts to the end joint
        for connection in wristConnections: #looping through the connection list
            if mc.objectType(connection) == "orientConstraint": #checking if it is an orient constraint
                orientConstraint = connection # if it is, it gets stored
                break
        mc.connectAttr(f"{ikFkBlendController}.{ikFkBlendAttrName}", f"{orientConstraint}.{endIKCtrl}W1") #connects the ik weighting
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{orientConstraint}.{endCtrl}W0") #connects the fk weighting
        topGrpName = f"{self.nameBase}_rig_grp" #sets a name for the top level group
        mc.group(n=topGrpName, empty=True) #creates an empty group

        mc.parent(rootCtrlGrp, topGrpName) #parents the fk controls to the top group
        mc.parent(ikFkBlendCtrlControllerGrp, topGrpName) #parents the blend control group
        mc.parent(endIKCtrlGrp, topGrpName) #parents the ik controller group
        mc.parent(poleVectorCtrlGrpName, topGrpName) #parents the pole vector group

        mc.setAttr(f"{topGrpName}.overrideEnabled", 1) #enables color override
        mc.setAttr(f"{topGrpName}.overrideRGBColors", 1) #sets it to use the rgb color mode

        mc.setAttr(f"{topGrpName}.overrideColorR", self.controllerColorRGB[0]) #sets the red color channel
        mc.setAttr(f"{topGrpName}.overrideColorG", self.controllerColorRGB[1]) #sets the green color channel
        mc.setAttr(f"{topGrpName}.overrideColorB", self.controllerColorRGB[2]) #sets the blue color channel

class LimbRiggerWidget(MayaWidget):

    def __init__(self):
        super().__init__() #initializes the parent widget
        self.setWindowTitle("Limb Rigger") #sets the title of the window
        self.rigger = LimbRigger() #creates the instance of the limbrigger
        self.masterLayout = QVBoxLayout() #the main vertical layout
        self.setLayout(self.masterLayout) #assigns the layout to the widget
        self.controlColorRGB = [0,0,0] #stores the selected color

        self.masterLayout.addWidget(QLabel("Select the 3 joints of the limb, from base to end, and then: ")) #the instructions that get displayed to the user
        self.infoLayout = QHBoxLayout() #horizontal input layout
        self.masterLayout.addLayout(self.infoLayout) #adds to the main layout
        self.infoLayout.addWidget(QLabel("Name Base:")) #the label the user sees for the name input

        self.nameBaseLineEdit = QLineEdit() #a text input box
        self.infoLayout.addWidget(self.nameBaseLineEdit) #adds to the main layout

        self.setNameBaseBtn = QPushButton("Set Name Base") #the button the user sees to set the name base
        self.setNameBaseBtn.clicked.connect(self.SetNameBaseBtnClicked) #connects the name base button to its function
        self.infoLayout.addWidget(self.setNameBaseBtn) #adds the button to the layout

        self.masterLayout.addWidget(QLabel("Base Color:")) #the label the user sees for color section

        self.controlColorBtn = QPushButton("Select Color") #the button the user sees to open the color choice dialog window
        self.controlColorBtn.clicked.connect(self.controlColorBtnClicked) #connects the button to the rigging function
        self.masterLayout.addWidget (self.controlColorBtn) #adds the button to the layout

        self.rigLimbBtn = QPushButton("Rig Limb") #the button the user sees that activates the rigging
        self.rigLimbBtn.clicked.connect(self.RigLimbBtnClicked) #connects to the rigging function
        self.masterLayout.addWidget(self.rigLimbBtn) #adds the button to the layout

    def controlColorBtnClicked(self):
        pickedColor = QColorDialog().getColor() #opens the color choice dialog
        self.rigger.controllerColorRGB[0] = pickedColor.redF() #stores the RGB value of red
        self.rigger.controllerColorRGB[1] = pickedColor.greenF() #stores the RGB value of green
        self.rigger.controllerColorRGB[2] = pickedColor.blueF() #stores the RGB value of blue
        print(self.rigger.controllerColorRGB) #prints the selected color

    def SetNameBaseBtnClicked(self):
        self.rigger.SetNameBase(self.nameBaseLineEdit.text()) #passes the text input to the rigger

    def RigLimbBtnClicked(self):
        self.rigger.RigLimb() #activates the rigging process


    def GetWidgetHash(self):
        return "4067fcd8bf8e146af389a6de3aff0f88f88668684ed0aa0944d96e6b3b94b3e8" #returns the unique identifier

def Run():
    limbRiggerWidget = LimbRiggerWidget() #creates the widget instance
    limbRiggerWidget.show() #displays the ui window

Run() #runs the tool

#run alt+shift+m