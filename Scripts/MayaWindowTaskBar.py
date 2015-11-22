# -*- coding: utf-8 -*-

'''
**********************
MayaWindowTaskBar
Rev.4
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
import mutex

import maya.cmds
import maya.mel
import maya.OpenMayaUI as OpenMayaUI

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import *
import shiboken


#-----------------------------------------------
def menuSeparator( p ):
	s = QAction( p )
	s.setSeparator( True )
	return s

#-----------------------------------------------
#Setting
#-----------------------------------------------
class Setting( object ):
	buttonSz = [ 36, 20 ]
	buttonFontSz = 7
	contextFontSz = 9
	buttonColor = [ 0.3, 0.3, 0.3 ]
	activeButtonColor = [ 0.5, 0.5, 0.5 ]
	fontColor = [ 1.0, 1.0, 1.0 ]
	sleepTime = 0.2
	
	#-----------------------------------------------
	def __init__( self ):
		pass

	#-----------------------------------------------
	@staticmethod
	def loadFromMaya( ):
		if( maya.cmds.optionVar( exists = 'MayaWindowTaskBar_buttonSzX' ) ):
			Setting.buttonSz[0] = maya.cmds.optionVar( query = 'MayaWindowTaskBar_buttonSzX' )
			
		if( maya.cmds.optionVar( exists = 'MayaWindowTaskBar_buttonSzY' ) ):
			Setting.buttonSz[1] = maya.cmds.optionVar( query = 'MayaWindowTaskBar_buttonSzY' )
			
		if( maya.cmds.optionVar( exists = 'MayaWindowTaskBar_buttonFontSz' ) ):
			Setting.buttonFontSz = maya.cmds.optionVar( query = 'MayaWindowTaskBar_buttonFontSz' )
			
		if( maya.cmds.optionVar( exists = 'MayaWindowTaskBar_contextFontSz' ) ):
			Setting.contextFontSz = maya.cmds.optionVar( query = 'MayaWindowTaskBar_contextFontSz' )

		if( maya.cmds.optionVar( exists = 'MayaWindowTaskBar_BR' ) ):
			Setting.buttonColor[0] = maya.cmds.optionVar( query = 'MayaWindowTaskBar_BR' )
		if( maya.cmds.optionVar( exists = 'MayaWindowTaskBar_BG' ) ):
			Setting.buttonColor[1] = maya.cmds.optionVar( query = 'MayaWindowTaskBar_BG' )
		if( maya.cmds.optionVar( exists = 'MayaWindowTaskBar_BB' ) ):
			Setting.buttonColor[2] = maya.cmds.optionVar( query = 'MayaWindowTaskBar_BB' )
			
		if( maya.cmds.optionVar( exists = 'MayaWindowTaskBar_AR' ) ):
			Setting.activeButtonColor[0] = maya.cmds.optionVar( query = 'MayaWindowTaskBar_AR' )
		if( maya.cmds.optionVar( exists = 'MayaWindowTaskBar_AG' ) ):
			Setting.activeButtonColor[1] = maya.cmds.optionVar( query = 'MayaWindowTaskBar_AG' )
		if( maya.cmds.optionVar( exists = 'MayaWindowTaskBar_AB' ) ):
			Setting.activeButtonColor[2] = maya.cmds.optionVar( query = 'MayaWindowTaskBar_AB' )
			
		if( maya.cmds.optionVar( exists = 'MayaWindowTaskBar_FR' ) ):
			Setting.fontColor[0] = maya.cmds.optionVar( query = 'MayaWindowTaskBar_FR' )
		if( maya.cmds.optionVar( exists = 'MayaWindowTaskBar_FG' ) ):
			Setting.fontColor[1] = maya.cmds.optionVar( query = 'MayaWindowTaskBar_FG' )
		if( maya.cmds.optionVar( exists = 'MayaWindowTaskBar_FB' ) ):
			Setting.fontColor[2] = maya.cmds.optionVar( query = 'MayaWindowTaskBar_FB' )
			
		if( maya.cmds.optionVar( exists = 'MayaWindowTaskBar_sleep' ) ):
			Setting.sleepTime = maya.cmds.optionVar( query = 'MayaWindowTaskBar_sleep' )
			
			
	#-----------------------------------------------
	@staticmethod
	def saveToMaya( ):
		maya.cmds.optionVar( intValue = ( 'MayaWindowTaskBar_buttonSzX', Setting.buttonSz[0] ) )
		maya.cmds.optionVar( intValue = ( 'MayaWindowTaskBar_buttonSzY', Setting.buttonSz[1] ) )
		maya.cmds.optionVar( intValue = ( 'MayaWindowTaskBar_buttonFontSz', Setting.buttonFontSz ) )
		maya.cmds.optionVar( intValue = ( 'MayaWindowTaskBar_contextFontSz', Setting.contextFontSz ) )

		maya.cmds.optionVar( floatValue = ( 'MayaWindowTaskBar_BR', Setting.buttonColor[0] ) )
		maya.cmds.optionVar( floatValue = ( 'MayaWindowTaskBar_BG', Setting.buttonColor[1] ) )
		maya.cmds.optionVar( floatValue = ( 'MayaWindowTaskBar_BB', Setting.buttonColor[2] ) )
		
		maya.cmds.optionVar( floatValue = ( 'MayaWindowTaskBar_AR', Setting.activeButtonColor[0] ) )
		maya.cmds.optionVar( floatValue = ( 'MayaWindowTaskBar_AG', Setting.activeButtonColor[1] ) )
		maya.cmds.optionVar( floatValue = ( 'MayaWindowTaskBar_AB', Setting.activeButtonColor[2] ) )
		
		maya.cmds.optionVar( floatValue = ( 'MayaWindowTaskBar_FR', Setting.fontColor[0] ) )
		maya.cmds.optionVar( floatValue = ( 'MayaWindowTaskBar_FG', Setting.fontColor[1] ) )
		maya.cmds.optionVar( floatValue = ( 'MayaWindowTaskBar_FB', Setting.fontColor[2] ) )
		
		maya.cmds.optionVar( floatValue = ( 'MayaWindowTaskBar_sleep', Setting.sleepTime ) )


#-----------------------------------------------
#SettingGUI
#-----------------------------------------------
class SettingGUI( QWidget ):
	instance = None

	#-----------------------------------------------
	def __new__( cls, *argc, **argv ):
		if( SettingGUI.instance != None ):
			return None
		SettingGUI.instance = QWidget.__new__( cls )
		return SettingGUI.instance
	
	#-----------------------------------------------
	def __init__( self, p = None ):
		super( SettingGUI, self ).__init__( p )
		
		self.isFrameLess = False
		self.windowFlags = Qt.Drawer | Qt.WindowStaysOnTopHint
		if( self.isFrameLess ):
			self.windowFlags = Qt.FramelessWindowHint | Qt.Drawer | Qt.WindowStaysOnTopHint
		self.setWindowFlags( self.windowFlags )
		
		self.spinBtnX = None
		self.spinBtnY = None
		self.spinBtnFontSz = None
		self.spinCFontSz = None

		self.spinBtnColors = []
		self.spinABtnColors = []
		self.spinFontColors = []

		self.sleep = None

		self.buildLayout()
		
		self.setWindowTitle( 'MayaWindowTaskBar Setting' )
		

	#-----------------------------------------------
	def __del__( self ):
		SettingGUI.instance = None
		
	#-----------------------------------------------
	def buildLayout( self ):

		#-----------------------------------------------
		def makeSingleSpin( label, valSrc, minval = 0, maxval = 1000, step = 1 ):
			l = QHBoxLayout()
			l.addWidget( QLabel( label ) )
			item = QSpinBox( self )
			item.setValue( valSrc )
			item.setMinimum( minval )
			item.setMaximum( maxval )
			item.setSingleStep( step )
			l.addWidget( item )

			return l, item

		#-----------------------------------------------
		def makeSingleFloatSpin( label, valSrc, minval = 0.0, maxval = 1.0, step = 0.1 ):
			l = QHBoxLayout()
			l.addWidget( QLabel( label ) )
			item = QDoubleSpinBox( self )
			item.setValue( valSrc )
			item.setMinimum( minval )
			item.setMaximum( maxval )
			item.setSingleStep( step )
			l.addWidget( item )

			return l, item
		
		#-----------------------------------------------
		def makeRGBSpin( label, valSrc, minval = 0.0, maxval = 1.0, step = 0.1 ):
			l = QHBoxLayout()
			l.addWidget( QLabel( label ) )

			ret = []
			for i in range( 3 ):
				item = QDoubleSpinBox( self )
				item.setMinimum( minval )
				item.setMaximum( maxval )
				item.setSingleStep( step )
				item.setValue( valSrc[i] )
				ret.append( item )

				l.addWidget( item )

			return l, ret


		margin = QMargins( 20, 20, 20, 20 )
		
		topLayout = QVBoxLayout()
		topLayout.setSpacing( 5 )
		topLayout.setContentsMargins( margin )

		Setting.loadFromMaya()

		#Visual
		topLayout.addWidget( QLabel( 'Visual' ) )
		l, self.spinBtnX = makeSingleSpin( 'Button Width', Setting.buttonSz[0] )
		topLayout.addLayout( l )
		l, self.spinBtnY = makeSingleSpin( 'Button Height', Setting.buttonSz[1] )
		topLayout.addLayout( l )
		l, self.spinBtnFontSz = makeSingleSpin( 'Button Font Size', Setting.buttonFontSz )
		topLayout.addLayout( l )
		l, self.spinCFontSz = makeSingleSpin( 'Context Font Size', Setting.contextFontSz )
		topLayout.addLayout( l )

 		l, self.spinBtnColors = makeRGBSpin( 'Button Color', Setting.buttonColor )
		topLayout.addLayout( l )
 		l, self.spinABtnColors = makeRGBSpin( 'Active Button Color', Setting.activeButtonColor )
		topLayout.addLayout( l )
 		l, self.spinFontColors = makeRGBSpin( 'Font Color', Setting.fontColor )
		topLayout.addLayout( l )

		#system
		topLayout.addWidget( QLabel( 'System' ) )
		l, self.sleep = makeSingleFloatSpin( 'update interval', Setting.sleepTime, 0.05, 5.0, 0.1 )
		topLayout.addLayout( l )

		btn = QPushButton( 'TEST setting' )
		btn.clicked.connect( self.onTestClicked )
		topLayout.addWidget( btn )
		
		#btn
		btnLayout = QHBoxLayout()
		btn = QPushButton( 'Save' )
		btn.clicked.connect( self.onApplyClicked )
		btnLayout.addWidget( btn )
		btn = QPushButton( 'Close' )
		btn.clicked.connect( self.onCloseClicked )
		btnLayout.addWidget( btn )

		topLayout.addLayout( btnLayout )
		self.setLayout( topLayout )

	#-----------------------------------------------
	def onApplyClicked( self ):
		
		Setting.buttonSz[0] = self.spinBtnX.value()
		Setting.buttonSz[1] = self.spinBtnY.value()
		Setting.buttonFontSz = self.spinBtnFontSz.value()
		Setting.contextFontSz = self.spinCFontSz.value()
		Setting.buttonColor = [ self.spinBtnColors[0].value(), self.spinBtnColors[1].value(), self.spinBtnColors[2].value() ]
		Setting.activeButtonColor = [ self.spinABtnColors[0].value(), self.spinABtnColors[1].value(), self.spinABtnColors[2].value() ]
		Setting.fontColor = [ self.spinFontColors[0].value(), self.spinFontColors[1].value(), self.spinFontColors[2].value() ]
		Setting.sleepTime = self.sleep.value()
		
		Setting.saveToMaya()
		restart()
		self.close()

	#-----------------------------------------------
	def onTestClicked( self ):
		
		Setting.buttonSz[0] = self.spinBtnX.value()
		Setting.buttonSz[1] = self.spinBtnY.value()
		Setting.buttonFontSz = self.spinBtnFontSz.value()
		Setting.contextFontSz = self.spinCFontSz.value()
		Setting.buttonColor = [ self.spinBtnColors[0].value(), self.spinBtnColors[1].value(), self.spinBtnColors[2].value() ]
		Setting.activeButtonColor = [ self.spinABtnColors[0].value(), self.spinABtnColors[1].value(), self.spinABtnColors[2].value() ]
		Setting.fontColor = [ self.spinFontColors[0].value(), self.spinFontColors[1].value(), self.spinFontColors[2].value() ]
		Setting.sleepTime = self.sleep.value()

		restart()
		
	#-----------------------------------------------
	def onCloseClicked( self ):
		Setting.loadFromMaya()
		restart()
		self.close()
		
	#-----------------------------------------------
	def closeEvent( self, event ):
		SettingGUI.instance = None

#-----------------------------------------------
# class BtnBase
#-----------------------------------------------
class BtnBase( QPushButton ):
	#-----------------------------------------------
	def __init__( self, title ):
		super( BtnBase, self ).__init__( title )
		
		sz = QSize( Setting.buttonSz[0], Setting.buttonSz[1] )
		self.setFixedSize( sz )
		self.setStyleSheet('text-align:left; font-size:%dpt;' % Setting.buttonFontSz )
		
		self.menu = QMenu( self )
		self.menu.setStyleSheet( 'text-align:left; font-size:%dpt;' % Setting.contextFontSz )

		self.clicked.connect( self.onButtonClicked )
		self.setContextMenuPolicy( Qt.CustomContextMenu )
		self.customContextMenuRequested.connect( self.onRightButtonClicked )
		
		p = self.palette()
		p.setColor( QPalette.Button, QColor( Setting.buttonColor[0] * 255.0, Setting.buttonColor[1] * 255.0, Setting.buttonColor[2] * 255.0 ) )
		p.setColor( QPalette.ButtonText, QColor( Setting.fontColor[0] * 255.0, Setting.fontColor[1] * 255.0, Setting.fontColor[2] * 255.0 ) )
		self.setAutoFillBackground( True )
		self.setPalette( p )
		
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
	def isActive( self ):
		return False

	#-----------------------------------------------
	def updateColors( self ):

		p = self.palette()

		coeff = 255.0
		if( self.getWidgetInstance().isMinimized() ):
			coeff = 255.0 * 0.6
			
		if( self.isActive() ):
			p.setColor( QPalette.Button, QColor( Setting.activeButtonColor[0] * coeff, Setting.activeButtonColor[1] * coeff, Setting.activeButtonColor[2] * coeff ) )
		else:
			p.setColor( QPalette.Button, QColor( Setting.buttonColor[0] * coeff, Setting.buttonColor[1] * coeff, Setting.buttonColor[2] * coeff ) )

		p.setColor( QPalette.ButtonText, QColor( Setting.fontColor[0] * coeff, Setting.fontColor[1] * coeff, Setting.fontColor[2] * coeff ) )
		self.setAutoFillBackground( True )
		self.setPalette( p )
		
	

#-----------------------------------------------
# class BtnWindow
#-----------------------------------------------
class BtnWindow( BtnBase ):
	#-----------------------------------------------
	def __init__( self, windowName ):
		title = maya.cmds.window( windowName, query = True, title = True )
		super( BtnWindow, self ).__init__( title )

		self.menu.addAction( 'Minimize', self.onMenuMinClicked )
		self.menu.addAction( 'Restore', self.onMenuResClicked )
		self.menu.addAction( menuSeparator( self.menu ) )
		self.menu.addAction( 'Close', self.onMenuCloseClicked )
		
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
	def isActive( self ):
		return self.getWidgetInstance().isActiveWindow()

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
	def onMenuCloseClicked( self ):
		maya.cmds.deleteUI( self.windowName )
		
	#-----------------------------------------------
	def isActive( self ):
		return self.getWidgetInstance().isActiveWindow()
	
#-----------------------------------------------
# class WindowManager
#-----------------------------------------------
class WindowManager( object ):
	selfInst = None

	#-----------------------------------------------
	def __init__( self ):

		self.targetLayout = None

		if( True ):
			toolBoxFormName = maya.mel.eval( 'string $tmp = $gToolboxForm;' )
			ptrToolBoxLayout = OpenMayaUI.MQtUtil.findLayout(toolBoxFormName)
			qtToolBoxLayout = shiboken.wrapInstance( long( ptrToolBoxLayout ), QWidget )
			qtToolBoxLayoutChildren = qtToolBoxLayout.children()
			
			self.targetLayout = qtToolBoxLayoutChildren[1].children()[2].children()[1].children()[0]

		else:
			#Todo: create own dockable window here.
			pass

		self.windowLists = []
		self.dockLists = []
		self.buttons = []

		self._mainLoopThread = None
		self._loop_run = threading.Event()
		self._loop_run.clear()

		self.targetDockWindow = [ 'MayaWindow|MainAttributeEditorLayout', 'MayaWindow|MainToolSettingsLayout', 'MayaWindow|MainChannelsLayersLayout' ]

		self.controlButton = self.buildControlButtons()



	#-----------------------------------------------
	def buildControlButtons( self ):

		if( self.targetLayout is None ):
			return
		
		newBtn = QToolButton()
		sz = QSize( Setting.buttonSz[0], 15 )
		newBtn.setFixedSize( sz )
		
		menu = QMenu(newBtn)
		
		menu.setStyleSheet( 'text-align:left; font-size:%dpt;' % Setting.contextFontSz )
		menu.addAction( 'Minimize all', self.onMenuMinAllClicked )
		menu.addAction( 'Restore all', self.onMenuResAllClicked )
		menu.addAction( menuSeparator( menu ) )
		menu.addAction( 'Close all', self.onMenuCloseAllClicked )
		menu.addAction( menuSeparator( menu ) )
		menu.addAction( 'Open setting window', self.onSettingClicked )
		menu.addAction( 'Exit', self.onStopClicked )

		newBtn.setMenu( menu )
		newBtn.setPopupMode( QToolButton.MenuButtonPopup )
		
		self.targetLayout.addWidget( newBtn )

		return newBtn

	#-----------------------------------------------
	def removeControlButton( self ):
		if( self.targetLayout is None ):
			return
		
		if( self.controlButton is not None ):
			self.targetLayout.removeWidget( self.controlButton )
			self.controlButton.deleteLater()
			self.controlButton = None
	
	#-----------------------------------------------
	def onMenuCloseAllClicked( self ):
		for w in self.windowLists:
			maya.cmds.deleteUI( w )
	
	#-----------------------------------------------
	def onMenuMinAllClicked( self ):
		for w in self.windowLists:
			p = OpenMayaUI.MQtUtil.findWindow( w )
			i = shiboken.wrapInstance( long( p ), QWidget )
			i.showMinimized()
	
	#-----------------------------------------------
	def onMenuResAllClicked( self ):
		for w in self.windowLists:
			p = OpenMayaUI.MQtUtil.findWindow( w )
			i = shiboken.wrapInstance( long( p ), QWidget )
			i.showNormal()
	
	#-----------------------------------------------
	def onSettingClicked( self ):
		self.showSettingGUI()

	#-----------------------------------------------
	def onStopClicked( self ):
		stop()
		
	#-----------------------------------------------
	def showSettingGUI( self ):
		settingUI = SettingGUI( )
		if( settingUI is not None ):
			settingUI.show()
			
	#-----------------------------------------------
	def buildWindowButtons( self ):

		if( self.targetLayout is None ):
			return
		
		for w in self.windowLists:
			newBtn = BtnWindow( w )
			self.buttons.append( newBtn )
			self.targetLayout.addWidget( newBtn )
	
	#-----------------------------------------------
	def buildDockLayoutButtons( self ):

		if( self.targetLayout is None ):
			return
		
		for w in self.dockLists:
			newBtn = BtnLayout( w )
			self.buttons.append( newBtn )
			self.targetLayout.addWidget( newBtn )
			
	#-----------------------------------------------
	def removeWindowButtons( self ):
		
		if( self.targetLayout is None ):
			return
		
		for item in self.buttons:
			self.targetLayout.removeWidget( item )
			item.deleteLater()

		self.buttons = []

	#-----------------------------------------------
	def cleanupButtons( self ):
		
		if( self.targetLayout is None ):
			return
		
		for item in self.buttons:
			self.targetLayout.removeWidget( item )
			item.deleteLater()
			
		if( self.controlButton is not None ):
			self.targetLayout.removeWidget( self.controlButton )
			self.controlButton.deleteLater()
			
		self.controlButton = None
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
			#wList.remove( 'MayaWindowTaskBar' )
		except:
			pass
		
		try:
			#fix for Maya2015
			wList.remove( 'nexFloatWindow' )
		except:
			pass

		if( cmpArray( wList, self.windowLists ) and cmpArray( dList, self.dockLists ) ):
			self.updateButtonColors()
			return
			
		self.removeWindowButtons()
		self.windowLists = wList
		self.dockLists = dList

		self.buildDockLayoutButtons()
		self.buildWindowButtons()
		
		self.updateButtonColors()

	#-----------------------------------------------
	def updateButtonColors( self ):
		for b in self.buttons:
			b.updateColors()
		
	#-----------------------------------------------
	## startLoop
	def startLoop( self ):

		self._loop_run.set()
		if( self._mainLoopThread is None ):
			self._mainLoopThread = threading.Thread( target = self.mainLoop )
			self._mainLoopThread.start()
		
	#-----------------------------------------------
	## stopLoop
	def stopLoop( self ):
		self._loop_run.clear()

	#-----------------------------------------------
	## mainLoop
	def mainLoop( self ):
		while( self._loop_run.isSet() ):
			maya.utils.executeDeferred( self.updateButtons )
			time.sleep( Setting.sleepTime )
	
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
		maya.utils.executeInMainThreadWithResult( WindowManager.selfInst.cleanupButtons )
		WindowManager.selfInst = None

#-----------------------------------------------
# start
#-----------------------------------------------
def start():
	Setting.loadFromMaya()
	WindowManager.getManager().startLoop()

#-----------------------------------------------
# restart
#-----------------------------------------------
def restart():
	WindowManager.killManager()
	WindowManager.getManager().startLoop()
	
#-----------------------------------------------
# stop
#-----------------------------------------------
def stop():
	WindowManager.killManager()

