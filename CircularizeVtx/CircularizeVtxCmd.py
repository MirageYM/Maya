# -*- coding: utf-8 -*-

import sys
import math

import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaUI as OpenMayaUI

import polyModifier as PolyModifier

kCircularizeVtxCmdName = 'CircularizeVtxCmd'
kCircularizeVtxNodeName = 'CircularizeVtxNode'
kCircularizeVtxNodeManipName = 'CircularizeVtxNodeManip'

kCircularizeVtxNodeId = OpenMaya.MTypeId(0xb5b250)
kCircularizeVtxNodeManipId = OpenMaya.MTypeId(0xb5b251)

#-----------------------------------------------
def statusError(message):
	fullMsg = 'Status failed: %s\n' % message
	sys.stderr.write(fullMsg)
	OpenMaya.MGlobal.displayError(fullMsg)
	raise	# called from exception handlers only, reraise exception

#=========================================
#CircularizeVtxNodeManip
#=========================================
class CircularizeVtxNodeManip( OpenMayaMPx.MPxManipContainer ):
	
	#-----------------------------------------------
	def __init__(self):
		OpenMayaMPx.MPxManipContainer.__init__(self)
		
		#Manip
		self.circleManip = OpenMaya.MDagPath()
		self.pivotManip = OpenMaya.MDagPath()
		self.dirManip = OpenMaya.MDagPath()

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
			
		fnNode = OpenMaya.MFnDependencyNode( node )
		self.parentNodeHdl = OpenMaya.MObjectHandle( node )

		rotPlug = fnNode.findPlug( 'rot' )
		pivotPlug = fnNode.findPlug( 'pivotPos' )
		nVecPlug = fnNode.findPlug( 'normalVec' )
		
		fnCircleSweep = OpenMayaUI.MFnCircleSweepManip( self.circleManip )
		fnCircleSweep.setVisible( 1 )
		fnCircleSweep.setOptimizePlayback( False )
		
		fnPivot = OpenMayaUI.MFnFreePointTriadManip( self.pivotManip )
		fnPivot.setVisible( 1 )
		fnPivot.setOptimizePlayback( False )
		
		#fnDir = OpenMayaUI.MFnDirectionManip( self.dirManip )
		fnDir = OpenMayaUI.MFnRotateManip( self.dirManip )
		fnDir.setVisible( 1 )
		fnDir.setOptimizePlayback( False )
		fnDir.setRotateMode( OpenMayaUI.MFnRotateManip.kObjectSpace )
		erot = self.nVecToRot()
		fnDir.setInitialRotation( OpenMaya.MEulerRotation( erot[0], erot[1], erot[2] ) )

		try:
			fnCircleSweep.connectToAnglePlug(rotPlug)
			#fnDir.connectToDirectionPlug( nVecPlug )
			#fnDir.connectToRotationPlug( nVecPlug )
			self.addPlugToManipConversion(fnCircleSweep.centerIndex())
			#self.addPlugToManipConversion(fnDir.startPointIndex())
			self.addPlugToManipConversion(fnDir.rotationCenterIndex())
			self.addPlugToManipConversion(fnPivot.pointIndex())
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

		self.circleManip = self.addCircleSweepManip('rotationManip', 'rotation')
		self.pivotManip = self.addFreePointTriadManip('pivotManip', 'pivotPoint')
		#self.dirManip = self.addDirectionManip( 'dirManip', 'dir' )
		self.dirManip = self.addRotateManip( 'dirManip', 'dir' )
		

	#-----------------------------------------------
	def draw(self, view, path, style, status):
		OpenMayaMPx.MPxManipContainer.draw(self, view, path, style, status)

	#-----------------------------------------------
	def manipToPlugConversion(self, theIndex):

		fnNode = OpenMaya.MFnDependencyNode( self.parentNodeHdl.object() )
		
		fnCircleSweep = OpenMayaUI.MFnCircleSweepManip(self.circleManip)
		fnPivot = OpenMayaUI.MFnFreePointTriadManip(self.pivotManip)
		#fnDir = OpenMayaUI.MFnDirectionManip( self.dirManip )
		fnDir = OpenMayaUI.MFnRotateManip( self.dirManip )
		
		ppx = fnNode.findPlug('ppx')
		ppy = fnNode.findPlug('ppy')
		ppz = fnNode.findPlug('ppz')
		px = ppx.asDouble()
		py = ppy.asDouble()
		pz = ppz.asDouble()
		
		if( theIndex in self.plugIdxMap ):
			plugName = self.plugIdxMap[theIndex]
			numData = OpenMaya.MFnNumericData()

			if( plugName == 'pp' ):
				numDataObj = numData.create(OpenMaya.MFnNumericData.k3Float)
				v = OpenMaya.MPoint()
				self.getConverterManipValue( fnPivot.pointIndex(), v )
				numData.setData3Float( v[0], v[1], v[2] )
				manipData = OpenMayaUI.MManipData(numDataObj)
				
				return manipData
			
			elif( plugName == 'dir' ):
				numDataObj = numData.create(OpenMaya.MFnNumericData.k3Float)
				r = OpenMaya.MEulerRotation()
				self.getConverterManipValue( fnDir.rotationIndex(), r )
				v = OpenMaya.MPoint( 0.0, 1.0, 0.0, 1.0 )
				v = v * r.asMatrix()
				numData.setData3Float( v[0], v[1], v[2] )
				manipData = OpenMayaUI.MManipData(numDataObj)
				
				return manipData
			else:
				numDataObj = numData.create(OpenMaya.MFnNumericData.k3Float)
				numData.setData3Float( 0.0, 0.0, 0.0 )
				manipData = OpenMayaUI.MManipData(numDataObj)
				
				return manipData

		else:
			numData = OpenMaya.MFnNumericData()
			numDataObj = numData.create(OpenMaya.MFnNumericData.k3Float)
			numData.setData3Float( 0.0, 0.0, 0.0 )
			manipData = OpenMayaUI.MManipData(numDataObj)
			return manipData

	#-----------------------------------------------
	def nVecToRot( self ):
		fnNode = OpenMaya.MFnDependencyNode( self.parentNodeHdl.object() )
		nx = fnNode.findPlug('nx')
		ny = fnNode.findPlug('ny')
		nz = fnNode.findPlug('nz')

		qrot = OpenMaya.MVector( 0.0, 1.0, 0.0 ).rotateTo( OpenMaya.MVector( nx.asDouble(), ny.asDouble(), nz.asDouble() ) )
		erot = qrot.asEulerRotation()

		return [ erot[0], erot[1], erot[2] ]
		
		
	#-----------------------------------------------
	def plugToManipConversion(self, theIndex):
		fnNode = OpenMaya.MFnDependencyNode( self.parentNodeHdl.object() )

		fnCircleSweep = OpenMayaUI.MFnCircleSweepManip(self.circleManip)
		fnPivot = OpenMayaUI.MFnFreePointTriadManip(self.pivotManip)
		#fnDir = OpenMayaUI.MFnDirectionManip( self.dirManip )
		fnDir = OpenMayaUI.MFnRotateManip( self.dirManip )

		prx = fnNode.findPlug('rot')
		rx = prx.asDouble()
		
		ppx = fnNode.findPlug('ppx')
		ppy = fnNode.findPlug('ppy')
		ppz = fnNode.findPlug('ppz')
		px = ppx.asDouble()
		py = ppy.asDouble()
		pz = ppz.asDouble()
		
		#if( fnCircleSweep.centerIndex() == theIndex or fnDir.startPointIndex() ):
		if( fnCircleSweep.centerIndex() == theIndex or fnDir.rotationCenterIndex() ):
			
			numData = OpenMaya.MFnNumericData()
			numDataObj = numData.create(OpenMaya.MFnNumericData.k3Float)
			numData.setData3Float(px,py,pz)
			manipData = OpenMayaUI.MManipData(numDataObj)
			return manipData

		elif( fnCircleSweep.angleIndex() == theIndex ):
			manipData = OpenMayaUI.MManipData( rx )
			return manipData
		
		elif( fnDir.rotationIncrement() == theIndex ):
			erot = self.nVecToRot()
			
			numData = OpenMaya.MFnNumericData()
			numDataObj = numData.create(OpenMaya.MFnNumericData.k3Float)
			numData.setData3Float( erot[0], erot[1], erot[2] )
			manipData = OpenMayaUI.MManipData(numDataObj)
			return manipData
		
		elif( fnPivot.pointIndex() == theIndex ):
			numData = OpenMaya.MFnNumericData()
			numDataObj = numData.create(OpenMaya.MFnNumericData.k3Float)
			numData.setData3Float(px,py,pz)
			manipData = OpenMayaUI.MManipData(numDataObj)
			return manipData
		
		else:
			numData = OpenMaya.MFnNumericData()
			numDataObj = numData.create(OpenMaya.MFnNumericData.k3Float)
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
#CircularizeVtxFactory
#=========================================
class CircularizeVtxFactory(PolyModifier.polyModifierFty):
	#-----------------------------------------------
	def __init__(self):
		PolyModifier.polyModifierFty.__init__(self)
		
		self.mesh = OpenMaya.MObject()
		self.vtxIds = OpenMaya.MIntArray()
		self.vtxIds.clear()
		self.rot = OpenMaya.MVector()
		self.pivot = OpenMaya.MVector()
		self.wmat = OpenMaya.MMatrix()
		self.wimat = OpenMaya.MMatrix()
		self.phaseMode = 0
		self.weight = 1.0
		self.distScale = 1.0
		self.normalMode = 0
		self.normalVec = OpenMaya.MVector()
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
	def doCircularizeDistOnly(self):
		
		meshFn = OpenMaya.MFnMesh(self.mesh)
		selVtxCount = self.vtxIds.length()
		pv = OpenMaya.MPoint( self.pivot ) * self.wimat
		
		points = OpenMaya.MPointArray()
		meshFn.getPoints( points, OpenMaya.MSpace.kObject )
		if( points.length() <= 0 ):
			return

		if( selVtxCount <= 0 ):
			return

		dists = 0.0
		for i in range( selVtxCount ):
			pIndex = self.vtxIds[i]
			p = points[pIndex]
			e = p - pv
			dists += e.length()

		dists /= selVtxCount
		dists *= self.distScale
		
		for i in range( selVtxCount ):
			pIndex = self.vtxIds[i]
			p = points[pIndex]
			e = p - pv
			en = p - pv
			en.normalize()
			en *= dists
			e = pv + ( e * ( 1.0 - self.weight ) + en * self.weight )
			points.set( OpenMaya.MPoint( e ), pIndex )


		meshFn.setPoints( points, OpenMaya.MSpace.kObject )

	#-----------------------------------------------
	def doCircularizeDistAngle(self):
		meshFn = OpenMaya.MFnMesh( self.mesh )
		selVtxCount = self.vtxIds.length()
		mUtil = OpenMaya.MScriptUtil()
		
		pv = OpenMaya.MPoint( self.pivot ) * self.wimat
		
		points = OpenMaya.MPointArray()
		meshFn.getPoints( points, OpenMaya.MSpace.kObject )
		if( points.length() <= 0 ):
			return

		if( selVtxCount <= 2 ):
			return

		da = ( math.pi * 2.0 ) / selVtxCount
			
		#compute initial coordinate system v0-n0-t
		n0 = self.normalVec
		n0.normalize()
		e0 = points[1] - points[0]
		e1 = points[2] - points[0]
		if(  ( e0 ^ e1 ) * n0 < 0.0 ):
			n0 = -n0
			
		v0 = OpenMaya.MVector( 0.0, 1.0, 0.0 )
		if( abs( n0.y ) > 0.99 ):
			v0 = OpenMaya.MVector( 1.0, 0.0, 0.0 )
		t = n0 ^ v0
		t.normalize()
		v0 = n0 ^ t
		v0.normalize()
		vs = []

		m = [ v0.x, n0.x, t.x, 0.0,
			  v0.y, n0.y, t.y, 0.0,
			  v0.z, n0.z, t.z, 0.0,
			  0.0, 0.0, 0.0, 1.0 ]
		
		localCoordMat = OpenMaya.MMatrix()
		mUtil.createMatrixFromList( m, localCoordMat )
		localCoordMatInv = localCoordMat.inverse()
		
		#sort by center angle, compute avg radius
		dists = 0.0
		for i in range( selVtxCount ):
			v = points[ self.vtxIds[i] ] - pv
			dists += v.length()
			vl = OpenMaya.MVector( OpenMaya.MPoint( v ) * localCoordMat )
			vl.y = 0.0
			vl.normalize()

			d = vl.x
			a = math.acos( min( 1.0, max( d, -1.0 ) ) )
			
			if( vl.z < 0.0 ):
				a = math.pi * 2.0 - a

			while( a < 0.0 ):
				a += math.pi * 2.0

			vs.append( ( self.vtxIds[i], a ) )
			
		dists /= selVtxCount
		dists *= self.distScale

		vs.sort( key = lambda x: x[1], reverse = False )

		accParams = meshFn.autoUniformGridParams()

		for i, elem in enumerate( vs ):
			idx = elem[0]
			a = da * i
			a += self.rot
			a = -a
			
			dSin = math.sin( a )
			dCos = math.cos( a )
			v = OpenMaya.MPoint( dCos * dists, 0.0, -dSin * dists, 1.0 )
			v = OpenMaya.MVector( v * localCoordMatInv )
			
			e = pv + ( ( points[ idx ] - pv ) * ( 1.0 - self.weight ) + v * self.weight )
			
			if( self.useRay ):
				hitPos = OpenMaya.MFloatPoint()
				errDist = ( points[ idx ] - e ).length()
				intersected = meshFn.closestIntersection( OpenMaya.MFloatPoint( e.x, e.y, e.z ), OpenMaya.MFloatVector( n0 ), None, None, False, OpenMaya.MSpace.kObject,
														  errDist * 2.0, True, accParams, hitPos, None, None, None, None, None )
				if( intersected ):
					e = OpenMaya.MPoint( hitPos )

			e = e + n0 * self.nOffset
			
			points.set( OpenMaya.MPoint( e ), idx )

		meshFn.setPoints( points, OpenMaya.MSpace.kObject )
		
		
#=========================================
#CircularizeVtxNode
#=========================================
class CircularizeVtxNode(PolyModifier.polyModifierNode):
	vtxList = OpenMaya.MObject()
	pivotPos = OpenMaya.MObject()
	pivotPosX = OpenMaya.MObject()
	pivotPosY = OpenMaya.MObject()
	pivotPosZ = OpenMaya.MObject()
	
	normalVec = OpenMaya.MObject()
	normalVecX = OpenMaya.MObject()
	normalVecY = OpenMaya.MObject()
	normalVecZ = OpenMaya.MObject()
	
	rot = OpenMaya.MObject()
	nOffset = OpenMaya.MObject()

	worldMatrix = OpenMaya.MObject()
	worldInverseMatrix = OpenMaya.MObject()

	weight = OpenMaya.MObject()
	distScale = OpenMaya.MObject()
	phaseMode = OpenMaya.MObject()
	normalMode = OpenMaya.MObject()
	rayMode = OpenMaya.MObject()

	#-----------------------------------------------
	def __init__(self):
		PolyModifier.polyModifierNode.__init__(self)
		self.fCircularizeVtxFactory = CircularizeVtxFactory()

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
					inputVtxs = data.inputValue(CircularizeVtxNode.vtxList)
				except:
					statusError('ERROR getting vtxList')

				try:
					rotData = data.inputValue( CircularizeVtxNode.rot )
					pivotData = data.inputValue( CircularizeVtxNode.pivotPos )
					normalVecData = data.inputValue( CircularizeVtxNode.normalVec )
					wmatData = data.inputValue( CircularizeVtxNode.worldMatrix )
					wimatData = data.inputValue( CircularizeVtxNode.worldInverseMatrix )
					wtData = data.inputValue( CircularizeVtxNode.weight )
					scData = data.inputValue( CircularizeVtxNode.distScale )
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

				compList = inputVtxs.data()
				compListFn = OpenMaya.MFnComponentListData(compList)

				vtxIds = OpenMaya.MIntArray()
				for i in range(compListFn.length()):
					comp = compListFn[i]
					if comp.apiType() == OpenMaya.MFn.kMeshVertComponent:
						vtxComp = OpenMaya.MFnSingleIndexedComponent(comp)
						for j in range(vtxComp.elementCount()):
							vtxId = vtxComp.element(j)
							vtxIds.append(vtxId)

				# Set the mesh object and vtxList on the factory
				#
				self.fCircularizeVtxFactory.mesh = mesh
				self.fCircularizeVtxFactory.vtxIds = vtxIds
				self.fCircularizeVtxFactory.rot = rot
				self.fCircularizeVtxFactory.pivot = pivot
				self.fCircularizeVtxFactory.normalVec = nVec
				self.fCircularizeVtxFactory.wmat = wmat
				self.fCircularizeVtxFactory.wimat = wimat
				self.fCircularizeVtxFactory.weight = weight
				self.fCircularizeVtxFactory.distScale = sc
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
				return OpenMaya.kUnknownParameter

		return None

	#-----------------------------------------------
	@staticmethod
	def nodeInitializer():
		attrFn = OpenMaya.MFnTypedAttribute()
		numAttrFn = OpenMaya.MFnNumericAttribute()
		
		def setNumAttrDefault( fn ):
			fn.setWritable(True)
			fn.setStorable(True)
			fn.setChannelBox(True)
			fn.setHidden(False)
		
		CircularizeVtxNode.vtxList = attrFn.create('inputComponents', 'ics', OpenMaya.MFnComponentListData.kComponentList)
		attrFn.setStorable(True)	# To be stored during file-save

		CircularizeVtxNode.inMesh = attrFn.create('inMesh', 'im', OpenMaya.MFnMeshData.kMesh)
		attrFn.setStorable(True)	# To be stored during file-save

		# Attribute is read-only because it is an output attribute
		#
		CircularizeVtxNode.outMesh = attrFn.create('outMesh', 'om', OpenMaya.MFnMeshData.kMesh)
		attrFn.setStorable(False)
		attrFn.setWritable(False)

		# Add the attributes we have created to the node
		#
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.vtxList)
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.inMesh)
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.outMesh)

		#vecs
		CircularizeVtxNode.pivotPosX = numAttrFn.create( 'pivotPosX', 'ppx', OpenMaya.MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.pivotPosX)
		
		CircularizeVtxNode.pivotPosY = numAttrFn.create( 'pivotPosY', 'ppy', OpenMaya.MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.pivotPosY)
		
		CircularizeVtxNode.pivotPosZ = numAttrFn.create( 'pivotPosZ', 'ppz', OpenMaya.MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.pivotPosZ)

		CircularizeVtxNode.pivotPos = numAttrFn.create( 'pivotPos', 'pp', CircularizeVtxNode.pivotPosX, CircularizeVtxNode.pivotPosY, CircularizeVtxNode.pivotPosZ )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.pivotPos)

		CircularizeVtxNode.normalVecX = numAttrFn.create( 'normalVecX', 'nx', OpenMaya.MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.normalVecX)
		
		CircularizeVtxNode.normalVecY = numAttrFn.create( 'normalVecY', 'ny', OpenMaya.MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.normalVecY)
		
		CircularizeVtxNode.normalVecZ = numAttrFn.create( 'normalVecZ', 'nz', OpenMaya.MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.normalVecZ)

		CircularizeVtxNode.normalVec = numAttrFn.create( 'normalVec', 'nv', CircularizeVtxNode.normalVecX, CircularizeVtxNode.normalVecY, CircularizeVtxNode.normalVecZ )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.normalVec)
		
		#rot
		CircularizeVtxNode.rot = numAttrFn.create( 'rot', 'r', OpenMaya.MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute(CircularizeVtxNode.rot)
		
		#mat
		fnMatrix = OpenMaya.MFnMatrixAttribute()
		CircularizeVtxNode.worldMatrix = fnMatrix.create( 'worldMatrix', 'wm' )
		fnMatrix.setStorable( False )
		fnMatrix.setConnectable( True )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.worldMatrix )
		
		CircularizeVtxNode.worldInverseMatrix = fnMatrix.create( 'worldInverseMatrix', 'wim' )
		fnMatrix.setStorable( False )
		fnMatrix.setConnectable( True )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.worldInverseMatrix )

		#weight
		CircularizeVtxNode.weight = numAttrFn.create( 'weight', 'wt', OpenMaya.MFnNumericData.kDouble, 1.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.weight )
		
		CircularizeVtxNode.nOffset = numAttrFn.create( 'offset', 'of', OpenMaya.MFnNumericData.kDouble, 0.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.nOffset )

		CircularizeVtxNode.distScale = numAttrFn.create( 'distScale', 'sc', OpenMaya.MFnNumericData.kDouble, 1.0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.distScale )
		
		CircularizeVtxNode.phaseMode = numAttrFn.create( 'phaseMode', 'pm', OpenMaya.MFnNumericData.kInt, 1 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.phaseMode )

		CircularizeVtxNode.normalMode = numAttrFn.create( 'normalMode', 'nm', OpenMaya.MFnNumericData.kInt, 0 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.normalMode )
		
		CircularizeVtxNode.rayMode = numAttrFn.create( 'rayMode', 'rm', OpenMaya.MFnNumericData.kInt, 1 )
		setNumAttrDefault( numAttrFn )
		CircularizeVtxNode.addAttribute( CircularizeVtxNode.rayMode )
		
		# Set up a dependency between the input and the output.  This will cause
		# the output to be marked dirty when the input changes.  The output will
		# then be recomputed the next time the value of the output is requested.
		#
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.inMesh, CircularizeVtxNode.outMesh)
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.vtxList, CircularizeVtxNode.outMesh)
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
		CircularizeVtxNode.attributeAffects(CircularizeVtxNode.distScale, CircularizeVtxNode.outMesh)
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
		
		self.vtxCompList = OpenMaya.MObject()
		self.vtxIds = OpenMaya.MIntArray()
		self.selVtxComp = OpenMaya.MObject()
		self.circularizeVtxFactory = CircularizeVtxFactory()


	#-----------------------------------------------
	def isUndoable(self):
		return True

	#-----------------------------------------------
	def doIt(self, args):
		
		selList = OpenMaya.MSelectionList()
		OpenMaya.MGlobal.getActiveSelectionList(selList)
		selListIter = OpenMaya.MItSelectionList(selList)
		
		compListFn = OpenMaya.MFnComponentListData()
		compListFn.create()
		found = False
		foundMultiple = False

		while not selListIter.isDone():
			dagPath = OpenMaya.MDagPath()
			component = OpenMaya.MObject()
			itemMatches = True
			selListIter.getDagPath(dagPath, component)

			# Check for selected components
			#
			if itemMatches and (component.apiType() == OpenMaya.MFn.kMeshVertComponent):
				if not found:  
					compListFn.add(component)
					self.vtxCompList = compListFn.object()

					self.selVtxComp = component
					compFn = OpenMaya.MFnSingleIndexedComponent(component)
					compFn.getElements(self.vtxIds)
					
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
					self.setResult('CircularizeVtx command succeeded!')
			else:
				self.displayError('CircularizeVtx command failed' )
		else:
			self.displayError('CircularizeVtx command failed: Unable to find selected Components')


	#-----------------------------------------------
	def redoIt(self):
		try:
			self._redoModifyPoly()
			self.setResult('CircularizeVtx command succeeded!')
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
		depNodeFn = OpenMaya.MFnDependencyNode(modifierNode)
		vtxListAttr = depNodeFn.attribute('inputComponents')
		
		vtxListPlug = OpenMaya.MPlug(modifierNode, vtxListAttr)
		vtxListPlug.setMObject(self.vtxCompList)

		itrVtx = OpenMaya.MItMeshVertex( self._getMeshNode(), self.selVtxComp )
		if( itrVtx.count() <= 0 ):
			return
		
		c = [0.0, 0.0, 0.0]
		n = OpenMaya.MVector()
		while( not itrVtx.isDone() ):
			p = itrVtx.position( OpenMaya.MSpace.kWorld )
			vn = OpenMaya.MVector()
			itrVtx.getNormal( vn, OpenMaya.MSpace.kWorld )
			c[0] = p[0] + c[0]
			c[1] = p[1] + c[1]
			c[2] = p[2] + c[2]
			n = vn + n
			itrVtx.next()
		c[0] = c[0] / itrVtx.count()
		c[1] = c[1] / itrVtx.count()
		c[2] = c[2] / itrVtx.count()
		n = n / itrVtx.count()
		if( n.length() == 0.0 ):
			n = OpenMaya.MVector( 1.0, 1.0, 1.0 )
			n.normalize()
		else:
			n.normalize()

		depNodeFn.findPlug('pivotPosX').setDouble( c[0] )
		depNodeFn.findPlug('pivotPosY').setDouble( c[1] )
		depNodeFn.findPlug('pivotPosZ').setDouble( c[2] )
		depNodeFn.findPlug('normalVecX').setDouble( n[0] )
		depNodeFn.findPlug('normalVecY').setDouble( n[1] )
		depNodeFn.findPlug('normalVecZ').setDouble( n[2] )

	#-----------------------------------------------
	def _directModifier(self, mesh):
		self.circularizeVtxFactory.mesh = mesh
		self.circularizeVtxFactory.vtxIds = self.vtxIds

		self.circularizeVtxFactory.doIt()

	#-----------------------------------------------
	def __validateVtxs(self):
		return True

	#-----------------------------------------------
	def _preModifierDoIt( self, dgModifier, modifierNode ):

		dagPath = self._getMeshNode()
		dagNodeFn = OpenMaya.MFnDagNode( dagPath )
		tweakFn = OpenMaya.MFnDependencyNode( modifierNode )

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
def initializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject, 'Mirage', '2016_1.1', 'Any')
	try:
		mplugin.registerCommand(kCircularizeVtxCmdName, cmdCreator)
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
