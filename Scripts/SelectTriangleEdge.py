# -*- coding: utf-8 -*-
from math import *
from pymel import *
from pymel.core import *
from pymel.util import *
import maya.cmds as cmds
import time

#-----------------------------------------------
def getVec(e,v):
	p0 = e.getPoint(0)
	p1 = e.getPoint(1)
	pd = v.getPosition() - p0
	if( pd.length() < 0.000001 ):
		p0 = e.getPoint(1)
		p1 = e.getPoint(0)

	vec = p1 - p0
	vec.normalize()
	
	return vec


#-----------------------------------------------
def getSideEdge( e, v ):
	ret = []
	
	f = e.connectedFaces()
	ves = v.connectedEdges()
	
	for ve in ves:
		for f2 in f:
			if( ve.isConnectedTo( f2 ) and ve != e ):
				ret.append( ve )
				
	return ret


#-----------------------------------------------
def doIt():
	cmds.ConvertSelectionToVertices()
	lsres = ls( sl = True )

	target = []
	
	for vtxs in lsres:
		for v in vtxs:
			minA = None
			minIndex = None
			ed = v.connectedEdges()

			if( ed.count() != 5 ):
				continue
			
			for index in range( ed.count() ):
				ed.setIndex(index)
				c = ed.currentItem()
				cv = getVec(c,v)
				
				se = getSideEdge( c, v )
				if( len( se ) != 2 ):
					continue

				pv = getVec(se[0],v)
				nv = getVec(se[1],v)
				
				a0 = acos( dot( cv, pv ) )
				a1 = acos( dot( cv, nv ) )
				a2 = acos( dot( pv, nv ) )
				acc = a0 + a1
				
				if( minA is None or minA > acc ):
					minA = acc
					minIndex = index
					
			if( minIndex is not None ):
				ed.setIndex( minIndex )
				target.append( ed.currentItem() )

	selectType( eg = True )
	select( cl = True )
	select( target, r = True )
