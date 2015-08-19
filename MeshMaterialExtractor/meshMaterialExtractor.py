# -*- coding: utf-8 -*-

import sys
import math
import os
import copy

from maya.OpenMaya import *
from maya.OpenMayaMPx import *
from maya.OpenMayaUI import *
import maya.cmds

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import *
import shiboken

kCmdName = "MeshMaterialExtractor"

#-----------------------------------------------
#SelGUI
#-----------------------------------------------
class SelGUI( QWidget ):

	#-----------------------------------------------
	def __init__( self, extractorInstance, p = None ):
		QWidget.__init__( self, p )
		self.extractorInstance = extractorInstance

		self.isFrameLess = False
		self.windowFlags = Qt.Drawer | Qt.WindowStaysOnTopHint
		if( self.isFrameLess ):
			self.windowFlags = Qt.FramelessWindowHint | Qt.Drawer | Qt.WindowStaysOnTopHint
		self.setWindowFlags( self.windowFlags )
		self.listView = None
		self.listModel = None

		self.buildLayout()

	#-----------------------------------------------
	def buildLayout( self ):

		margin = QMargins( 10, 10, 10, 10 )
		
		topLayout = QVBoxLayout()
		topLayout.setSpacing(3)
		topLayout.setContentsMargins( margin )

		#listView
		self.listView = QListView()
		self.listModel = QStandardItemModel( self.listView )
		topLayout.addWidget( self.listView )
		
		#btn
		btnLayout = QHBoxLayout()
		btn = QPushButton( 'Extract' )
		btn.clicked.connect( self.onClick_Extract )
		btnLayout.addWidget( btn )
		btn = QPushButton( 'Cancel' )
		btn.clicked.connect( self.onClick_Cancel )
		btnLayout.addWidget( btn )

		topLayout.addLayout( btnLayout )
		self.setLayout( topLayout )

	#-----------------------------------------------
	def addSGName( self, n ):
		
		i = QStandardItem()
		i.setText( n )
		i.setCheckable( True )
		i.setBackground( QBrush( QColor( 100, 100, 100 ) ) )
		
		self.listModel.appendRow( i )
		self.listView.setModel( self.listModel )

	#-----------------------------------------------
	def onClick_Extract( self ):
		for i in range( self.listModel.rowCount() ):
			item = self.listModel.item( i )
			s = int( item.checkState() )

			if( s ):
				self.extractorInstance.extractFaceBySGName( item.text() )


	#-----------------------------------------------
	def onClick_Cancel( self ):
		self.close()

#-----------------------------------------------
#Single Extractor
#-----------------------------------------------
class ExtractorColt1911( object ):

	ui = None
	
	#-----------------------------------------------
	def __init__( self, nodeObj ):
		self.__debug = False
		self.nodeObjHdl = MObjectHandle( nodeObj )
		self.useGUI = True
		ExtractorColt1911.ui = None

	#-----------------------------------------------
	def fire( self ):
		fnMesh = MFnMesh( self.nodeObjHdl.object() )

		vtxCount = MIntArray()
		vtxList = MIntArray()
		fnMesh.getVertices( vtxCount, vtxList )
		
		shaderObjs = MObjectArray()
		shaderIndices = MIntArray()
		fnMesh.getConnectedShaders( 0, shaderObjs, shaderIndices )
		if( shaderObjs.length() < 1 ):
			return

		if( self.useGUI ):
			ExtractorColt1911.ui = SelGUI( self )
			for i in range( shaderObjs.length() ):
				ExtractorColt1911.ui.addSGName( MFnDependencyNode( shaderObjs[i] ).name() )

			ExtractorColt1911.ui.show()
			
		else:
			for i in range( shaderObjs.length() ):
				self.extractFaceByShaderIndex( i )

	#-----------------------------------------------
	def extractFaceBySGName( self, name ):
		nodeObj = self.nodeObjHdl.object()
		fnMesh = MFnMesh( nodeObj )
		#get shaders
		shaderObjs = MObjectArray()
		shaderIndices = MIntArray()
		fnMesh.getConnectedShaders( 0, shaderObjs, shaderIndices )

		for i in range( shaderObjs.length() ):
			sg = shaderObjs[i]
			if( MFnDependencyNode( sg ).name() == name ):
				self.extractFaceByShaderIndex( i )
				break
		
	#-----------------------------------------------
	def extractFaceByShaderIndex( self, index ):
		nodeObj = self.nodeObjHdl.object()
		fnMesh = MFnMesh( nodeObj )

		#get src face and vertices
		vtxCount = MIntArray()
		vtxList = MIntArray()
		fnMesh.getVertices( vtxCount, vtxList )

		vtxArray = MFloatPointArray()
		fnMesh.getPoints( vtxArray )

		nmlArray = MFloatVectorArray()
		fnMesh.getNormals( nmlArray )
		nmlCount = MIntArray()
		nmlIds = MIntArray()
		fnMesh.getNormalIds( nmlCount, nmlIds )
		

		#get shaders
		shaderObjs = MObjectArray()
		shaderIndices = MIntArray()
		fnMesh.getConnectedShaders( 0, shaderObjs, shaderIndices )

		shaderObj = shaderObjs[index]
		fnShader = MFnDependencyNode( shaderObj )

		print( '=================================' )
		print( 'extract target/ index:%d / name:%s' % ( index, fnShader.name() ) )

		#dst face and vertices for new mesh
		newVtxCount = MIntArray()
		newVtxList = MIntArray()
		newVtxArray = MFloatPointArray()
		newNmlFaceList = MIntArray()
		newNmlVtxList = MIntArray()
		newNmlArray = MVectorArray()


		#vertex-point index map for shared point
		srcToNewVtxMap = {}
		srcToNewNmlMap = {}

		#accumulator for vtx count
		vtxItr = 0
		
		for faceCnt in range( vtxCount.length() ):
			currentVtxCnt = vtxCount[ faceCnt ]
			currentNmlCnt = nmlCount[ faceCnt ]

			#only target SG
			if( shaderIndices[ faceCnt ] == index ):
				newVtxCount.append( currentVtxCnt )

				#copy per face vertex
				for vtxCnt in range( currentVtxCnt ):
					vtxIndex = vtxItr + vtxCnt
					pointIndex = vtxList[ vtxIndex ]

					if( pointIndex not in srcToNewVtxMap ):
						newVtxArray.append( vtxArray[ pointIndex ] )
						srcToNewVtxMap[ pointIndex ] = newVtxArray.length() - 1

					newVtxList.append( srcToNewVtxMap[ pointIndex ] )

					#copy normals
					nmlId = nmlIds[ vtxIndex ]
					newNmlFaceList.append( newVtxCount.length() - 1 )
					newNmlVtxList.append( srcToNewVtxMap[ pointIndex ] )
					n = nmlArray[ nmlId ]
					newNmlArray.append( MVector( n[0], n[1], n[2] ) )

			vtxItr = vtxItr + currentVtxCnt

		#create new mesh
		newNumVertices = newVtxArray.length()
		newNumPolygons = newVtxCount.length()
		newFnMesh = MFnMesh()
		newObj = newFnMesh.create( newNumVertices, newNumPolygons, newVtxArray, newVtxCount, newVtxList )
		newFnMesh.setFaceVertexNormals( newNmlArray, newNmlFaceList, newNmlVtxList )
		maya.cmds.sets( newFnMesh.name(), e = True, fe = fnShader.name() )


		#Debug dump print
		
		if( self.__debug ):
			print( 'numVertices:%d numPolygons:%d' % ( newNumVertices, newNumPolygons ) )
			print( 'newVtxCount.length %d/ newVtxList.length %d / newVtxArray.length %d' % ( newVtxCount.length(), newVtxList.length(), newVtxArray.length() ) )
			print( '=================================\n' )

			print( 'vtxCountDump:' )
			tmp = []
			for i in range( newVtxCount.length() ):
				tmp.append( newVtxCount[i] )
			print( tmp )
			
			print( 'vtxListDump:' )
			tmp = []
			for i in range( newVtxList.length() ):
				tmp.append( newVtxList[i] )
			print( tmp )

#-----------------------------------------------
#MeshMaterialExtractorCmd
#-----------------------------------------------
class MeshMaterialExtractorCmd( MPxCommand ):
	#-----------------------------------------------
	def __init__(self):
		MPxCommand.__init__(self)

	#-----------------------------------------------
	def doIt( self, args ):
		
		selList = MSelectionList()
		MGlobal.getActiveSelectionList( selList )
		
		selListIter = MItSelectionList( selList )
		selListIter.setFilter( MFn.kMesh )

		

		while not selListIter.isDone():
			nodeObj = MObject()
			dagPath = MDagPath()
			selComp = MObject()

			selListIter.getDagPath( dagPath, selComp )
			selListIter.getDependNode( nodeObj )


			extractor = ExtractorColt1911( nodeObj )
			extractor.fire()

			break
			#selListIter.next()


	#-----------------------------------------------
	def isUndoable( self ):
		return False

	#-----------------------------------------------
	@staticmethod
	def cmdCreator():
		return MeshMaterialExtractorCmd()

#-----------------------------------------------
#initializePlugin
#-----------------------------------------------
def initializePlugin( mobject ):
	mplugin = MFnPlugin( mobject )
	try:
		mplugin.registerCommand( kCmdName, MeshMaterialExtractorCmd.cmdCreator )
	except:
		sys.stderr.write("Failed to register command: %s\n" % kCmdName)
		raise


#-----------------------------------------------
#uninitializePlugin
#-----------------------------------------------
def uninitializePlugin( mobject ):
	mplugin = MFnPlugin( mobject )
	try:
		mplugin.deregisterCommand( kCmdName )
	except:
		sys.stderr.write("Failed to deregister command: %s\n" % kCmdName)
		raise

