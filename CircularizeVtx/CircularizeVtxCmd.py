# -*- coding: utf-8 -*-

'''
CircularizeVtxCmd
Maya plugin


Installation:
 1.copy script files into your plugin folder

Usage:
 1.load "CircularizeVtxCmd.py" from Plug-in Manager 
  or run mel command
  loadPlugin( "CircularizeVtxCmd" )

 2.select Mesh Vertex/Edge/Face
 3.run mel command
 CircularizeVtxCmd



Copyright (c) 2016, yasutoshi Mori All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''


import sys
import math
import collections

import maya.OpenMaya as OpenMaya
from maya.OpenMaya import *
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaUI as OpenMayaUI
import maya.cmds

import CircularizeVtxPM as PolyModifier
reload( PolyModifier )

kCircularizeVtxCmdName = 'CircularizeVtxCmd'
kCircularizeVtxNodeName = 'CircularizeVtxNode'
kCircularizeVtxNodeManipName = 'CircularizeVtxNodeManip'

kCircularizeVtxNodeId = MTypeId(0x00126ec0)
kCircularizeVtxNodeManipId = MTypeId(0x00126ec1)

#-----------------------------------------------
def statusError(message):
	fullMsg = 'Status failed: %s\n' % message
	sys.stderr.write(fullMsg)
	MGlobal.displayError(fullMsg)
	raise	# called from exception handlers only, reraise exception

#-----------------------------------------------
def MIntArrayToList( intArray ):
	return [ intArray[i] for i in xrange( intArray.length() ) ]

#-----------------------------------------------
def MIntArrayToSet( intArray ):
	return set( MIntArrayToList( intArray ) )

#-----------------------------------------------
def DebugPrintMat( mat, prefixStr = '', suffixStr = '' ):

	print prefixStr
	for i in xrange( 4 ):
		m = []
		for j in xrange( 4 ):
			m.append( mat( i, j ) )
		print m
	print suffixStr
#-----------------------------------------------
def DebugPrintVec( vec, prefixStr = '', suffixStr = '' ):
	print '%s %f %f %f %s' % ( prefixStr, vec.x, vec.y, vec.z, suffixStr )

#-----------------------------------------------
def createSystemMat( v0, n0, t, pv ):
	mUtil = MScriptUtil()
	m = [ 1.0, 0.0, 0.0, 0.0,
		  0.0, 1.0, 0.0, 0.0,
		  0.0, 0.0, 1.0, 0.0,
		  -pv.x, -pv.y, -pv.z, 1.0 ]

	mat0 = MMatrix()
	mUtil.createMatrixFromList( m, mat0 )
	
	m = [ v0.x, n0.x, t.x, 0.0,
		  v0.y, n0.y, t.y, 0.0,
		  v0.z, n0.z, t.z, 0.0,
		  0.0, 0.0, 0.0, 1.0 ]

	mat1 = MMatrix()
	mUtil.createMatrixFromList( m, mat1 )
	mat = mat0 * mat1
	matInv = mat.inverse()

	return ( mat, matInv )
	
#-----------------------------------------------
def getPcaAxis( points, checkNormal = False ):

	#-----------------------------------------------
	def getDiagonalizeMat( mat ):
		
		#-----------------------------------------------
		def getMaxRowCol( mat ):

			maxVal = abs( mat[0][1] )
			maxRow = 0
			maxCol = 1

			for i in range( 3 ):
				for j in range( i + 1, 3 ):
					if( abs( mat[i][j] ) > maxVal ):
						maxVal = abs( mat[i][j] )
						maxRow = i
						maxCol = j
			return [ maxVal, maxRow, maxCol ]
		#- - - - -
	
		eps = 0.0001

		retVecMat = [ [ 0 for i in range( 3 ) ] for j in range( 3 ) ]
		retVecMat[0][0] = 1.0
		retVecMat[1][1] = 1.0
		retVecMat[2][2] = 1.0

		for sentinel in xrange( 100 ):
			maxVal, p, q = getMaxRowCol( mat )
			if( maxVal <= eps ):
				break

			app = mat[p][p]
			apq = mat[p][q]
			aqq = mat[q][q]

			alpha = ( app - aqq ) / 2.0
			beta = -apq
			gamma = abs( alpha ) / math.sqrt( alpha * alpha + beta * beta )

			sinVal = math.sqrt( ( 1.0 - gamma ) / 2.0 )
			cosVal = math.sqrt( ( 1.0 + gamma ) / 2.0 )
			if( alpha * beta < 0.0 ):
				sinVal = -sinVal
			sin2Val = sinVal * sinVal
			cos2Val = cosVal * cosVal
			sinCosVal = sinVal * cosVal

			for i in xrange( 3 ):
				temp = cosVal * mat[p][i] - sinVal * mat[q][i]
				mat[q][i] = sinVal * mat[p][i] + cosVal * mat[q][i]
				mat[p][i] = temp
				
			for i in xrange( 3 ):
				mat[i][p] = mat[p][i]
				mat[i][q] = mat[q][i]

			mat[p][p] = cos2Val * app + sin2Val * aqq - 2.0 * sinCosVal * apq
			mat[p][q] = sinCosVal * ( app - aqq ) + ( cos2Val - sin2Val ) * apq
			mat[q][p] = mat[p][q]
			mat[q][q] = sin2Val * app + cos2Val * aqq + 2.0 * sinCosVal * apq

			for i in xrange( 3 ):
				temp = cosVal * retVecMat[i][p] - sinVal * retVecMat[i][q]
				retVecMat[i][q] = sinVal * retVecMat[i][p] + cosVal * retVecMat[i][q]
				retVecMat[i][p] = temp

		return mat, retVecMat
	#- - - - -


	if( len( points ) < 3 ):
		return None
	
	covarianceMat = [ [ 0 for i in range( 3 ) ] for j in range( 3 ) ]

	center = MVector( 0.0, 0.0, 0.0 )

	for p in points:
		center = center + MVector( p )
	center = center / len( points )
	
	for p in points:
		dv = MVector( p ) - center
		covarianceMat[0][0] += dv.x * dv.x
		covarianceMat[1][1] += dv.y * dv.y
		covarianceMat[2][2] += dv.z * dv.z
		covarianceMat[0][1] += dv.x * dv.y
		covarianceMat[1][0] += dv.x * dv.y
		covarianceMat[0][2] += dv.x * dv.z
		covarianceMat[2][0] += dv.x * dv.z
		covarianceMat[1][2] += dv.y * dv.z
		covarianceMat[2][1] += dv.y * dv.z

	for i in xrange( 3 ):
		for j in xrange( 3 ):
			covarianceMat[i][j] /= len( points )

	diagMat, eigenVecs = getDiagonalizeMat( covarianceMat )

	eigenVecArray = [ ( diagMat[0][0], MVector( eigenVecs[0][0], eigenVecs[1][0], eigenVecs[2][0] ) ),
				  ( diagMat[1][1], MVector( eigenVecs[0][1], eigenVecs[1][1], eigenVecs[2][1] ) ),
				  ( diagMat[2][2], MVector( eigenVecs[0][2], eigenVecs[1][2], eigenVecs[2][2] ) ) ]
	eigenVecArray.sort( key = lambda x:x[0], reverse = False )

	if( checkNormal ):
		tempE0 = MVector( points[0] ) - center
		tempE1 = MVector( points[1] ) - center
		tempE0.normalize()
		tempE1.normalize()
		tempN = tempE0 ^ tempE1
		if( eigenVecArray[0][1] * tempN < 0.0 ):
			eigenVecArray[0][1] *= -1.0

	return ( eigenVecArray[2][1], eigenVecArray[1][1], eigenVecArray[0][1], center )

#=========================================
#CircularizeVtxNodeManip
#=========================================
class CircularizeVtxNodeManip( OpenMayaMPx.MPxManipContainer ):
	
	#-----------------------------------------------
	def __init__(self):
		OpenMayaMPx.MPxManipContainer.__init__(self)
		
		#Manip
		self.circleManip = MDagPath()
		self.pivotManip = MDagPath()
		self.dirManip = MDagPath()
		self.scaleManip = MDagPath()
		self.stateManip = MDagPath()

		#val
		self.parentNodeHdl = None

		self.plugIdxMap = {}

	#-----------------------------------------------
	def __del__(self):
		pass

	#-----------------------------------------------
	def connectToDependNode(self, node):

		if( self.parentNodeHdl is not None ):
			return
			
		fnNode = MFnDependencyNode( node )
		self.parentNodeHdl = MObjectHandle( node )

		rotPlug = fnNode.findPlug( 'rot' )
		pivotPlug = fnNode.findPlug( 'pivotPos' )
		nVecPlug = fnNode.findPlug( 'normalVec' )
		radPlug = fnNode.findPlug( 'radius' )
		rayPlug = fnNode.findPlug( 'rayMode' )
		
		fnDisc = OpenMayaUI.MFnDiscManip( self.circleManip )
		fnDisc.setVisible( 1 )
		fnDisc.setOptimizePlayback( False )
		
		fnPivot = OpenMayaUI.MFnFreePointTriadManip( self.pivotManip )
		fnPivot.setVisible( 1 )
		fnPivot.setOptimizePlayback( False )
		
		fnDir = OpenMayaUI.MFnRotateManip( self.dirManip )
		fnDir.setVisible( 1 )
		fnDir.setOptimizePlayback( False )
		fnDir.setRotateMode( OpenMayaUI.MFnRotateManip.kObjectSpace )
		erot = self.nVecToRot()
		fnDir.setInitialRotation( MEulerRotation( erot[0], erot[1], erot[2] ) )

		fnScale = OpenMayaUI.MFnDistanceManip( self.scaleManip )
		fnScale.setVisible( 1 )
		fnScale.connectToDistancePlug( radPlug )
		fnScale.setScalingFactor( 1.0 )
		fnScale.setDirection( MVector( 1.0, 1.0, 1.0 ) )

		fnState = OpenMayaUI.MFnStateManip( self.stateManip )
		fnState.setVisible( 1 )
		fnState.setMaxStates( 2 )

		try:
			fnState.connectToStatePlug( rayPlug )
			fnDisc.connectToAnglePlug(rotPlug)
			self.addPlugToManipConversion(fnDisc.centerIndex())
			self.addPlugToManipConversion(fnDir.rotationCenterIndex())
			self.addPlugToManipConversion(fnPivot.pointIndex())
			self.addPlugToManipConversion(fnScale.startPointIndex())
			self.addPlugToManipConversion( fnState.positionIndex() )
			idx = self.addManipToPlugConversion( pivotPlug )
			self.plugIdxMap[idx] = 'pp'
			idx = self.addManipToPlugConversion( nVecPlug )
			self.plugIdxMap[idx] = 'dir'
			
		except:
			pass
		
		self.finishAddingManips()
		OpenMayaMPx.MPxManipContainer.connectToDependNode(self, node)
		
	#-----------------------------------------------
	def createChildren(self):

		self.circleManip = self.addDiscManip('rotationManip', 'rotation')
		self.pivotManip = self.addFreePointTriadManip('pivotManip', 'pivotPoint')
		self.dirManip = self.addRotateManip( 'dirManip', 'dir' )
		self.scaleManip = self.addDistanceManip( 'sclManip', 'scl' )
		self.stateManip = self.addStateManip( 'stateManip', 'state' )
		

	#-----------------------------------------------
	def draw(self, view, path, style, status):
		OpenMayaMPx.MPxManipContainer.draw(self, view, path, style, status)

	#-----------------------------------------------
	def manipToPlugConversion(self, theIndex):

		fnNode = MFnDependencyNode( self.parentNodeHdl.object() )
		
		fnDisc = OpenMayaUI.MFnDiscManip(self.circleManip)
		fnPivot = OpenMayaUI.MFnFreePointTriadManip(self.pivotManip)
		fnDir = OpenMayaUI.MFnRotateManip( self.dirManip )
		
		ppx = fnNode.findPlug('ppx')
		ppy = fnNode.findPlug('ppy')
		ppz = fnNode.findPlug('ppz')
		px = ppx.asDouble()
		py = ppy.asDouble()
		pz = ppz.asDouble()
		
		pwm = fnNode.findPlug( 'wm' )
		o = pwm.asMObject()
		wm = MFnMatrixData( o ).matrix()
		pwim = fnNode.findPlug( 'wim' )
		o = pwim.asMObject()
		wim = MFnMatrixData( o ).matrix()
		
		if( theIndex in self.plugIdxMap ):
			plugName = self.plugIdxMap[theIndex]
			numData = MFnNumericData()

			if( plugName == 'pp' ):
				numDataObj = numData.create(MFnNumericData.k3Float)
				v = MPoint()
				self.getConverterManipValue( fnPivot.pointIndex(), v )
				v = v * wim
				numData.setData3Float( v[0], v[1], v[2] )
				manipData = OpenMayaUI.MManipData(numDataObj)
				
				return manipData
			
			elif( plugName == 'dir' ):
				numDataObj = numData.create(MFnNumericData.k3Float)
				r = MEulerRotation()
				self.getConverterManipValue( fnDir.rotationIndex(), r )
				v = MPoint( 0.0, 1.0, 0.0, 0.0 )
				v = v * r.asMatrix()
				v = v * wim
				numData.setData3Float( v[0], v[1], v[2] )
				manipData = OpenMayaUI.MManipData(numDataObj)
				
				return manipData
			else:
				numDataObj = numData.create(MFnNumericData.k3Float)
				numData.setData3Float( 0.0, 0.0, 0.0 )
				manipData = OpenMayaUI.MManipData(numDataObj)
				
				return manipData

		else:
			numData = MFnNumericData()
			numDataObj = numData.create(MFnNumericData.k3Float)
			numData.setData3Float( 0.0, 0.0, 0.0 )
			manipData = OpenMayaUI.MManipData(numDataObj)
			return manipData

	#-----------------------------------------------
	def nVecToRot( self ):
		fnNode = MFnDependencyNode( self.parentNodeHdl.object() )
		pwm = fnNode.findPlug( 'wm' )
		o = pwm.asMObject()
		wm = MFnMatrixData( o ).matrix()
		nx = fnNode.findPlug('nx')
		ny = fnNode.findPlug('ny')
		nz = fnNode.findPlug('nz')

		v = MPoint( 0.0, 1.0, 0.0, 0.0 )
		nw = MPoint( nx.asDouble(), ny.asDouble(), nz.asDouble(), 0.0 )
		nw = nw * wm

		qrot = MVector( v ).rotateTo( MVector( nw[0], nw[1], nw[2] ) )
		erot = qrot.asEulerRotation()

		return [ erot[0], erot[1], erot[2] ]
		
		
	#-----------------------------------------------
	def plugToManipConversion(self, theIndex):
		fnNode = MFnDependencyNode( self.parentNodeHdl.object() )

		fnDisc = OpenMayaUI.MFnDiscManip(self.circleManip)
		fnPivot = OpenMayaUI.MFnFreePointTriadManip(self.pivotManip)
		fnDir = OpenMayaUI.MFnRotateManip( self.dirManip )
		fnScale = OpenMayaUI.MFnDistanceManip( self.scaleManip )
		fnState = OpenMayaUI.MFnStateManip( self.stateManip )

		prx = fnNode.findPlug('rot')
		rx = prx.asDouble()
		
		ppx = fnNode.findPlug('ppx')
		ppy = fnNode.findPlug('ppy')
		ppz = fnNode.findPlug('ppz')
		px = ppx.asDouble()
		py = ppy.asDouble()
		pz = ppz.asDouble()

		pwm = fnNode.findPlug( 'wm' )
		o = pwm.asMObject()
		wm = MFnMatrixData( o ).matrix()
		pwim = fnNode.findPlug( 'wim' )
		o = pwim.asMObject()
		wim = MFnMatrixData( o ).matrix()
		
		pw = MPoint( px, py, pz ) * wm
		
		if( fnDisc.centerIndex() == theIndex or fnDir.rotationCenterIndex() == theIndex or fnScale.startPointIndex() == theIndex ):
			
			numData = MFnNumericData()
			numDataObj = numData.create(MFnNumericData.k3Float)
			numData.setData3Float( pw[0], pw[1], pw[2] )
			manipData = OpenMayaUI.MManipData(numDataObj)
			return manipData
		
		elif( fnState.positionIndex() == theIndex ):
			numData = MFnNumericData()
			numDataObj = numData.create(MFnNumericData.k3Float)
			numData.setData3Float( pw[0] + 0.5, pw[1] + 0.5, pw[2] )
			manipData = OpenMayaUI.MManipData(numDataObj)
			return manipData

		elif( fnDisc.angleIndex() == theIndex ):
			manipData = OpenMayaUI.MManipData( rx )
			return manipData
		
		elif( fnPivot.pointIndex() == theIndex ):
			numData = MFnNumericData()
			numDataObj = numData.create(MFnNumericData.k3Float)
			numData.setData3Float( pw[0], pw[1], pw[2] )
			manipData = OpenMayaUI.MManipData(numDataObj)
			return manipData
		
		else:
			numData = MFnNumericData()
			numDataObj = numData.create(MFnNumericData.k3Float)
			numData.setData3Float(0.0, 0.0, 0.0)
			manipData = OpenMayaUI.MManipData(numDataObj)
			return manipData
	
	
	#-----------------------------------------------
	@staticmethod
	def nodeInitializer():
		OpenMayaMPx.MPxManipContainer.initialize()
	
	#-----------------------------------------------
	@staticmethod
	def nodeCreator():
		return OpenMayaMPx.asMPxPtr(CircularizeVtxNodeManip())

#=========================================
#FaceCompToVertices
#=========================================
class FaceCompToVertices( object ):
	#-----------------------------------------------
	def __init__( self ):
		super( FaceCompToVertices, self ).__init__()

	
	#-----------------------------------------------
	def getPerimeter( self, dagPath, component ):
		compFn = MFnSingleIndexedComponent(component)
		selFaceIds = MIntArray()
		compFn.getElements( selFaceIds )
		selFaceIdSet = MIntArrayToSet( selFaceIds )
		
		vtxIds = set()
	
		itr = MItMeshPolygon( dagPath, component )
		while not itr.isDone():
			connVtx = MIntArray()
			itr.getVertices( connVtx )
			for i in xrange( connVtx.length() ):
				vtxIds.add( connVtx[i] )
			itr.next()

		compFn = MFnSingleIndexedComponent()
		component = compFn.create( MFn.kMeshVertComponent )
		for i in vtxIds:
			compFn.addElement( i )

		itr = MItMeshVertex( dagPath, component )
		borderVtxIds = set()
		while not itr.isDone():
			connFaceIds = MIntArray()
			itr.getConnectedFaces( connFaceIds )
			isSelBound = False
			for i in xrange( connFaceIds.length() ):
				if( not ( connFaceIds[i] in selFaceIdSet ) ):
					isSelBound = True
					break

			if( isSelBound ):
				borderVtxIds.add( itr.index() )
			
			itr.next()

		return borderVtxIds
		
	#-----------------------------------------------
	def get( self, dagPath, component ):
		compFn = MFnSingleIndexedComponent(component)
		selFaceIds = MIntArray()
		compFn.getElements( selFaceIds )
		selFaceIdSet = MIntArrayToSet( selFaceIds )

		vtxIds = set()
	
		itr = MItMeshPolygon( dagPath, component )
		while not itr.isDone():
			connVtx = MIntArray()
			itr.getVertices( connVtx )
			for i in xrange( connVtx.length() ):
				vtxIds.add( connVtx[i] )
			itr.next()
		
		return vtxIds
	
	#-----------------------------------------------
	def getPerimeterFromMesh( self, mesh, component ):
		compFn = MFnSingleIndexedComponent(component)
		fnMesh = MFnMesh( mesh )
		tmpIds = MIntArray()
		vtxIds = set()
		
		selFaceIdSet = set()
		for i in xrange( compFn.elementCount() ):
			faceId = compFn.element( i )
			selFaceIdSet.add( faceId )
			
			fnMesh.getPolygonVertices( faceId, tmpIds )
			for j in xrange( tmpIds.length() ):
				vtxIds.add( tmpIds[j] )

		itr = MItMeshVertex( mesh )
		borderVtxIds = set()
		while not itr.isDone():
			if( itr.index() in vtxIds ):
				connFaceIds = MIntArray()
				itr.getConnectedFaces( connFaceIds )
				isSelBound = False
				for i in xrange( connFaceIds.length() ):
					if( not ( connFaceIds[i] in selFaceIdSet ) ):
						isSelBound = True
						break

				if( isSelBound ):
					borderVtxIds.add( itr.index() )

			itr.next()

		return borderVtxIds
	
	#-----------------------------------------------
	def getFromMesh( self, mesh, component ):
		compFn = MFnSingleIndexedComponent(component)
		fnMesh = MFnMesh( mesh )
		tmpIds = MIntArray()
		vtxIds = set()
		
		for i in xrange( compFn.elementCount() ):
			faceId = compFn.element( i )
			fnMesh.getPolygonVertices( faceId, tmpIds )
			for j in xrange( tmpIds.length() ):
				vtxIds.add( tmpIds[j] )
		
		return vtxIds
	
#=========================================
#CircularizeVtxFactory
#=========================================
class CircularizeVtxFactory(PolyModifier.polyModifierFty):
	#-----------------------------------------------
	def __init__(self):
		PolyModifier.polyModifierFty.__init__(self)
		
		self.mesh = MObject()
		self.vtxIds = MIntArray()
		self.vtxIds.clear()
		self.innerVtxIds = MIntArray()
		self.innerVtxIds.clear()
		
		self.rot = MVector()
		self.pivot = MVector()
		self.wmat = MMatrix()
		self.wimat = MMatrix()
		self.phaseMode = 0
		self.weight = 1.0
		self.radius = 0.1
		self.radiusScale = 1.0
		self.normalMode = 0
		self.initialN = MVector()
		self.initialP = MVector()
		self.normalVec = MVector()
		self.useRay = 0
		self.nOffset = 0.0
		self.profileRamp = None
		
	#-----------------------------------------------
	def doIt(self):

		if( self.phaseMode == 0 ):
			self.doCircularizeDistOnly()
		elif( self.phaseMode == 1 ):
			self.doCircularizeDistAngle()
		else:
			return

	#-----------------------------------------------
	@staticmethod
	def getInitialCoordAndMatrix( vtxIds, points, pv, normalVec ):
		#compute initial coordinate system v0-n0-t
		mUtil = MScriptUtil()

		n0 = normalVec
		"""
		v0 = points[vtxIds[1]] - points[vtxIds[0]]
		v0.normalize()
		"""
		v0 = MVector( 0.0, 1.0, 0.0 )

		if( v0 * n0 > 0.999999 ):
			v0 = MVector( 1.0, 0.0, 0.0 )
			
		t = n0 ^ v0
		t.normalize()
		v0 = t ^ n0
		v0.normalize()

		localCoordMat, localCoordMatInv = createSystemMat( v0, n0, t, pv )
		return ( v0, n0, t, localCoordMat, localCoordMatInv )
	
	#-----------------------------------------------
	@staticmethod
	def getVertexTopologySortedList( vtxIds, pv, points, localCoordMat, mesh ):

		fnMesh = MFnMesh( mesh )
		
		selVtxCount = vtxIds.length()
		accRadius = 0.0
		vs = []
		vtxIdsSet = MIntArrayToSet( vtxIds )
		itr = MItMeshVertex( mesh )

		connList = {}
		while not itr.isDone():
			idx = itr.index()
			if( not idx in vtxIdsSet ):
				itr.next()
				continue

			conns = MIntArray()
			itr.getConnectedVertices( conns )
			connCnt = 0
			connVrt = []
			for i in xrange( conns.length() ):
				if( conns[i] == idx ):
					itr.next()
					continue
				if( conns[i] in vtxIdsSet ):
					connVrt.append( conns[i] )

			if( len( connVrt ) == 2 ):
				connList[ idx ] = connVrt
				
			itr.next()

		if( len( connList ) != vtxIds.length() ):
			return None

		loopIds = [ vtxIds[0] ]
		for cnt in xrange( vtxIds.length() ):
			currentId = loopIds[-1]
			c = connList[ currentId ]
			c0In = c[0] in loopIds
			c1In = c[1] in loopIds
			if(  not c0In and not c1In ):
				loopIds.append( c[0] )
			elif( c0In and c1In ):
				break
			elif( connList > 1 ):
				if( loopIds[-2] == c[0] ):
					loopIds.append( c[1] )
				elif( loopIds[-2] == c[1] ):
					loopIds.append( c[0] )

		return loopIds
	
	#-----------------------------------------------
	@staticmethod
	def getAngle( v, localCoordMat ):
		vl = MVector( v * localCoordMat )
		vl.y = 0.0
		vl.normalize()

		d = vl.x
		a = math.acos( min( 1.0, max( d, -1.0 ) ) )
		
		if( vl.z < 0.0 ):
			a = math.pi * 2.0 - a

		while( a < 0.0 ):
			a += math.pi * 2.0

		return a
	
	#-----------------------------------------------
	@staticmethod
	def getSortedVtxIdsAndAngle( vtxIds, pv, points, localCoordMat, mesh, n0 = None ):

		selVtxCount = vtxIds.length()
		accRadius = 0.0
		minRadius = 1000000.0
		maxRadius = 0.0
		vs = []
		
		topoSortedList = CircularizeVtxFactory.getVertexTopologySortedList( vtxIds, pv, points, localCoordMat, mesh )
		#topoSortedList = None

		pv0 = MVector( 0.0, 0.0, 0.0 )
		for i in range( selVtxCount ):
			v = points[ vtxIds[i] ]
			pv0 = MVector( v ) + pv0
		pv0.x /= selVtxCount
		pv0.y /= selVtxCount
		pv0.z /= selVtxCount
		pv0 = MPoint( pv0 )

		if( topoSortedList is not None ):

			if( n0 ):
				v0 = MVector( points[ topoSortedList[0] ] - pv0 )
				v1 = MVector( points[ topoSortedList[1] ] - pv0 )
				if( ( v0 ^ v1 ) * n0 > 0.0 ):
					topoSortedList.reverse()
			
			for i in topoSortedList:
				v = points[ i ]
				l = v.distanceTo( pv0 )
				accRadius += l
				minRadius = min( minRadius, l )
				maxRadius = max( maxRadius, l )
				vs.append( ( i, CircularizeVtxFactory.getAngle( v, localCoordMat ) ) )

			minIndex = 0
			minAngle = 100.0
			vsNrm = collections.deque( vs )
			
			for i, val in enumerate( vsNrm ):
				if( val[1] < minAngle ):
					minIndex = i
					minAngle = val[1]

			if( minIndex != 0 ):
				vsNrm.rotate( -minIndex )
			vs = list( vsNrm )
				
		else:
			for i in range( selVtxCount ):
				v = points[ vtxIds[i] ]
				l = v.distanceTo( pv0 )
				accRadius += l
				minRadius = min( minRadius, l )
				maxRadius = max( maxRadius, l )
				vs.append( ( vtxIds[i], CircularizeVtxFactory.getAngle( v, localCoordMat ) ) )
				
			vs.sort( key = lambda x: x[1], reverse = False )
		
		accRadius /= selVtxCount
		return ( vs, accRadius, minRadius, maxRadius )

		
	#-----------------------------------------------
	def doCircularizeDistOnly(self):
		
		fnMesh = MFnMesh(self.mesh)
		selVtxCount = self.vtxIds.length()
		pv = MPoint( self.pivot )
		
		points = MPointArray()
		fnMesh.getPoints( points, MSpace.kObject )
		if( points.length() <= 0 ):
			return

		if( selVtxCount <= 0 ):
			return

		radius = 0.0
		for i in range( selVtxCount ):
			pIndex = self.vtxIds[i]
			p = points[pIndex]
			e = p - pv
			radius += e.length()

		radius = self.radius
		radius *= self.radiusScale
		
		for i in range( selVtxCount ):
			pIndex = self.vtxIds[i]
			p = points[pIndex]
			e = p - pv
			en = p - pv
			en.normalize()
			en *= radius
			e = pv + ( e * ( 1.0 - self.weight ) + en * self.weight )
			points.set( MPoint( e ), pIndex )


		fnMesh.setPoints( points, MSpace.kObject )

	#-----------------------------------------------
	def doCircularizeDistAngle(self):
		mUtil = MScriptUtil()
		fnMesh = MFnMesh( self.mesh )
		selVtxCount = self.vtxIds.length()
		self.normalVec.normalize()

		pv = MPoint( self.pivot )
		radius = self.radius
		radius *= self.radiusScale
		
		points = MPointArray()
		fnMesh.getPoints( points, MSpace.kObject )
		if( points.length() <= 0 ):
			return

		if( selVtxCount <= 2 ):
			return

		da = ( math.pi * 2.0 ) / selVtxCount

		#compute initial coordinate system v0-n0-t
		v0, n0, t, localCoordMat, localCoordMatInv = CircularizeVtxFactory.getInitialCoordAndMatrix( self.vtxIds, points, self.initialP, self.initialN )
		nl = self.normalVec * localCoordMat
		rotMat = nl.rotateTo( MVector( 0.0, 1.0, 0.0 ) ).asMatrix()
		m = [ 1.0, 0.0, 0.0, 0.0,
			  0.0, 1.0, 0.0, 0.0,
			  0.0, 0.0, 1.0, 0.0,
			  -pv.x + self.initialP.x, -pv.y + self.initialP.y, -pv.z + self.initialP.z, 1.0 ]
		trsMat = MMatrix()
		mUtil.createMatrixFromList( m, trsMat )
		
		projMat = trsMat * localCoordMat * rotMat
		#projMat = localCoordMat
		projMatInv = projMat.inverse()
		
		#sort by center angle, compute avg radius
		vs, avgRadius, minRadius, maxRadius = CircularizeVtxFactory.getSortedVtxIdsAndAngle( self.vtxIds, self.initialP, points, localCoordMat, self.mesh, self.initialN )
		accParams = fnMesh.autoUniformGridParams()

		avgAngleDelta = 0.0
		for i, elem in enumerate( vs ):
			idx = elem[0]
			a = da * i
			avgAngleDelta += a - elem[1]
		avgAngleDelta /= len( vs )

		orgToCirurizePos = []
		rampVal = mUtil.asFloatPtr()
		
		for i, elem in enumerate( vs ):
			params = []
			idx = elem[0]
			a = da * i
			a += self.rot
			a = a + avgAngleDelta
			
			dSin = math.sin( a )
			dCos = math.cos( a )
			mUtil.createFromDouble( 0.0 )

			self.profileRamp.getValueAtPosition( float(i) / float(len( vs ) ), rampVal )
			radScale = radius * mUtil.getFloat( rampVal )
			
			v = MPoint( dCos * radScale, 0.0, -dSin * radScale, 1.0 )
			lv = points[idx] * projMat
			lv.y = 0.0
			elv = v - lv
			v = v * projMatInv

			v2 = MVector( v )
			e = points[ idx ] * ( 1.0 - self.weight ) + v2 * self.weight

			if( self.useRay ):
				hitPos = MFloatPoint()
				errDist = ( points[ idx ] - e ).length()
				intersected = fnMesh.closestIntersection( MFloatPoint( e.x, e.y, e.z ), MFloatVector( self.normalVec ), None, None, False, MSpace.kObject,
														  errDist * 2.0, True, accParams, hitPos, None, None, None, None, None )
				if( intersected ):
					e = MPoint( hitPos )
			
			e = e + self.normalVec * self.nOffset

			orgToCirurizePos.append( [ MVector( points[ idx ] ), MVector( elv ) ] )
			points.set( MPoint( e ), idx )

		if( self.innerVtxIds.length() > 0 ):

			fscale = self.radiusScale * ( radius / maxRadius )
			dSin = math.sin( self.rot )
			dCos = math.cos( self.rot )
			m = [ dCos, 0.0, -dSin, 0.0,
				  0.0, 1.0, 0.0, 0.0,
				  dSin, 0.0, dCos, 0.0,
				  0.0, 0.0, 0.0, 1.0 ]
			nRotMat = MMatrix()
			mUtil.createMatrixFromList( m, nRotMat )

			innerProjMat = trsMat * localCoordMat * rotMat * nRotMat
			innerProjMatInv = innerProjMat.inverse()
			innerProjMat = projMat
			innerProjMatInv = projMatInv

				
			for i in xrange( self.innerVtxIds.length() ):
				idx = self.innerVtxIds[i]
				org = points[ idx ]
				angle = CircularizeVtxFactory.getAngle( org, localCoordMat )
				self.profileRamp.getValueAtPosition( 1.0 - ( angle / ( math.pi * 2.0 ) ), rampVal )
				
				radScale = fscale * mUtil.getFloat( rampVal )
				
				p2 = org * innerProjMat
				p2.y = 0.0
				p2 = p2 * nRotMat
				
				accLen = 0.0
				lens = []
				for item in orgToCirurizePos:
					dv = MVector( org ) - item[0]
					l = dv.length()
					accLen = accLen + l
					lens.append( l )

				w = []
				wt = 0.0
				for l in lens:
					w.append( 1.0 - l / accLen )
					wt += w[-1]

				for item, weight in zip( orgToCirurizePos, w ):
					p2 = p2 + item[1] * ( weight / wt )

				p2.x *= radScale
				p2.z *= radScale
				
				p4 = MVector( MPoint( p2 ) * innerProjMatInv )
				p5 = org * ( 1.0 - self.weight ) + p4 * self.weight
				
				if( self.useRay ):
					hitPos = MFloatPoint()
					errDist = ( points[ idx ] - p5 ).length()
					intersected = fnMesh.closestIntersection( MFloatPoint( p5.x, p5.y, p5.z ), MFloatVector( self.normalVec ), None, None, False, MSpace.kObject,
																errDist * 2.0, True, accParams, hitPos, None, None, None, None, None )

					if( intersected ):
						p5 = MPoint( hitPos )
				
				p5 = p5 + self.normalVec * self.nOffset
				
				points.set( MPoint( p5 ), idx )

		fnMesh.setPoints( points, MSpace.kObject )
		
		
#=========================================
#CircularizeVtxNode
#=========================================
class CircularizeVtxNode(PolyModifier.polyModifierNode):
	vtxList = MObject()
	pivotPos = MObject()
	pivotPosX = MObject()
	pivotPosY = MObject()
	pivotPosZ = MObject()
	
	normalVec = MObject()
	normalVecX = MObject()
	normalVecY = MObject()
	normalVecZ = MObject()
	
	initialN = MObject()
	initialNX = MObject()
	initialNY = MObject()
	initialNZ = MObject()
	
	initialP = MObject()
	initialPX = MObject()
	initialPY = MObject()
	initialPZ = MObject()
	
	rot = MObject()
	nOffset = MObject()

	worldMatrix = MObject()
	worldInverseMatrix = MObject()

	weight = MObject()
	radius = MObject()
	radiusScale = MObject()
	
	phaseMode = MObject()
	normalMode = MObject()
	rayMode = MObject()

	profileRamp = MObject()

	#-----------------------------------------------
	def __init__(self):
		PolyModifier.polyModifierNode.__init__(self)
		self.fCircularizeVtxFactory = CircularizeVtxFactory()

	def getShapeDagPath( self ):
		
		p = MPlug( self.thisMObject(), CircularizeVtxNode.inMesh )
		
		plugs = MPlugArray()
		p.connectedTo( plugs, True, False )
		dagPath = MDagPath()
		
		sl = MSelectionList()
		MGlobal.getSelectionListByName( MFnDependencyNode( plugs[0].node() ).name(), sl )
		sl.getDagPath( 0, dagPath )
		
		return dagPath

	
	#-----------------------------------------------
	def compute(self, plug, data):
		stateData = 0
		state = OpenMayaMPx.cvar.MPxNode_state
		try:
			stateData = data.outputValue(state)
		except:
			statusError('ERROR getting state')

		if stateData.asShort() == 1:
			try:
				inputData = data.inputValue(CircularizeVtxNode.inMesh)
			except:
				statusError('ERROR getting inMesh')

			try:
				outputData = data.outputValue(CircularizeVtxNode.outMesh)
			except:
				statusError('ERROR getting outMesh')

			outputData.setMObject(inputData.asMesh())
		else:
			if plug == CircularizeVtxNode.outMesh:
				try:
					inputData = data.inputValue(CircularizeVtxNode.inMesh)
				except:
					statusError('ERROR getting inMesh')

				try:
					outputData = data.outputValue(CircularizeVtxNode.outMesh)
				except:
					statusError('ERROR getting outMesh') 

				try:
					inputComp = data.inputValue(CircularizeVtxNode.inputComponents)
				except:
					statusError('ERROR getting vtxList')

				try:
					rotData = data.inputValue( CircularizeVtxNode.rot )
					pivotData = data.inputValue( CircularizeVtxNode.pivotPos )
					normalVecData = data.inputValue( CircularizeVtxNode.normalVec )
					initialNData = data.inputValue( CircularizeVtxNode.initialN )
					initialPData = data.inputValue( CircularizeVtxNode.initialP )
					wmatData = data.inputValue( CircularizeVtxNode.worldMatrix )
					wimatData = data.inputValue( CircularizeVtxNode.worldInverseMatrix )
					wtData = data.inputValue( CircularizeVtxNode.weight )
					scData = data.inputValue( CircularizeVtxNode.radiusScale )
					radData = data.inputValue( CircularizeVtxNode.radius )
					pmodeData = data.inputValue( CircularizeVtxNode.phaseMode )
					nmodeData = data.inputValue( CircularizeVtxNode.normalMode )
					nOffsetData = data.inputValue( CircularizeVtxNode.nOffset )
					rayModeData = data.inputValue( CircularizeVtxNode.rayMode )
				except:
					statusError('ERROR getting trs')

				outputData.setMObject(inputData.asMesh())
				mesh = outputData.asMesh()
				self.fCircularizeVtxFactory.rot = rotData.asDouble()
				self.fCircularizeVtxFactory.pivot = pivotData.asVector()
				self.fCircularizeVtxFactory.normalVec = normalVecData.asVector()
				self.fCircularizeVtxFactory.wmat = wmatData.asMatrix()
				self.fCircularizeVtxFactory.wimat = wimatData.asMatrix()
				self.fCircularizeVtxFactory.weight = wtData.asDouble()
				self.fCircularizeVtxFactory.radius = radData.asDouble()
				self.fCircularizeVtxFactory.radiusScale = scData.asDouble()
				self.fCircularizeVtxFactory.phaseMode = pmodeData.asInt()
				self.fCircularizeVtxFactory.normalMode = nmodeData.asInt()
				self.fCircularizeVtxFactory.nOffset = nOffsetData.asDouble()
				self.fCircularizeVtxFactory.useRay = rayModeData.asInt()
				self.fCircularizeVtxFactory.initialN = initialNData.asVector()
				self.fCircularizeVtxFactory.initialP = initialPData.asVector()

				compList = inputComp.data()
				compListFn = MFnComponentListData(compList)

				vtxIds = MIntArray()
				innerIds = MIntArray()

				for i in range(compListFn.length()):
					comp = compListFn[i]
					if comp.apiType() == MFn.kMeshVertComponent:
						vtxComp = MFnSingleIndexedComponent(comp)
						for j in range(vtxComp.elementCount()):
							vtxId = vtxComp.element(j)
							vtxIds.append(vtxId)
					elif comp.apiType() == MFn.kMeshPolygonComponent:
						borderIds = FaceCompToVertices().getPerimeterFromMesh( mesh, comp )
						allIds = FaceCompToVertices().getFromMesh( mesh, comp )
						inner = allIds - borderIds
						
						for i in borderIds:
							vtxIds.append( i )
						for i in inner:
							innerIds.append( i )
							
				self.fCircularizeVtxFactory.mesh = mesh
				self.fCircularizeVtxFactory.vtxIds = vtxIds
				self.fCircularizeVtxFactory.innerVtxIds = innerIds

				self.fCircularizeVtxFactory.profileRamp = MRampAttribute( MPlug( self.thisMObject(), CircularizeVtxNode.profileRamp ) )

				# Now, perform the CircularizeVtx
				#
				try:
					self.fCircularizeVtxFactory.doIt()
				except:
					statusError('ERROR in CircularizeVtxFactory.doIt()')

				# Mark the output mesh as clean
				#
				outputData.setClean()
			else:
				return kUnknownParameter

		return None

	#-----------------------------------------------
	@staticmethod
	def nodeInitializer():
		attrFn = MFnTypedAttribute()
		numAttrFn = MFnNumericAttribute()
		
		def setNumAttrDefault( fn ):
			fn.setWritable(True)
			fn.setStorable(True)
			fn.setChannelBox(True)
			fn.setHidden(False)
		
		CircularizeVtxNode.inputComponents = attrFn.create('inputComponents', 'ics', MFnComponentListData.kComponentList)
		attrFn.setStorable(True)	# To be stored during file-save

		CircularizeVtxNode.inMesh = attrFn.create('inMesh', 'im', MFnMeshData.kMesh)
		attrFn.setStorable(True)	# To be stored during file-save

		# Attribute is read-only because it is an output attribute
		#
		CircularizeVtxNode.outMesh = attrFn.create('outMesh', 'om', MFnMeshData.kMesh)
		attrFn.setStorable(False)
		attrFn.setWritable(False)

		# Add the attributes we have created to the node
		#
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.inputComponents)
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.inMesh)
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.outMesh)

		#vecs
		CircularizeVtxNode.pivotPosX = numAttrFn.create( 'pivotPosX', 'ppx', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.pivotPosX)
		
		CircularizeVtxNode.pivotPosY = numAttrFn.create( 'pivotPosY', 'ppy', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.pivotPosY)
		
		CircularizeVtxNode.pivotPosZ = numAttrFn.create( 'pivotPosZ', 'ppz', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.pivotPosZ)

		CircularizeVtxNode.pivotPos = numAttrFn.create( 'pivotPos', 'pp', CircularizeVtxNode.pivotPosX, CircularizeVtxNode.pivotPosY, CircularizeVtxNode.pivotPosZ )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.pivotPos)

		CircularizeVtxNode.normalVecX = numAttrFn.create( 'normalVecX', 'nx', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.normalVecX)
		
		CircularizeVtxNode.normalVecY = numAttrFn.create( 'normalVecY', 'ny', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.normalVecY)
		
		CircularizeVtxNode.normalVecZ = numAttrFn.create( 'normalVecZ', 'nz', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.normalVecZ)

		CircularizeVtxNode.normalVec = numAttrFn.create( 'normalVec', 'nv', CircularizeVtxNode.normalVecX, CircularizeVtxNode.normalVecY, CircularizeVtxNode.normalVecZ )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.normalVec)
		
		#initial N
		CircularizeVtxNode.initialNX = numAttrFn.create( 'initialNX', 'inx', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		numAttrFn.setChannelBox( False )
		numAttrFn.setHidden( True )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.initialNX)

		CircularizeVtxNode.initialNY = numAttrFn.create( 'initialNY', 'iny', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		numAttrFn.setChannelBox( False )
		numAttrFn.setHidden( True )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.initialNY)
		
		CircularizeVtxNode.initialNZ = numAttrFn.create( 'initialNZ', 'inz', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		numAttrFn.setChannelBox( False )
		numAttrFn.setHidden( True )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.initialNZ)

		CircularizeVtxNode.initialN = numAttrFn.create( 'initialN', 'inv', CircularizeVtxNode.initialNX, CircularizeVtxNode.initialNY, CircularizeVtxNode.initialNZ )
		setNumAttrDefault( numAttrFn )
		numAttrFn.setChannelBox( False )
		numAttrFn.setHidden( True )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.initialN)
		
		#initial P
		CircularizeVtxNode.initialPX = numAttrFn.create( 'initialPX', 'ipx', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		numAttrFn.setChannelBox( False )
		numAttrFn.setHidden( True )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.initialPX)
		
		CircularizeVtxNode.initialPY = numAttrFn.create( 'initialPY', 'ipy', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		numAttrFn.setChannelBox( False )
		numAttrFn.setHidden( True )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.initialPY)
		
		CircularizeVtxNode.initialPZ = numAttrFn.create( 'initialPZ', 'ipz', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		numAttrFn.setChannelBox( False )
		numAttrFn.setHidden( True )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.initialPZ)

		CircularizeVtxNode.initialP = numAttrFn.create( 'initialP', 'ipv', CircularizeVtxNode.initialPX, CircularizeVtxNode.initialPY, CircularizeVtxNode.initialPZ )
		setNumAttrDefault( numAttrFn )
		numAttrFn.setChannelBox( False )
		numAttrFn.setHidden( True )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.initialP)
		
		#rot
		CircularizeVtxNode.rot = numAttrFn.create( 'rot', 'r', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.rot)
		
		#mat
		fnMatrix = MFnMatrixAttribute()
		CircularizeVtxNode.worldMatrix = fnMatrix.create( 'worldMatrix', 'wm' )
		fnMatrix.setStorable( False )
		fnMatrix.setConnectable( True )
		fnMatrix.setHidden( True )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.worldMatrix )
		
		CircularizeVtxNode.worldInverseMatrix = fnMatrix.create( 'worldInverseMatrix', 'wim' )
		fnMatrix.setStorable( False )
		fnMatrix.setConnectable( True )
		fnMatrix.setHidden( True )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.worldInverseMatrix )

		#weight
		CircularizeVtxNode.weight = numAttrFn.create( 'weight', 'wt', MFnNumericData.kDouble, 1.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.weight )
		
		CircularizeVtxNode.nOffset = numAttrFn.create( 'offset', 'of', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.nOffset )

		CircularizeVtxNode.radius = numAttrFn.create( 'radius', 'rd', MFnNumericData.kDouble, 1.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.radius )
		
		CircularizeVtxNode.radiusScale = numAttrFn.create( 'radiusScale', 'sc', MFnNumericData.kDouble, 1.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.radiusScale )
		
		CircularizeVtxNode.phaseMode = numAttrFn.create( 'phaseMode', 'pm', MFnNumericData.kInt, 1 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.phaseMode )

		CircularizeVtxNode.normalMode = numAttrFn.create( 'normalMode', 'nm', MFnNumericData.kInt, 0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.normalMode )
		
		CircularizeVtxNode.rayMode = numAttrFn.create( 'rayMode', 'rm', MFnNumericData.kInt, 1 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.rayMode )

		#ramp
		CircularizeVtxNode.profileRamp = MRampAttribute.createCurveRamp( 'profileRamp', 'pr' )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.profileRamp )
		
		
		# Set up a dependency between the input and the output.  This will cause
		# the output to be marked dirty when the input changes.  The output will
		# then be recomputed the next time the value of the output is requested.
		#
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.inMesh, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.inputComponents, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.pivotPos, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.pivotPosX, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.pivotPosY, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.pivotPosZ, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.normalVec, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.normalVecX, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.normalVecY, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.normalVecZ, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.rot, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.worldMatrix, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.worldInverseMatrix, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.weight, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.radius, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.radiusScale, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.phaseMode, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.normalMode, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.nOffset, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.rayMode, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.initialN, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.initialNX, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.initialNY, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.initialNZ, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.initialP, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.initialPX, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.initialPY, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.initialPZ, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.profileRamp, CircularizeVtxNode.outMesh)
		
		OpenMayaMPx.MPxManipContainer.addToManipConnectTable(kCircularizeVtxNodeId)

	#-----------------------------------------------
	@staticmethod
	def nodeCreator():
		return OpenMayaMPx.asMPxPtr(CircularizeVtxNode())
		
	
#=========================================
#CircularizeVtx
#=========================================
class CircularizeVtx(PolyModifier.polyModifierCmd):
	def __init__(self):
		PolyModifier.polyModifierCmd.__init__(self)
		
		self.compList = MObject()
		self.compIds = MIntArray()
		self.selComp = MObject()
		self.circularizeVtxFactory = CircularizeVtxFactory()

		self.selDagPath = None
		self.selComp = None
		self.userSpecPV = None
		self.userSpecN = None
		self.initRadMode = 0
		self.initRadius = None

	#-----------------------------------------------
	def isUndoable(self):
		return True

	#-----------------------------------------------
	def doIt(self, args):
		
		argDB = MArgDatabase ( self.syntax(), args )

		if( argDB.isFlagSet( 't' ) ):
			s = argDB.flagArgumentString( 't', 0 )
			
			maya.cmds.select( s.split( ' ' ), r = True )
			
		if( argDB.isFlagSet( 'p' ) ):
			p = []
			p.append( argDB.flagArgumentDouble( 'p', 0 ) )
			p.append( argDB.flagArgumentDouble( 'p', 1 ) )
			p.append( argDB.flagArgumentDouble( 'p', 2 ) )
			self.userSpecPV = p

		if( argDB.isFlagSet( 'n' ) ):
			p = []
			p.append( argDB.flagArgumentDouble( 'n', 0 ) )
			p.append( argDB.flagArgumentDouble( 'n', 1 ) )
			p.append( argDB.flagArgumentDouble( 'n', 2 ) )
			self.userSpecN = p
			
		if( argDB.isFlagSet( 'rm' ) ):
			self.initRadMode = argDB.flagArgumentInt( 'rm', 0 )
			
		if( argDB.isFlagSet( 'r' ) ):
			self.initRadius = argDB.flagArgumentDouble( 'r', 0 )
			
		selList = MSelectionList()
		MGlobal.getActiveSelectionList(selList)
		selListIter = MItSelectionList(selList)
		
		compListFn = MFnComponentListData()
		compListFn.create()
		found = False
		foundMultiple = False

		while not selListIter.isDone():
			dagPath = MDagPath()
			component = MObject()
			try:
				selListIter.getDagPath(dagPath, component)
			except:
				pass

			# Check for selected components
			#
			if component.apiType() == MFn.kMeshVertComponent or component.apiType() == MFn.kMeshPolygonComponent:
				if not found:  
					self.selDagPath = dagPath
					self.selComp = component
					
					compListFn.add(component)
					self.compList = compListFn.object()

					self.selComp = component
					compFn = MFnSingleIndexedComponent(component)
					compFn.getElements(self.compIds)
					
					dagPath.extendToShape()
					self._setMeshNode(dagPath)
					found = True
				else:
					foundMultiple = True
					break
				
			elif component.apiType() == MFn.kMeshEdgeComponent:
				if not found:  
					self.selDagPath = dagPath
					self.selComp = component
					
					itr = MItMeshEdge( dagPath, component )
					vtxIds = set()
					while not itr.isDone():
						vtxIds.add( itr.index( 0 ) )
						vtxIds.add( itr.index( 1 ) )
						itr.next()

					compFn = MFnSingleIndexedComponent()
					component = compFn.create( MFn.kMeshVertComponent )
					for i in vtxIds:
						compFn.addElement( i )
					compListFn.add(component)
					self.compList = compListFn.object()
					self.selComp = component
					compFn.getElements(self.compIds)
					
					dagPath.extendToShape()
					self._setMeshNode(dagPath)
					found = True
				else:
					foundMultiple = True
					break

			selListIter.next()

		if foundMultiple:
			self.displayWarning('Found more than one object selected.')

		# Initialize the polyModifierCmd node type - mesh node already set
		#
		self._setModifierNodeType(kCircularizeVtxNodeId)

		if found:
			if self.__validateVtxs():
				try:
					self._doModifyPoly()
				except:
					self.displayError('CircularizeVtx command failed!')
					raise
				else:
					MGlobal.select( self.selDagPath, self.selComp, MGlobal.kReplaceList )
					MGlobal.executeCommandOnIdle( 'select -add ' + self._getModifierNodeName() + ';ShowManipulators();' )
					self.setResult( self._getModifierNodeName() )
			else:
				self.displayError('CircularizeVtx command failed' )
		else:
			self.displayError('CircularizeVtx command failed: Unable to find selected Components')

	#-----------------------------------------------
	def redoIt(self):
		try:
			self._redoModifyPoly()
			MGlobal.executeCommandOnIdle( 'select -r ' + self._getModifierNodeName() + '; ShowManipulators();' )
			self.setResult( self._getModifierNodeName() )
		except:
			self.displayError('CircularizeVtx command failed!')
			raise


	#-----------------------------------------------
	def undoIt(self):
		try:
			self._undoModifyPoly()
			self.setResult('CircularizeVtx undo succeeded!')
		except:
			self.displayError('CircularizeVtx undo failed!')
			raise

	#-----------------------------------------------
	def _initModifierNode(self, modifierNode):
		depNodeFn = MFnDependencyNode(modifierNode)
		compListAttr = depNodeFn.attribute('inputComponents')
		
		compListPlug = MPlug(modifierNode, compListAttr)
		compListPlug.setMObject(self.compList)

		itrVtx = None
		if self.selComp.apiType() == MFn.kMeshVertComponent:
			itrVtx = MItMeshVertex( self._getMeshNode(), self.selComp )
		elif self.selComp.apiType() == MFn.kMeshPolygonComponent:
			ids = FaceCompToVertices().getPerimeter( self.selDagPath, self.selComp )
			compFn = MFnSingleIndexedComponent()
			component = compFn.create( MFn.kMeshVertComponent )
			for i in ids:
				compFn.addElement( i )
			itrVtx = MItMeshVertex( self._getMeshNode(), component )
		
		if( itrVtx.count() <= 0 ):
			return

		points = []
		while( not itrVtx.isDone() ):
			p = itrVtx.position( MSpace.kObject )
			points.append( p )
			itrVtx.next()

		majorAxis, t, n, c = getPcaAxis( points )
		
		mat, matInv = createSystemMat( majorAxis, n, t, c )
		#make bbox center
		useBBoxCenter = True

		if( useBBoxCenter ):
			p = points[0] * mat
			boxmin = MVector( p.x, p.y, p.z )
			boxmax = MVector( p.x, p.y, p.z )
			for i in xrange( 1, len( points ) ):
				p = points[i] * mat
				boxmin.x = min( boxmin.x, p.x )
				boxmin.y = min( boxmin.y, p.y )
				boxmin.z = min( boxmin.z, p.z )
				boxmax.x = max( boxmax.x, p.x )
				boxmax.y = max( boxmax.y, p.y )
				boxmax.z = max( boxmax.z, p.z )
			c = boxmax + boxmin
			c = c * 0.5
			c = MVector( MPoint( c ) * matInv )

		minRad = 100000000.0
		maxRad = 0.0
		avgRad = 0.0
		for p in points:
			v = MVector( p ) - c
			l = v.length()
			minRad = min( l, minRad )
			maxRad = max( l, maxRad )
			avgRad += l
		avgRad /= len( points )

		if( self.initRadius ):
			depNodeFn.findPlug('radius').setDouble( self.initRadius )
		elif( self.initRadMode == 1 ):
			depNodeFn.findPlug('radius').setDouble( minRad )
		elif( self.initRadMode == 2 ):
			depNodeFn.findPlug('radius').setDouble( maxRad )
		else:
			depNodeFn.findPlug('radius').setDouble( avgRad )

		depNodeFn.findPlug('initialNX').setDouble( n[0] )
		depNodeFn.findPlug('initialNY').setDouble( n[1] )
		depNodeFn.findPlug('initialNZ').setDouble( n[2] )
			
		depNodeFn.findPlug('initialPX').setDouble( c[0] )
		depNodeFn.findPlug('initialPY').setDouble( c[1] )
		depNodeFn.findPlug('initialPZ').setDouble( c[2] )
		
		if( self.userSpecPV and len( self.userSpecPV ) == 3 ):
			depNodeFn.findPlug('pivotPosX').setDouble( self.userSpecPV[0] )
			depNodeFn.findPlug('pivotPosY').setDouble( self.userSpecPV[1] )
			depNodeFn.findPlug('pivotPosZ').setDouble( self.userSpecPV[2] )
		else:
			depNodeFn.findPlug('pivotPosX').setDouble( c.x )
			depNodeFn.findPlug('pivotPosY').setDouble( c.y )
			depNodeFn.findPlug('pivotPosZ').setDouble( c.z )
			
		if( self.userSpecN and len( self.userSpecN ) == 3 ):
			depNodeFn.findPlug('normalVecX').setDouble( self.userSpecN[0] )
			depNodeFn.findPlug('normalVecY').setDouble( self.userSpecN[1] )
			depNodeFn.findPlug('normalVecZ').setDouble( self.userSpecN[2] )
		else:
			depNodeFn.findPlug('normalVecX').setDouble( n[0] )
			depNodeFn.findPlug('normalVecY').setDouble( n[1] )
			depNodeFn.findPlug('normalVecZ').setDouble( n[2] )

		ramp = MRampAttribute( MPlug( modifierNode, CircularizeVtxNode.profileRamp ) )
		if( ramp.getNumEntries() > 0 ):
			for i in range( ramp.getNumEntries() ):
				ramp.setValueAtIndex( 1.0, i )
		else:
			defaultPositions = MFloatArray( 2, 1.0 )
			defaultValues = MFloatArray( 2, 1.0 )
			defaultInterpolations = MIntArray( 2, 1 )
			ramp.addEntries( defaultPositions, defaultValues, defaultInterpolations )

	#-----------------------------------------------
	def _directModifier(self, mesh):
		self.circularizeVtxFactory.mesh = mesh
		self.circularizeVtxFactory.compIds = self.compIds

		self.circularizeVtxFactory.doIt()

	#-----------------------------------------------
	def __validateVtxs(self):
		return True

	#-----------------------------------------------
	def _preModifierDoIt( self, dgModifier, modifierNode ):

		dagPath = self._getMeshNode()
		dagNodeFn = MFnDagNode( dagPath )
		tweakFn = MFnDependencyNode( modifierNode )

		inWMat = tweakFn.findPlug('worldMatrix')
		outWMat = dagNodeFn.findPlug('worldMatrix')
		inIWMat = tweakFn.findPlug('worldInverseMatrix')
		outIWMat = dagNodeFn.findPlug('worldInverseMatrix')

		dgModifier.connect( outWMat.elementByLogicalIndex(0), inWMat )
		dgModifier.connect( outIWMat.elementByLogicalIndex(0), inIWMat )

#=========================================
#REGISTRATION
#=========================================
def cmdCreator():
	return OpenMayaMPx.asMPxPtr(CircularizeVtx())

#-----------------------------------------------
def syntaxCreator():
	syntax = MSyntax()
	syntax.addFlag( 't', 'target', MSyntax.kString )
	syntax.addFlag( 'p', 'pivot', MSyntax.kDouble, MSyntax.kDouble, MSyntax.kDouble )
	syntax.addFlag( 'n', 'normal', MSyntax.kDouble, MSyntax.kDouble, MSyntax.kDouble )
	syntax.addFlag( 'r', 'radius', MSyntax.kDouble )
	syntax.addFlag( 'rm', 'initialRadiusMode', MSyntax.kDouble )
	return syntax

#-----------------------------------------------
def initializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject, 'Mirage', '2016.1.4', 'Any')
	try:
		mplugin.registerCommand( kCircularizeVtxCmdName, cmdCreator, syntaxCreator )
	except:
		sys.stderr.write( 'Failed to register command: %s\n' % kCircularizeVtxCmdName)
		raise

	try:
		
		mplugin.registerNode(kCircularizeVtxNodeName, 
							 kCircularizeVtxNodeId, 
							 CircularizeVtxNode.nodeCreator, 
							 CircularizeVtxNode.nodeInitializer, 
							 OpenMayaMPx.MPxNode.kDependNode)
		
		mplugin.registerNode(kCircularizeVtxNodeManipName, 
							 kCircularizeVtxNodeManipId, 
							 CircularizeVtxNodeManip.nodeCreator, 
							 CircularizeVtxNodeManip.nodeInitializer, 
							 OpenMayaMPx.MPxNode.kManipContainer)
		
	except:
		sys.stderr.write( 'Failed to register node: %s' % kCircularizeVtxNodeName)
		raise


#-----------------------------------------------
def uninitializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject)
	try:
		mplugin.deregisterCommand(kCircularizeVtxCmdName)
	except:
		sys.stderr.write('Failed to unregister command: %s\n' % kCircularizeVtxCmdName)
		raise

	try:
		mplugin.deregisterNode(kCircularizeVtxNodeId)
		mplugin.deregisterNode(kCircularizeVtxNodeManipId)
	except:
		sys.stderr.write('Failed to deregister node: %s' % kCircularizeVtxNodeName)
		raise
