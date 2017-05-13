import maya
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI

#=========================================
#  ClickedPos
#=========================================
class ClickedPos( object ):
	def __init__( self, p = None, n = None, d = None ):
		super( ClickedPos, self ).__init__()
		
		self.worldPos = OpenMaya.MPoint()
		self.worldNormal = OpenMaya.MVector()
		self.hitDagPath = OpenMaya.MDagPath()

		if( p ):
			self.worldPos = OpenMaya.MPoint( p )
		if( n ):
			self.worldNormal = OpenMaya.MVector( n )
		if( d ):
			self.hitDagPath = d
	
#=========================================
#  CurveConnectorContext
#=========================================
class CurveConnectorContext( object ):
	#-----------------------------------------------
	def __init__( self ):
		super( CurveConnectorContext, self ).__init__()
		self.ctxName = 'CurveConnectorContext'
		self.reset()
		
		if( cmds.draggerContext( self.ctxName, ex = True  ) ):
			cmds.draggerContext( self.ctxName, 
								 e = True,
								 pressCommand = self.onPress, 
								 dragCommand = self.onDrag, 
								 finalize = self.onFinalize,
								 cursor='hand', 
								 sp = 'screen' )
		else:
			cmds.draggerContext( self.ctxName, 
								 pressCommand = self.onPress, 
								 dragCommand = self.onDrag, 
								 finalize = self.onFinalize,
								 cursor='hand', 
								 sp = 'screen' )
		cmds.setToolTo( self.ctxName )
		self.updateStatusLine()

	#-----------------------------------------------
	def reset( self ):
		self.clickedPoints = []
		self.curve = None
		self.circle = None
		self.magCoeff = 0.5
		
	#-----------------------------------------------
	def getClickedParams( self ):
		pressPosition = cmds.draggerContext( self.ctxName, query=True, anchorPoint=True)
		m3dView = OpenMayaUI.M3dView()
		active = m3dView.active3dView()
		cameraPath = OpenMaya.MDagPath()
		active.getCamera( cameraPath )
		clip = OpenMaya.MFnCamera( cameraPath ).farClippingPlane()

		pos = OpenMaya.MPoint()
		dirV = OpenMaya.MVector()

		active.viewToWorld( int( pressPosition[0] ), int( pressPosition[1] ), pos, dirV )

		itrDag = OpenMaya.MItDag( OpenMaya.MItDag.kDepthFirst, OpenMaya.MFn.kMesh )
		nearDist = None
		nearPos = None
		nearDagPath = None
		while( not itrDag.isDone() ):
			dagPath = OpenMaya.MDagPath()
			itrDag.getPath( dagPath )
			if( dagPath.isVisible() ):
				fnMesh = OpenMaya.MFnMesh( dagPath )
				p = OpenMaya.MFloatPoint()
				f = OpenMaya.MScriptUtil()
				f.createFromInt( 0 )
				t = OpenMaya.MScriptUtil()
				t.createFromInt( 0 )
				fp = f.asIntPtr()
				tp = t.asIntPtr()
				if( fnMesh.closestIntersection( OpenMaya.MFloatPoint( pos ), 
												OpenMaya.MFloatVector( dirV ), 
												None, 
												None, 
												True, 
												OpenMaya.MSpace.kWorld, 
												clip,
												True, 
												None, 
												p, 
												None, 
												fp, 
												tp, 
												None, 
												None ) ):
					d = ( OpenMaya.MFloatPoint( pos ) - p ).length()
					if( not nearDist ):
						nearDist = d
						nearPos = p
						nearDagPath = dagPath
					elif( nearDist > d ):
						nearDist = d
						nearPos = p
						nearDagPath = dagPath
						
			itrDag.next()
			
		if( nearPos ):
			n = OpenMaya.MVector()
			OpenMaya.MFnMesh( nearDagPath ).getClosestNormal( OpenMaya.MPoint( nearPos ), n, OpenMaya.MSpace.kWorld )
			return ClickedPos( nearPos, n, nearDagPath )
		else:
			return None

	#-----------------------------------------------
	def updateStatusLine( self ):
		if( len( self.clickedPoints ) == 0 ):
			OpenMaya.MGlobal.displayInfo( 'add StartPoint' )
		elif( len( self.clickedPoints ) == 1 ):
			OpenMaya.MGlobal.displayInfo( 'add EndPoint' )
		elif( len( self.clickedPoints ) == 2 ):
			OpenMaya.MGlobal.displayInfo( 'Middle click to end' )
		else:
			OpenMaya.MGlobal.displayInfo( '' )
	#-----------------------------------------------
	def vecToTuple( self, arg ):
		return ( arg[0], arg[1], arg[2] )
	
	#-----------------------------------------------
	def getCurveParam( self ):

		mag = ( self.clickedPoints[0].worldPos - self.clickedPoints[1].worldPos ).length() * self.magCoeff;
		
		p = [ self.vecToTuple( self.clickedPoints[0].worldPos ),
			  self.vecToTuple( self.clickedPoints[0].worldPos + self.clickedPoints[0].worldNormal * mag ),
			  self.vecToTuple( self.clickedPoints[1].worldPos + self.clickedPoints[1].worldNormal * mag ),
			  self.vecToTuple( self.clickedPoints[1].worldPos ) ]

		return p
		
	#-----------------------------------------------
	def createCurve( self ):
		self.curve = cmds.curve( p = self.getCurveParam() )
		cmds.displaySmoothness( divisionsU = 3, divisionsV=3, pointsWire=16, pointsShaded=4, polygonObject=3 )
		#self.curveRebuild = cmds.rebuildCurve( self.curve, ch = True, rt = 0, s = 5 )
		#self.circle = cmds.circle( c = self.vecToTuple( self.clickedPoints[0].worldPos ), nr = self.vecToTuple( self.clickedPoints[0].worldNormal ), r = 0.01 )[0]
		#cmds.extrude( self.circle, self.curve, ch = True )

	#-----------------------------------------------
	def modifyCurve( self ):
		param = self.getCurveParam()
		cmds.setAttr( self.curve + '.cv[0]', param[0][0], param[0][1], param[0][2], type = 'float3' )
		cmds.setAttr( self.curve + '.cv[1]', param[1][0], param[1][1], param[1][2], type = 'float3' )
		cmds.setAttr( self.curve + '.cv[2]', param[2][0], param[2][1], param[2][2], type = 'float3' )
		cmds.setAttr( self.curve + '.cv[3]', param[3][0], param[3][1], param[3][2], type = 'float3' )
		cmds.refresh( cv = True )
		#cmds.circle( self.circle, e = True, c = self.vecToTuple( self.clickedPoints[0].worldPos ), nr = self.vecToTuple( self.clickedPoints[0].worldNormal ), r = 0.01 )

	#-----------------------------------------------
	def onPress( self ):
		mods = cmds.getModifiers()
		if( mods & 4 ) > 0:
			return

		if( cmds.draggerContext( self.ctxName, q = True, bu = True ) > 1 ):
			self.reset()
			self.updateStatusLine()
			return
		
		p = self.getClickedParams()
		if( not p ):
			return
		
		if( len( self.clickedPoints ) > 1 and self.curve ):
			mods = cmds.getModifiers()
			if( mods & 1 ) > 0:
				self.clickedPoints[0] = p
			else:
				self.clickedPoints[1] = p
			self.modifyCurve()
		elif( len( self.clickedPoints ) == 1 ):
			self.clickedPoints.append( p )
			self.createCurve()
		else:
			self.clickedPoints.append( p )
		self.updateStatusLine()


	#-----------------------------------------------
	def onDrag( self ):

		mods = cmds.getModifiers()
		if( mods & 4 ) > 0:
			pressPosition = cmds.draggerContext( self.ctxName, query=True, anchorPoint=True)
			dragPosition = cmds.draggerContext( self.ctxName, query=True, dragPoint=True)

			self.magCoeff += ( float( dragPosition[0] ) - float( pressPosition[0] ) ) * 0.001
			if( len( self.clickedPoints ) > 1 and self.curve ):
				self.modifyCurve()
		"""
		elif( len( self.clickedPoints ) > 1 and self.curve ):
			p = self.getClickedParams()
			if( mods & 1 ) > 0:
				self.clickedPoints[0] = p
			else:
				self.clickedPoints[1] = p
			self.modifyCurve()
		"""
			
		cmds.refresh( cv = True )

	#-----------------------------------------------
	def onFinalize( self ):
		self.reset()

#-----------------------------------------------
def doIt():
	CurveConnectorContext()

