import maya.cmds
import maya.mel
import maya.OpenMayaUI as OpenMayaUI

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import *
import shiboken


class WindowManager( object ):
	selfInst = None
	
	#-----------------------------------------------
	def __init__( self ):
		self.targetLayout = None
		
		toolBoxFormName = maya.mel.eval( 'string $tmp = $gToolboxForm;' )
		ptrToolBoxLayout = OpenMayaUI.MQtUtil.findLayout(toolBoxFormName)
		qtToolBoxLayout = shiboken.wrapInstance( long( ptrToolBoxLayout ), QWidget )
		qtToolBoxLayoutChildren = qtToolBoxLayout.children()

		self.targetLayout = qtToolBoxLayoutChildren[1].children()[2].children()[1].children()[0]

		self.windowLists = []
		self.buttons = []

		self.scriptJobId = None

	#-----------------------------------------------
	def updateButtons( self ):

		wList = maya.cmds.lsUI( windows = True )

		rebuild = False
		if( len( wList ) == len( self.windowLists ) ):
			for i in range( len( wList ) ):
				if( wList[i] != self.windowLists[i] ):
					rebuild = True
					break
		else:
			rebuild = True

		if( not rebuild ):
			return
			
		self.removeButtons()
		
		self.windowLists = wList
		for w in self.windowLists:
			#avoid Main window
			if( w == 'MayaWindow' ):
				continue

			#fix for Maya2015
			if( w == 'nexFloatWindow' ):
				continue
			
			title = maya.cmds.window( w, query = True, title = True )
			newBtn = QPushButton( title )
			#newBtn.setToolTip( title )
			sz = QSize( 32, 24 )
			newBtn.setFixedSize( sz )
			newBtn.setStyleSheet('text-align:left; font-size:6pt;' )
			newBtn.clicked.connect( self.onButtonClickedFactory(w) )
			self.buttons.append( newBtn )
			self.targetLayout.addWidget( newBtn )

	#-----------------------------------------------
	def onButtonClickedFactory( self, w ):
		def clickedImp():
			maya.cmds.setFocus( w )
		return clickedImp

	#-----------------------------------------------
	def removeButtons( self ):
		for item in self.buttons:
			self.targetLayout.removeWidget( item )
			item.deleteLater()

		self.buttons = []
		
	#-----------------------------------------------
	def onIdleEvent(self):
		self.updateButtons()

	#-----------------------------------------------
	def startScriptJob(self):
		if( self.scriptJobId is not None ):
			maya.cmds.scriptJob( k = WindowManager.selfInst.scriptJobId )
			
		self.scriptJobId = maya.cmds.scriptJob( ie = 'MayaWindowTaskBar.WindowManager.getManager().onIdleEvent()' )
	
	#-----------------------------------------------
	@staticmethod
	def getManager():
		if( WindowManager.selfInst is None ):
			WindowManager.selfInst = WindowManager()
		return WindowManager.selfInst
	

	#-----------------------------------------------
	@staticmethod
	def killManager():
		if( WindowManager.selfInst is None ):
			return
		maya.cmds.scriptJob( k = WindowManager.selfInst.scriptJobId )
		WindowManager.selfInst.removeButtons()
		WindowManager.selfInst = None

#-----------------------------------------------
def start():
	WindowManager.getManager().startScriptJob()
	

#-----------------------------------------------
def stop():
	WindowManager.killManager()

