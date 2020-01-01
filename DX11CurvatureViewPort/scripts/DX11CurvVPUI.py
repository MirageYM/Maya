# -*- coding: utf-8 -*-

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

if( maya.cmds.about( api = True ) >= 201700 ):
	from PySide2.QtWidgets import *
	from PySide2.QtCore import *
	from PySide2.QtGui import *
	from PySide2.QtUiTools import *
	import shiboken2 as shiboken

else:
	from PySide.QtCore import *
	from PySide.QtGui import *
	from PySide.QtUiTools import *
	import shiboken


#-----------------------------------------------
def menuSeparator( p ):
	s = QAction( p )
	s.setSeparator( True )
	return s

#=========================================
#Setting
#=========================================
class SettingBase( object ):
	#-----------------------------------------------
	def __init__( self ):
		pass

	#-----------------------------------------------
	def getPrefix( self ):
		return None

	#-----------------------------------------------
	def loadFromMaya( self ):
		for k, v in self.__dict__.items():
			p = self.getPrefix() + k
			if( maya.cmds.optionVar( exists = p ) ):
				self.__dict__[ k ] = maya.cmds.optionVar( query = p )
			
	#-----------------------------------------------
	def saveToMaya( self ):
		for k, v in self.__dict__.items():
			p = self.getPrefix() + k
			if( type( self.__dict__[ k ] ) is int ):
				maya.cmds.optionVar( intValue = ( p, v ) )
			elif( type( self.__dict__[ k ] ) is float ):
				maya.cmds.optionVar( floatValue = ( p, v ) )
			elif( type( self.__dict__[ k ] ) is str ):
				maya.cmds.optionVar( stringValue = ( p, v ) )
			elif( type( self.__dict__[ k ] ) is unicode ):
				maya.cmds.optionVar( stringValue = ( p, v ) )

	#-----------------------------------------------
	def delFromMaya( self ):
		for k, v in self.__dict__.items():
			p = self.getPrefix() + k
			maya.cmds.optionVar( rm = p )
			
#-----------------------------------------------
#Setting
#-----------------------------------------------
class Setting( SettingBase ):
	
	#-----------------------------------------------
	def __init__( self ):
		super( Setting, self ).__init__()
		
		self.valPower = 0.5
		self.valMult = 2.0
		self.gridDistX = 0.1
		self.gridDistY = 0.1
		self.gridDistZ = 0.1
		self.gridOffsetX = 0.0
		self.gridOffsetY = 0.0
		self.gridOffsetZ = 0.0
		self.gridWidthX = 0.001
		self.gridWidthY = 0.001
		self.gridWidthZ = 0.001
		self.gridAlpha = 0.1
		self.checkerAlpha = 0.9
		self.checkerRepeat = 10.0
		self.ambient = 0.5
		self.colorMidR = 1.0
		self.colorMidG = 1.0
		self.colorMidB = 1.0
		self.colorPosR = 1.0
		self.colorPosG = 0.0
		self.colorPosB = 0.0
		self.colorNegR = 0.0
		self.colorNegG = 0.0
		self.colorNegB = 1.0
		self.depthLimit = 0.01

	#-----------------------------------------------
	def getPrefix( self ):
		return 'DX11CurvVPSetting'
	
#-----------------------------------------------
#SettingGUI
#-----------------------------------------------
class SettingGUI( QWidget ):
	instance = None
	
	#-----------------------------------------------
	def __init__( self, p = None ):
		super( SettingGUI, self ).__init__( p )
		self.setting = Setting()
		self.setting.loadFromMaya()
		
		self.isFrameLess = False
		self.windowFlags = Qt.Drawer | Qt.WindowStaysOnTopHint
		if( self.isFrameLess ):
			self.windowFlags = Qt.FramelessWindowHint | Qt.Drawer | Qt.WindowStaysOnTopHint
		self.setWindowFlags( self.windowFlags )

		self.valWidget = []

		self.buildLayout()
		
		self.setWindowTitle( 'DX11CurvVP Setting' )

	#-----------------------------------------------
	def __del__( self ):
		SettingGUI.instance = None

	@staticmethod
	def getInstance():
		if( SettingGUI.instance is None ):
			SettingGUI.instance = SettingGUI()
		return SettingGUI.instance

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
		def makeSingleFloatSpin( label, valSrc, minval = 0.0, maxval = 1.0, step = 0.1, decimal = 3 ):
			l = QHBoxLayout()
			l.addWidget( QLabel( label ) )
			item = QDoubleSpinBox( self )
			item.setValue( valSrc )
			item.setMinimum( minval )
			item.setMaximum( maxval )
			item.setSingleStep( step )
			item.setDecimals( decimal )
			l.addWidget( item )

			return l, item
		
		#-----------------------------------------------
		def makeFloatSlider( label, valSrc, minval = 0.0, maxval = 1.0, step = 0.1, decimal = 3, sliderScale = 0.01 ):
			l = QHBoxLayout()
			l.addWidget( QLabel( label ) )

			slider = QSlider( self )
			spin = QDoubleSpinBox( self )

			l.addWidget( slider )
			l.addWidget( spin )

			spin.setValue( valSrc )
			spin.setRange( minval, maxval )
			spin.setSingleStep( step )
			spin.setDecimals( decimal )

			slider.setValue( ( valSrc - minval ) / ( ( maxval - minval ) * sliderScale )  )
			slider.setRange( 0, 100 )
			slider.setOrientation( Qt.Horizontal )

			slider.valueChanged.connect( lambda: spin.setValue( slider.value() * ( maxval - minval ) * sliderScale + minval ) )


			return l, [ slider, spin ]
		
		#-----------------------------------------------
		def makeRGBSpin( label, valSrc, minval = 0.0, maxval = 1.0, step = 0.1, decimal = 3 ):
			l = QHBoxLayout()
			l.addWidget( QLabel( label ) )

			ret = []
			for i in range( 3 ):
				item = QDoubleSpinBox( self )
				item.setMinimum( minval )
				item.setMaximum( maxval )
				item.setSingleStep( step )
				item.setDecimals( decimal )
				item.setValue( valSrc[i] )
				ret.append( item )

				l.addWidget( item )

			return l, ret


		margin = QMargins( 20, 20, 20, 20 )
		
		topLayout = QVBoxLayout()
		topLayout.setSpacing( 5 )
		topLayout.setContentsMargins( margin )

		#Evalution

		#Value
		topLayout.addWidget( QLabel( 'K Value Vusalize' ) )
		self.valWidget.append( makeFloatSlider( 'Value Power', self.setting.valPower, 0.001, 100.0, 0.1, 4, 0.001 ) )
		topLayout.addLayout( self.valWidget[-1][0] )
		self.valWidget[-1][1][1].valueChanged.connect( self.onApplyClicked )
		self.valWidget.append( makeFloatSlider( 'Value Multiply', self.setting.valMult, 0.0001, 100.0, 0.1, 4, 0.001 ) )
		topLayout.addLayout( self.valWidget[-1][0] )
		self.valWidget[-1][1][1].valueChanged.connect( self.onApplyClicked )

		#Grid
		topLayout.addWidget( QLabel( 'Grid' ) )
		self.valWidget.append( makeRGBSpin( 'Grid Width', [ self.setting.gridWidthX, self.setting.gridWidthY, self.setting.gridWidthZ ],  0.0001, 100000.0, 0.01, 5 ) )
		topLayout.addLayout( self.valWidget[-1][0] )
		self.valWidget[-1][1][0].valueChanged.connect( self.onApplyClicked )
		self.valWidget[-1][1][1].valueChanged.connect( self.onApplyClicked )
		self.valWidget[-1][1][2].valueChanged.connect( self.onApplyClicked )
		self.valWidget.append( makeRGBSpin( 'Grid Dist', [ self.setting.gridDistX, self.setting.gridDistY, self.setting.gridDistZ ], 0.00001, 1000000.0, 0.01, 5 ) )
		topLayout.addLayout( self.valWidget[-1][0] )
		self.valWidget[-1][1][0].valueChanged.connect( self.onApplyClicked )
		self.valWidget[-1][1][1].valueChanged.connect( self.onApplyClicked )
		self.valWidget[-1][1][2].valueChanged.connect( self.onApplyClicked )
		self.valWidget.append( makeRGBSpin( 'Grid Offset', [ self.setting.gridOffsetX, self.setting.gridOffsetY, self.setting.gridOffsetZ ], -1000000.0, 1000000.0, 0.01, 5 ) )
		topLayout.addLayout( self.valWidget[-1][0] )
		self.valWidget[-1][1][0].valueChanged.connect( self.onApplyClicked )
		self.valWidget[-1][1][1].valueChanged.connect( self.onApplyClicked )
		self.valWidget[-1][1][2].valueChanged.connect( self.onApplyClicked )

		self.valWidget.append( makeFloatSlider( 'Grid Transparency', self.setting.gridAlpha, 0.0, 1.0, 0.1, 3 ) )
		topLayout.addLayout( self.valWidget[-1][0] )
		self.valWidget[-1][1][1].valueChanged.connect( self.onApplyClicked )
		self.valWidget.append( makeFloatSlider( 'Checker Transparency', self.setting.checkerAlpha, 0.0, 1.0, 0.1, 3 ) )
		topLayout.addLayout( self.valWidget[-1][0] )
		self.valWidget[-1][1][1].valueChanged.connect( self.onApplyClicked )
		self.valWidget.append( makeFloatSlider( 'Checker Repeat', self.setting.checkerRepeat, 0.0, 1000.0, 1.0, 3 ) )
		topLayout.addLayout( self.valWidget[-1][0] )
		self.valWidget[-1][1][1].valueChanged.connect( self.onApplyClicked )
		self.valWidget.append( makeFloatSlider( 'Shading Ambient', self.setting.ambient, 0.0, 1.0, 1.0, 3 ) )
		topLayout.addLayout( self.valWidget[-1][0] )
		self.valWidget[-1][1][1].valueChanged.connect( self.onApplyClicked )
		
		self.valWidget.append( makeRGBSpin( 'Color Flat', [ self.setting.colorMidR, self.setting.colorMidG, self.setting.colorMidB ], 0.0, 1.0, 0.1, 3 ) )
		topLayout.addLayout( self.valWidget[-1][0] )
		self.valWidget[-1][1][0].valueChanged.connect( self.onApplyClicked )
		self.valWidget[-1][1][1].valueChanged.connect( self.onApplyClicked )
		self.valWidget[-1][1][2].valueChanged.connect( self.onApplyClicked )
		
		self.valWidget.append( makeRGBSpin( 'Color Positive', [ self.setting.colorPosR, self.setting.colorPosG, self.setting.colorPosB ], 0.0, 1.0, 0.1, 3 ) )
		topLayout.addLayout( self.valWidget[-1][0] )
		self.valWidget[-1][1][0].valueChanged.connect( self.onApplyClicked )
		self.valWidget[-1][1][1].valueChanged.connect( self.onApplyClicked )
		self.valWidget[-1][1][2].valueChanged.connect( self.onApplyClicked )
		
		self.valWidget.append( makeRGBSpin( 'Color Negative', [ self.setting.colorNegR, self.setting.colorNegG, self.setting.colorNegB ], 0.0, 1.0, 0.1, 3 ) )
		topLayout.addLayout( self.valWidget[-1][0] )
		self.valWidget[-1][1][0].valueChanged.connect( self.onApplyClicked )
		self.valWidget[-1][1][1].valueChanged.connect( self.onApplyClicked )
		self.valWidget[-1][1][2].valueChanged.connect( self.onApplyClicked )
		
		self.valWidget.append( makeFloatSlider( 'Depth Limit', self.setting.depthLimit, 0.00001, 0.1, 0.001, 6, 0.01 ) )
		topLayout.addLayout( self.valWidget[-1][0] )
		self.valWidget[-1][1][1].valueChanged.connect( self.onApplyClicked )

		
		#btn
		btnLayout = QHBoxLayout()
		btn = QPushButton( 'Apply' )
		btn.clicked.connect( self.onApplyClicked )
		btnLayout.addWidget( btn )
		btn = QPushButton( 'Close' )
		btn.clicked.connect( self.onCloseClicked )
		btnLayout.addWidget( btn )

		topLayout.addLayout( btnLayout )
		self.setLayout( topLayout )

	#-----------------------------------------------
	def onApplyClicked( self ):
		
		self.setting.valPower = self.valWidget[0][1][1].value()
		self.setting.valMult = self.valWidget[1][1][1].value()
		self.setting.gridWidthX = self.valWidget[2][1][0].value()
		self.setting.gridWidthY = self.valWidget[2][1][1].value()
		self.setting.gridWidthZ = self.valWidget[2][1][2].value()
		self.setting.gridDistX = self.valWidget[3][1][0].value()
		self.setting.gridDistY = self.valWidget[3][1][1].value()
		self.setting.gridDistZ = self.valWidget[3][1][2].value()
		self.setting.gridOffsetX = self.valWidget[4][1][0].value()
		self.setting.gridOffsetY = self.valWidget[4][1][1].value()
		self.setting.gridOffsetZ = self.valWidget[4][1][2].value()
		self.setting.gridAlpha = self.valWidget[5][1][1].value()
		self.setting.checkerAlpha = self.valWidget[6][1][1].value()
		self.setting.checkerRepeat = self.valWidget[7][1][1].value()
		self.setting.ambient = self.valWidget[8][1][1].value()
		self.setting.colorMidR = self.valWidget[9][1][0].value()
		self.setting.colorMidG = self.valWidget[9][1][1].value()
		self.setting.colorMidB = self.valWidget[9][1][2].value()
		self.setting.colorPosR = self.valWidget[10][1][0].value()
		self.setting.colorPosG = self.valWidget[10][1][1].value()
		self.setting.colorPosB = self.valWidget[10][1][2].value()
		self.setting.colorNegR = self.valWidget[11][1][0].value()
		self.setting.colorNegG = self.valWidget[11][1][1].value()
		self.setting.colorNegB = self.valWidget[11][1][2].value()
		self.setting.depthLimit = self.valWidget[12][1][1].value()
		
		self.setting.saveToMaya()
		maya.cmds.DX11CurvViewPortControl( vm = self.setting.valMult, 
										 vp = self.setting.valPower,
										 gox = self.setting.gridOffsetX,
										 goy = self.setting.gridOffsetY,
										 goz = self.setting.gridOffsetZ,
										 gdx = self.setting.gridDistX,
										 gdy = self.setting.gridDistY,
										 gdz = self.setting.gridDistZ,
										 gwx = self.setting.gridWidthX,
										 gwy = self.setting.gridWidthY,
										 gwz = self.setting.gridWidthZ,
										 ga = self.setting.gridAlpha,
										 ca = self.setting.checkerAlpha,
										 cr = self.setting.checkerRepeat,
										 amb = self.setting.ambient,
										 cmr = self.setting.colorMidR,
										 cmg = self.setting.colorMidG,
										 cmb = self.setting.colorMidB,
										 cpr = self.setting.colorPosR,
										 cpg = self.setting.colorPosG,
										 cpb = self.setting.colorPosB,
										 cnr = self.setting.colorNegR,
										 cng = self.setting.colorNegG,
										 cnb = self.setting.colorNegB,
										 dl = self.setting.depthLimit,
									  )
		maya.cmds.refresh( f = True )

	#-----------------------------------------------
	def onCloseClicked( self ):
		self.close()
		
	#-----------------------------------------------
	def closeEvent( self, event ):
		SettingGUI.instance = None

def show():
	settingUI = SettingGUI.getInstance()
	settingUI.show()
