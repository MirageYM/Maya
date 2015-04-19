/*
  AlignPlaneManip
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/

#pragma once

#if !defined( ALIGNPLANCMD_HPP_INCLUDED__ )
#define ALIGNPLANCMD_HPP_INCLUDED__

#include <maya/MIOStream.h>

//C
#include <stdio.h>
#include <stdlib.h>

//Maya
#include <maya/MGlobal.h>
#include <maya/MPxCommand.h>
#include <maya/MSyntax.h>
#include <maya/MArgList.h>
#include <maya/MDGModifier.h>
#include <maya/MDagModifier.h>
#include <maya/MDagPath.h>
#include <maya/MIntArray.h>
#include <maya/MFloatVectorArray.h>

#include <maya/MPlug.h>

//--------------------------------------------------------
//! AlignPlaneCmd
//! 
//
//--------------------------------------------------------
class AlignPlaneCmd: public MPxCommand{
 public:
	//Typedefs
	struct ModifyTargetInfo{
		MObject		selCompList_;
		MDagPath	selDagPath_;

		
		MDagPath	targetMeshShapeDagPath_;
		MObject		initialMeshShape_;
		
		MDagPath	cachedDagPath_;

		MObject		transformNode_;

		MPlug		meshShapeNodeDstPlug_;
		MObject		meshShapeNodeDstAttr_;
		
		MObject		upstreamNode_;
		MPlug		upstreamSrcPlug_;
		MObject		upstreamSrcAttr_;

		MObject		tweakNode_;
		MObject		tweakNodeSrcAttr_;
		MObject		tweakNodeDstAttr_;

		MObject		thisNode_;

	};

	struct ModifyParams{
		MVector	center_;
		MVector	normal_;
	};
	
 public:
	//Creators
	AlignPlaneCmd();
	virtual				~AlignPlaneCmd();
	
 public:
	//Manipulators
	virtual MStatus		doIt( const MArgList& ) override;
	virtual MStatus		redoIt( void ) override;
	virtual MStatus		undoIt( void ) override;
	virtual bool		isUndoable( void ) const override;
	
	static void*		creator();
	static MSyntax		syntaxCreator			(	void );

 protected:
	//Manipulators
	virtual MStatus		performCmd( void );
	virtual MStatus		performUndoCmd( void );
	
	virtual MStatus		createModifierNode( void );
	virtual void		createTweakNode( void );
	virtual void		cleanupShapeTweakPnts( void );
	
	virtual MStatus		rollbackTweak( void );
	virtual MStatus		rollbackCachedMesh( void );
	virtual MStatus		rollbackNodeConnection( void );
	
	virtual void		getInitialParam( void );
	virtual void		setInitialParamToNode( void );


 protected:
	//Members
	MDGModifier		dgModifier_;
	MDagModifier	dagModifier_;

	MIntArray			tweakIndexArray_;
	MFloatVectorArray	tweakVectorArray_;

	ModifyTargetInfo	targetInfo_;
	ModifyParams		modifyParams_;

	MSelectionList		initialSelList_;
	
	bool				hasTweak_;
	bool				hasHistory_;
	int					isRecordHistory_;
	
};

#endif //ALIGNPLANCMD_HPP_INCLUDED__