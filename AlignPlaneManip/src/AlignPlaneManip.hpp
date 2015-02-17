/*
  AlignPlaneManip
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/


///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
/*

  THIS IS AlignPlaneManip PROTOTYPE SOURCE CODE.
  THIS CODE IS OBSOLETED FROM AlignPlaneManip PROJECT.

*/
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////


#pragma once

#if !defined( ALIGNPLANEMANIP_HPP_INCLUDED__ )
#define ALIGNPLANEMANIP_HPP_INCLUDED__

#include <maya/MIOStream.h>
//C
#include <stdio.h>
#include <stdlib.h>

//Maya
#include <maya/MFn.h>
#include <maya/MPxNode.h>
#include <maya/MPxManipContainer.h>
#include <maya/MPxSelectionContext.h>
#include <maya/MPxContextCommand.h>
#include <maya/MModelMessage.h>
#include <maya/MGlobal.h>
#include <maya/MItSelectionList.h>
#include <maya/MPoint.h>
#include <maya/MPointArray.h>
#include <maya/MVector.h>
#include <maya/MDagPath.h>
#include <maya/MManipData.h>
#include <maya/MSelectionList.h>
#include <maya/MItMeshVertex.h>
#include <maya/MFnComponent.h>
#include <maya/MFnScaleManip.h>
#include <maya/MFnRotateManip.h>
#include <maya/MFnDirectionManip.h>
#include <maya/MFnDistanceManip.h>
#include <maya/MFnFreePointTriadManip.h>

//project


//--------------------------------------------------------
//! AlignPlaneManip
//! 
//
//--------------------------------------------------------
class AlignPlaneManip: public MPxManipContainer{
 public:
	//Creators
	AlignPlaneManip();
	virtual ~AlignPlaneManip();
	
 public:
	//Manipulators
	static void*			creator( void );
	static MStatus			initialize( void );
	static inline MTypeId	getId( void ){ return id; };
	
	virtual MStatus		createChildren( void ) override;
	virtual MStatus		connectToDependNode( const MObject &node ) override;

	virtual void		draw(	M3dView &view, 
								const MDagPath &path, 
								M3dView::DisplayStyle style,
								M3dView::DisplayStatus status) override;

	inline void			setMeshDagPath( const MDagPath& dagPath ){ meshDagPath_ = dagPath; }
	inline void			setComponentObject( const MObject& obj ){ component_ = obj; }
	
	MManipData			onChangedCallback( unsigned index );

	// Virtual handlers
	virtual MManipData	manipToPlugConversion( unsigned index ) override;
	virtual MManipData	plugToManipConversion( unsigned index ) override;
	virtual MStatus		doRelease( void ) override;

 protected:
	//Members
	static MTypeId	id;

	MDagPath	fScaleManip_;
	MDagPath	fDirManip_;
	MDagPath	fTriManip_;
	
	MDagPath	meshDagPath_;
	MObject		component_;

	MPoint		centroid_;
	MPoint		planePoint_;
	MVector		normal_;

	int			numComponents_;
	MPointArray	initialPositionsW_;
	MPointArray	initialPositionsL_;
	MPointArray	initialPoints_;
	MMatrix		trsMatrix_;
	MMatrix		invTrsMatrix_;
	
	bool		resetPos_;
	bool		resetDir_;

};

//--------------------------------------------------------
//! AlignPlaneContextObject
//! 
//
//--------------------------------------------------------
class AlignPlaneContextObject : public MPxSelectionContext{
 public:
	//Creatros
	AlignPlaneContextObject();
	virtual ~AlignPlaneContextObject();

 public:
	//Manipulators
	virtual void	toolOnSetup( MEvent &event ) override;
	virtual void	toolOffCleanup( void ) override;

	// Callback issued when selection list changes
	static void		updateManipulators( void* data );

 protected:
	//Members
	MCallbackId id1;
};

//--------------------------------------------------------
//! AlignPlaneContext
//! 
//
//--------------------------------------------------------
class AlignPlaneContext : public MPxContextCommand{
 public:
	//Creators
	inline AlignPlaneContext(){};
	virtual MPxContext* makeObj( void );

 public:
	//Static manipulators
	static void* creator( void );
};


#endif //ALIGNPLANEMANIP_HPP_INCLUDED__