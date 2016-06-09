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

from maya.OpenMaya import *
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaUI as OpenMayaUI
import maya.cmds

import CircularizeVtxPM as PolyModifier
reload( PolyModifier )

kCircularizeVtxCmdName = 'CircularizeVtxCmd'
kCircularizeVtxNodeName = 'CircularizeVtxNode'
kCircularizeVtxNodeManipName = 'CircularizeVtxNodeManip'

kCircularizeVtxNodeId = MTypeId(0xb5b250)
kCircularizeVtxNodeManipId = MTypeId(0xb5b251)

#-----------------------------------------------
def statusError(message):
	fullMsg = 'Status failed: %s\n' % message
	sys.stderr.write(fullMsg)
	MGlobal.displayError(fullMsg)
	raise	# called from exception handlers only, reraise exception

def MIntArrayToList( intArray ):
	return [ intArray[i] for i in xrange( intArray.length() ) ]

def MIntArrayToSet( intArray ):
	return set( MIntArrayToList( intArray ) )

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
		sclPlug = fnNode.findPlug( 'radiusScale' )
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
		fnScale.connectToDistancePlug( sclPlug )
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
		self.radiusScale = 1.0
		self.normalMode = 0
		self.normalVec = MVector()
		self.useRay = 0
		self.nOffset = 0.0
		
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
	def getInitialCoordAndMatrix( vtxIds, points, normalVec ):
		#compute initial coordinate system v0-n0-t
		mUtil = MScriptUtil()
		
		n0 = normalVec
		n0.normalize()
		e0 = points[vtxIds[1]] - points[vtxIds[0]]
		e1 = points[vtxIds[2]] - points[vtxIds[0]]
		if(  ( e0 ^ e1 ) * n0 < 0.0 ):
			n0 = -n0
			
		v0 = MVector( 0.0, 1.0, 0.0 )
		if( abs( n0.y ) > 0.99 ):
			v0 = MVector( 1.0, 0.0, 0.0 )
		t = n0 ^ v0
		t.normalize()
		v0 = n0 ^ t
		v0.normalize()

		m = [ v0.x, n0.x, t.x, 0.0,
			  v0.y, n0.y, t.y, 0.0,
			  v0.z, n0.z, t.z, 0.0,
			  0.0, 0.0, 0.0, 1.0 ]
		
		localCoordMat = MMatrix()
		mUtil.createMatrixFromList( m, localCoordMat )
		localCoordMatInv = localCoordMat.inverse()

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
	def getSortedVtxIdsAndAngle( vtxIds, pv, points, localCoordMat, mesh, n0 = None ):

		selVtxCount = vtxIds.length()
		accRadius = 0.0
		vs = []
		
		topoSortedList = CircularizeVtxFactory.getVertexTopologySortedList( vtxIds, pv, points, localCoordMat, mesh )
		#topoSortedList = None

		if( topoSortedList is not None ):

			if( n0 ):
				v0 = MVector( points[ topoSortedList[0] ] - pv )
				v1 = MVector( points[ topoSortedList[1] ] - pv )
				if( ( v0 ^ v1 ) * n0 > 0.0 ):
					topoSortedList.reverse()
			
			for i in topoSortedList:
				v = points[ i ] - pv
				accRadius += v.length()
				vl = MVector( MPoint( v ) * localCoordMat )
				vl.y = 0.0
				vl.normalize()

				d = vl.x
				a = math.acos( min( 1.0, max( d, -1.0 ) ) )
				
				if( vl.z < 0.0 ):
					a = math.pi * 2.0 - a

				while( a < 0.0 ):
					a += math.pi * 2.0

				vs.append( ( i, a ) )

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
				v = points[ vtxIds[i] ] - pv
				accRadius += v.length()
				vl = MVector( MPoint( v ) * localCoordMat )
				vl.y = 0.0
				vl.normalize()

				d = vl.x
				a = math.acos( min( 1.0, max( d, -1.0 ) ) )
				
				if( vl.z < 0.0 ):
					a = math.pi * 2.0 - a

				while( a < 0.0 ):
					a += math.pi * 2.0

				vs.append( ( vtxIds[i], a ) )
			vs.sort( key = lambda x: x[1], reverse = False )
		
		accRadius /= selVtxCount
		return ( vs, accRadius )

		
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

		radius /= selVtxCount
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
		fnMesh = MFnMesh( self.mesh )
		selVtxCount = self.vtxIds.length()
		
		#pv = MPoint( self.pivot ) * self.wimat
		pv = MPoint( self.pivot )
		
		points = MPointArray()
		fnMesh.getPoints( points, MSpace.kObject )
		if( points.length() <= 0 ):
			return

		if( selVtxCount <= 2 ):
			return

		da = ( math.pi * 2.0 ) / selVtxCount
			
		#compute initial coordinate system v0-n0-t
		v0, n0, t, localCoordMat, localCoordMatInv = CircularizeVtxFactory.getInitialCoordAndMatrix( self.vtxIds, points, self.normalVec )
		
		#sort by center angle, compute avg radius
		vs = None
		radius = None

		vs, radius = CircularizeVtxFactory.getSortedVtxIdsAndAngle( self.vtxIds, pv, points, localCoordMat, self.mesh, n0 )
		radius *= self.radiusScale

		accParams = fnMesh.autoUniformGridParams()

		avgAngleDelta = 0.0
		for i, elem in enumerate( vs ):
			idx = elem[0]
			a = da * i
			avgAngleDelta += a - elem[1]
		avgAngleDelta /= len( vs )

		orgToCirurizePos = []
		
		for i, elem in enumerate( vs ):
			params = []
			idx = elem[0]
			a = da * i
			a += self.rot
			a = -a + avgAngleDelta
			
			dSin = math.sin( a )
			dCos = math.cos( a )
			v = MPoint( dCos * radius, 0.0, -dSin * radius, 1.0 )
			lv = ( points[idx] - pv ) * localCoordMat
			lv.y = 0.0
			elv = v - lv
			
			v2 = MVector( v * localCoordMatInv )
			e = pv + ( ( points[ idx ] - pv ) * ( 1.0 - self.weight ) + v2 * self.weight )

			if( self.useRay ):
				hitPos = MFloatPoint()
				errDist = ( points[ idx ] - e ).length()
				intersected = fnMesh.closestIntersection( MFloatPoint( e.x, e.y, e.z ), MFloatVector( n0 ), None, None, False, MSpace.kObject,
														  errDist * 2.0, True, accParams, hitPos, None, None, None, None, None )
				if( intersected ):
					e = MPoint( hitPos )
			
			e = e + n0 * self.nOffset

			orgToCirurizePos.append( [ MVector( points[ idx ] ), MVector( elv ) ] )
			points.set( MPoint( e ), idx )

		if( self.innerVtxIds.length() > 0 ):

			fscale = 1.0
			if( self.radiusScale < 1.0 ):
				fscale = self.radiusScale
				
			for i in xrange( self.innerVtxIds.length() ):
				idx = self.innerVtxIds[i]
				org = points[ idx ]
				p = MVector( org )

				p = MPoint( p ) - pv
				p2 = p * localCoordMat
				p2.y = 0.0
				
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

				p2.x *= fscale
				p2.z *= fscale
				p4 = MVector( MPoint( p2 ) * localCoordMatInv )
				p5 = pv + MVector( org - pv ) * ( 1.0 - self.weight ) + p4 * self.weight
				
				if( self.useRay ):
					hitPos = MFloatPoint()
					errDist = ( points[ idx ] - p5 ).length()
					intersected = fnMesh.closestIntersection( MFloatPoint( p5.x, p5.y, p5.z ), MFloatVector( n0 ), None, None, False, MSpace.kObject,
																errDist * 2.0, True, accParams, hitPos, None, None, None, None, None )

					if( intersected ):
						p5 = MPoint( hitPos )
				
				p5 = p5 + n0 * self.nOffset
				
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
	
	rot = MObject()
	nOffset = MObject()

	worldMatrix = MObject()
	worldInverseMatrix = MObject()

	weight = MObject()
	radiusScale = MObject()
	phaseMode = MObject()
	normalMode = MObject()
	rayMode = MObject()

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
					wmatData = data.inputValue( CircularizeVtxNode.worldMatrix )
					wimatData = data.inputValue( CircularizeVtxNode.worldInverseMatrix )
					wtData = data.inputValue( CircularizeVtxNode.weight )
					scData = data.inputValue( CircularizeVtxNode.radiusScale )
					pmodeData = data.inputValue( CircularizeVtxNode.phaseMode )
					nmodeData = data.inputValue( CircularizeVtxNode.normalMode )
					nOffsetData = data.inputValue( CircularizeVtxNode.nOffset )
					rayModeData = data.inputValue( CircularizeVtxNode.rayMode )
				except:
					statusError('ERROR getting trs')

				outputData.setMObject(inputData.asMesh())
				mesh = outputData.asMesh()
				rot = rotData.asDouble()
				pivot = pivotData.asVector()
				nVec = normalVecData.asVector()
				wmat = wmatData.asMatrix()
				wimat = wimatData.asMatrix()
				weight = wtData.asDouble()
				sc = scData.asDouble()
				pmode = pmodeData.asInt()
				nmode = nmodeData.asInt()
				rayMode = rayModeData.asInt()
				nOffset = nOffsetData.asDouble()

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

				# Set the mesh object and vtxList on the factory
				#
				self.fCircularizeVtxFactory.mesh = mesh
				self.fCircularizeVtxFactory.vtxIds = vtxIds
				self.fCircularizeVtxFactory.innerVtxIds = innerIds
				self.fCircularizeVtxFactory.rot = rot
				self.fCircularizeVtxFactory.pivot = pivot
				self.fCircularizeVtxFactory.normalVec = nVec
				self.fCircularizeVtxFactory.wmat = wmat
				self.fCircularizeVtxFactory.wimat = wimat
				self.fCircularizeVtxFactory.weight = weight
				self.fCircularizeVtxFactory.radiusScale = sc
				self.fCircularizeVtxFactory.phaseMode = pmode
				self.fCircularizeVtxFactory.normalMode = nmode
				self.fCircularizeVtxFactory.nOffset = nOffset
				self.fCircularizeVtxFactory.useRay = rayMode

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
		
		#rot
		CircularizeVtxNode.rot = numAttrFn.create( 'rot', 'r', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.rot)
		
		#mat
		fnMatrix = MFnMatrixAttribute()
		CircularizeVtxNode.worldMatrix = fnMatrix.create( 'worldMatrix', 'wm' )
		fnMatrix.setStorable( False )
		fnMatrix.setConnectable( True )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.worldMatrix )
		
		CircularizeVtxNode.worldInverseMatrix = fnMatrix.create( 'worldInverseMatrix', 'wim' )
		fnMatrix.setStorable( False )
		fnMatrix.setConnectable( True )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.worldInverseMatrix )

		#weight
		CircularizeVtxNode.weight = numAttrFn.create( 'weight', 'wt', MFnNumericData.kDouble, 1.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.weight )
		
		CircularizeVtxNode.nOffset = numAttrFn.create( 'offset', 'of', MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.nOffset )

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
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.radiusScale, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.phaseMode, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.normalMode, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.nOffset, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.rayMode, CircularizeVtxNode.outMesh)
		
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

		#make tempolar normal
		c = [0.0, 0.0, 0.0]
		n = MVector()
		while( not itrVtx.isDone() ):
			p = itrVtx.position( MSpace.kObject )
			vn = MVector()
			itrVtx.getNormal( vn, MSpace.kObject )
			c[0] = p[0] + c[0]
			c[1] = p[1] + c[1]
			c[2] = p[2] + c[2]
			n = vn + n
			itrVtx.next()
			
		c[0] = c[0] / itrVtx.count()
		c[1] = c[1] / itrVtx.count()
		c[2] = c[2] / itrVtx.count()
		pv = MPoint( c[0], c[1], c[2] )
		n = n / itrVtx.count()
		if( n.length() == 0.0 ):
			n = MVector( 1.0, 1.0, 1.0 )
			n.normalize()
		else:
			n.normalize()

		#make avg normal
		itrVtx.reset()
		vtxIds = MIntArray()
		while not itrVtx.isDone():
			vtxIds.append( itrVtx.index() )
			itrVtx.next()
					
		fnMesh = MFnMesh( self._getMeshNode() )
		points = MPointArray()
		fnMesh.getPoints( points, MSpace.kObject )
		
		if( points.length() > 0 ):

			v0, n0, t, localCoordMat, localCoordMatInv = CircularizeVtxFactory.getInitialCoordAndMatrix( vtxIds, points, n )
			#sort by center angle, compute avg radius
			vs, radius = CircularizeVtxFactory.getSortedVtxIdsAndAngle( vtxIds, pv, points, localCoordMat, self._getMeshNode() )

			accN = MVector()
			for i in range( len( vs ) ):
				e0 = MVector( points[ vs[i][0] ] - pv )
				e1 = MVector( points[ vs[ ( i + 1 ) % len( vs ) ][0] ] - pv )
				w = ( e0 ^ e1 ).length()
				e0.normalize()
				e1.normalize()
				n1 = e0 ^ e1
				n1.normalize()
				n1 = n1 * w
				accN += n1

			accN.normalize()
			n = accN

		if( self.userSpecPV and len( self.userSpecPV ) == 3 ):
			depNodeFn.findPlug('pivotPosX').setDouble( self.userSpecPV[0] )
			depNodeFn.findPlug('pivotPosY').setDouble( self.userSpecPV[1] )
			depNodeFn.findPlug('pivotPosZ').setDouble( self.userSpecPV[2] )
		else:
			depNodeFn.findPlug('pivotPosX').setDouble( c[0] )
			depNodeFn.findPlug('pivotPosY').setDouble( c[1] )
			depNodeFn.findPlug('pivotPosZ').setDouble( c[2] )
			
		if( self.userSpecN and len( self.userSpecN ) == 3 ):
			depNodeFn.findPlug('normalVecX').setDouble( self.userSpecN[0] )
			depNodeFn.findPlug('normalVecY').setDouble( self.userSpecN[1] )
			depNodeFn.findPlug('normalVecZ').setDouble( self.userSpecN[2] )
		else:
			depNodeFn.findPlug('normalVecX').setDouble( n[0] )
			depNodeFn.findPlug('normalVecY').setDouble( n[1] )
			depNodeFn.findPlug('normalVecZ').setDouble( n[2] )

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
	return syntax

#-----------------------------------------------
def initializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject, 'Mirage', '2016.1.3', 'Any')
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
