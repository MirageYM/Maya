import json
import sys
import os
import thread
import threading
import time

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

		self._mainLoopThread = None
		self._loop_run = True

		self.buttonSz = [ 36, 20 ]
		self.buttonFontSz = 7
		self.contextFontSz = 9

		self.controlButton = self.buildControlButtons()


	#-----------------------------------------------
	def buildControlButtons( self ):
		
		newBtn = QToolButton()
		sz = QSize( self.buttonSz[0], self.buttonSz[1] )
		newBtn.setFixedSize( sz )
		
		menu = QMenu(newBtn)
		menu.setStyleSheet( 'text-align:left; font-size:%dpt;' % self.contextFontSz )
		menu.addAction( 'minimize all', self.menuMinAllFactory() )
		menu.addAction( 'restore all', self.menuResAllFactory() )
		menu.addAction( 'close all', self.menuCloseAllFactory() )

		newBtn.setMenu( menu )
		newBtn.setPopupMode( QToolButton.MenuButtonPopup )
		
		self.targetLayout.addWidget( newBtn )

		return newBtn

	#-----------------------------------------------
	def removeControlButton( self ):
		if( self.controlButton is not None ):
			self.targetLayout.removeWidget( self.controlButton )
			self.controlButton.deleteLater()
			self.controlButton = None
	
	#-----------------------------------------------
	def menuCloseAllFactory( self ):
		def imp():
			for w in self.windowLists:
				maya.cmds.deleteUI( w )

		return imp
	
	#-----------------------------------------------
	def menuMinAllFactory( self ):
		def imp():
			for w in self.windowLists:
				p = OpenMayaUI.MQtUtil.findWindow( w )
				i = shiboken.wrapInstance( long( p ), QWidget )
				i.showMinimized()

		return imp
	
	#-----------------------------------------------
	def menuResAllFactory( self ):
		def imp():
			for w in self.windowLists:
				p = OpenMayaUI.MQtUtil.findWindow( w )
				i = shiboken.wrapInstance( long( p ), QWidget )
				i.showNormal()

		return imp
	
	#-----------------------------------------------
	def buildWindowButtons( self ):

		for w in self.windowLists:
			
			title = maya.cmds.window( w, query = True, title = True )
			newBtn = QPushButton( title )

			sz = QSize( self.buttonSz[0], self.buttonSz[1] )
			newBtn.setFixedSize( sz )
			newBtn.setStyleSheet('text-align:left; font-size:%dpt;' % self.buttonFontSz )
			
			menu = QMenu(newBtn)
			menu.setStyleSheet('text-align:left; font-size:9pt;' )
			menu.addAction( 'minimize', self.menuMinFactory(w) )
			menu.addAction( 'restore', self.menuResFactory(w) )
			menu.addAction( 'close', self.menuCloseFactory(w) )
			
			newBtn.clicked.connect( self.onButtonClickedFactory(w) )
			newBtn.setContextMenuPolicy( Qt.CustomContextMenu )
			newBtn.customContextMenuRequested.connect( self.onRightButtonClickedFactory( menu ) )
			
			self.buttons.append( newBtn )
			self.targetLayout.addWidget( newBtn )
	
	#-----------------------------------------------
	def removeWindowButtons( self ):
		for item in self.buttons:
			self.targetLayout.removeWidget( item )
			item.deleteLater()

		self.buttons = []

	#-----------------------------------------------
	def updateButtons( self ):

		wList = maya.cmds.lsUI( windows = True )
		try:
			#avoid Main window
			wList.remove( 'MayaWindow' )
			#fix for Maya2015
			wList.remove( 'nexFloatWindow' )
		except:
			pass

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
			
		self.removeWindowButtons()
		self.windowLists = wList
		
		self.buildWindowButtons()

	#-----------------------------------------------
	def onButtonClickedFactory( self, w ):
		def clickedImp():
			p = OpenMayaUI.MQtUtil.findWindow( w )
			i = shiboken.wrapInstance( long( p ), QWidget )
			i.showNormal()
			maya.cmds.setFocus( w )
		return clickedImp

	#-----------------------------------------------
	def menuCloseFactory( self, w ):
		def imp():
			maya.cmds.deleteUI( w )

		return imp
	
	#-----------------------------------------------
	def menuMinFactory( self, w ):
		def imp():
			p = OpenMayaUI.MQtUtil.findWindow( w )
			i = shiboken.wrapInstance( long( p ), QWidget )
			i.showMinimized()

		return imp
	
	#-----------------------------------------------
	def menuResFactory( self, w ):
		def imp():
			p = OpenMayaUI.MQtUtil.findWindow( w )
			i = shiboken.wrapInstance( long( p ), QWidget )
			i.showNormal()

		return imp
	
	#-----------------------------------------------
	def onRightButtonClickedFactory( self, menu ):
		def clickedImp():
			menu.popup(QCursor.pos())

		return clickedImp

	#-----------------------------------------------
	## startLoop
	def startLoop( self ):
		self._loop_run = True
		self._mainLoopThread = threading.Thread( target = self.mainLoop )
		self._mainLoopThread.start()
		
	#-----------------------------------------------
	## stopLoop
	def stopLoop( self ):
		self._loop_run = False

	#-----------------------------------------------
	## mainLoop
	def mainLoop( self ):
		while( self._loop_run ):
			maya.utils.executeInMainThreadWithResult( self.updateButtons )
			time.sleep( 0.1 )
	
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
		WindowManager.selfInst.stopLoop()
		WindowManager.selfInst.removeWindowButtons()
		WindowManager.selfInst.removeControlButton()
		WindowManager.selfInst = None

#-----------------------------------------------
def start():
	WindowManager.getManager().startLoop()

#-----------------------------------------------
def stop():
	WindowManager.killManager()

