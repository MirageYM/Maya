/*
  SpreadNormalManip
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/

#pragma once

#if !defined( ALIGNPLANNODE_HPP_INCLUDED__ )
#define ALIGNPLANNODE_HPP_INCLUDED__

#include <maya/MIOStream.h>

//C
#include <stdio.h>
#include <stdlib.h>

//Maya
#include <maya/MPxNode.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MTypeId.h>
#include <maya/MPoint.h>
#include <maya/MPointArray.h>
#include <maya/MMatrix.h>
#include <maya/MItMeshPolygon.h>
#include <maya/MFloatVectorArray.h>


//--------------------------------------------------------
//! SpreadNormalNode
//! 
//
//--------------------------------------------------------
class SpreadNormalNode: public MPxNode{
 public:
	//Creators
	SpreadNormalNode();
	virtual				~SpreadNormalNode();
	
 public:
	//Manipulators
	virtual MStatus		compute( const MPlug& plug, MDataBlock& data ) override;

	static void*			creator();
	static MStatus			initialize();
	static inline MTypeId	getId( void ){ return id_; };

 protected:
	//Manipulators
	static void			vecPlugCreate(	MObject*		pVecObj,
										MObject*		pVecObjElem[3],
										const char*		pNames[4][2],
										bool			isWriteable = true,
										bool			isHidden = false,
										bool			isChannelBox = true );

 protected:
	//Members
	static	MTypeId		id_;

	static MObject		inMesh_;
	static MObject		outMesh_;
	static MObject		inComponent_;
	
	static MObject		pivotPos_;
	static MObject		pivotPosX_;
	static MObject		pivotPosY_;
	static MObject		pivotPosZ_;
	
	static MObject		blendRatio_;
	static MObject		sharedVtxMode_;

	static MObject		worldMatrix_;
	static MObject		worldInvMatrix_;
};

#endif //ALIGNPLANNODE_HPP_INCLUDED__