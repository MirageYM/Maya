# -*- coding: utf-8 -*-

'''
**********************
MayaWindowTaskBar
Rev.3
**********************

License
Copyright (c) 2015, yasutoshi Mori All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1.Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
2.Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

https://github.com/MirageYM


**********************
Usage:

<<to START>>:
import MayaWindowTaskBar
MayaWindowTaskBar.start()

<<to STOP>>:
MayaWindowTaskBar.stop()

'''


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


buttonSz = [ 36, 20 ]
buttonFontSz = 7
contextFontSz = 9

#-----------------------------------------------
# class BtnBase
#-----------------------------------------------
class BtnBase( QPushButton ):
	#-----------------------------------------------
	def __init__( self, title ):
		super( BtnBase, self ).__init__( title )
		
		sz = QSize( buttonSz[0], buttonSz[1] )
		self.setFixedSize( sz )
		self.setStyleSheet('text-align:left; font-size:%dpt;' % buttonFontSz )
		
		self.menu = QMenu( self )
		self.menu.setStyleSheet( 'text-align:left; font-size:%dpt;' % contextFontSz )

		self.clicked.connect( self.onButtonClicked )
		self.setContextMenuPolicy( Qt.CustomContextMenu )
		self.customContextMenuRequested.connect( self.onRightButtonClicked )
		
	#-----------------------------------------------
	def getWidgetInstance( self ):
		return None
	
	#-----------------------------------------------
	def onButtonClicked( self ):
		pass
	
	#-----------------------------------------------
	def onRightButtonClicked( self ):
		pass


#-----------------------------------------------
# class BtnWindow
#-----------------------------------------------
class BtnWindow( BtnBase ):
	#-----------------------------------------------
	def __init__( self, windowName ):
		title = maya.cmds.window( windowName, query = True, title = True )
		super( BtnWindow, self ).__init__( title )

		self.menu.addAction( 'minimize', self.onMenuMinClicked )
		self.menu.addAction( 'restore', self.onMenuResClicked )
		self.menu.addAction( 'close', self.onMenuCloseClicked )
		
		self.windowName = windowName

	#-----------------------------------------------
	def getWidgetInstance( self ):
		p = OpenMayaUI.MQtUtil.findWindow( self.windowName )
		return shiboken.wrapInstance( long( p ), QWidget )
		
	#-----------------------------------------------
	def onMenuMinClicked( self ):
		self.getWidgetInstance().showMinimized()
		
	#-----------------------------------------------
	def onMenuResClicked( self ):
		self.getWidgetInstance().showNormal()
		
	#-----------------------------------------------
	def onMenuCloseClicked( self ):
		maya.cmds.deleteUI( self.windowName )
		
	#-----------------------------------------------
	def onButtonClicked( self ):
		self.getWidgetInstance().showNormal()
		maya.cmds.setFocus( self.windowName )
	
	#-----------------------------------------------
	def onRightButtonClicked( self ):
		self.menu.popup( QCursor.pos() )
	

#-----------------------------------------------
# class BtnLayout
#-----------------------------------------------
class BtnLayout( BtnBase ):
	#-----------------------------------------------
	def __init__( self, layoutName ):
		p = OpenMayaUI.MQtUtil.findLayout( layoutName )
		i = shiboken.wrapInstance( long( p ), QWidget )
		parent = i.parent()
		
		super( BtnLayout, self ).__init__( parent.windowTitle() )

		self.windowName = layoutName
		
	#-----------------------------------------------
	def getWidgetInstance( self ):
		p = OpenMayaUI.MQtUtil.findLayout( self.windowName )
		return shiboken.wrapInstance( long( p ), QWidget )
	
	#-----------------------------------------------
	def onButtonClicked( self ):
		self.getWidgetInstance().showNormal()
		maya.cmds.setFocus( self.windowName )

	
#-----------------------------------------------
# class WindowManager
#-----------------------------------------------
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
		self.dockLists = []
		self.buttons = []

		self._mainLoopThread = None
		self._loop_run = True

		self.targetDockWindow = [ 'MayaWindow|MainAttributeEditorLayout', 'MayaWindow|MainToolSettingsLayout', 'MayaWindow|MainChannelsLayersLayout' ]

		self.controlButton = self.buildControlButtons()

	#-----------------------------------------------
	def buildControlButtons( self ):
		
		newBtn = QToolButton()
		sz = QSize( buttonSz[0], buttonSz[1] )
		newBtn.setFixedSize( sz )
		
		menu = QMenu(newBtn)
		menu.setStyleSheet( 'text-align:left; font-size:%dpt;' % contextFontSz )
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
			newBtn = BtnWindow( w )
			self.buttons.append( newBtn )
			self.targetLayout.addWidget( newBtn )
	
	#-----------------------------------------------
	def buildDockLayoutButtons( self ):

		for w in self.dockLists:
			newBtn = BtnLayout( w )
			self.buttons.append( newBtn )
			self.targetLayout.addWidget( newBtn )
			
	#-----------------------------------------------
	def removeWindowButtons( self ):
		for item in self.buttons:
			self.targetLayout.removeWidget( item )
			item.deleteLater()

		self.buttons = []

	#-----------------------------------------------
	def isDockLayoutFloating( self, s ):
		p = OpenMayaUI.MQtUtil.findLayout( s )
		i = shiboken.wrapInstance( long( p ), QWidget )
		parent = i.parent()
		return maya.cmds.dockControl( parent.objectName(), q = True, fl = True )

	#-----------------------------------------------
	def listFloatDock( self ):
		r = []
		for s in self.targetDockWindow:
			if( self.isDockLayoutFloating( s ) ):
				r.append( s )

		return r

	#-----------------------------------------------
	def updateButtons( self ):

		def cmpArray( l, r ):
			if( len( l ) == len( r ) ):
				for i in range( len( l ) ):
					if( l[i] != r[i] ):
						return False
				return True
			else:
				return False

		wList = maya.cmds.lsUI( windows = True )
		dList = self.listFloatDock()
		
		try:
			#avoid Main window
			wList.remove( 'MayaWindow' )
			#fix for Maya2015
			wList.remove( 'nexFloatWindow' )
		except:
			pass

		if( cmpArray( wList, self.windowLists ) and cmpArray( dList, self.dockLists ) ):
			return
			
		self.removeWindowButtons()
		self.windowLists = wList
		self.dockLists = dList

		self.buildDockLayoutButtons()
		self.buildWindowButtons()

	#-----------------------------------------------
	## startLoop
	def startLoop( self ):
		self._loop_run = True
		if( self._mainLoopThread is None ):
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
# start
#-----------------------------------------------
def start():
	WindowManager.getManager().startLoop()

#-----------------------------------------------
# stop
#-----------------------------------------------
def stop():
	WindowManager.killManager()

