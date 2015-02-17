/*
  AlignPlaneNodeManip
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/

#pragma once

#if !defined( ALIGNPLANENODEMANIP_HPP_INCLUDED__ )
#define ALIGNPLANENODEMANIP_HPP_INCLUDED__

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
//! AlignPlaneNodeManip
//! 
//
//--------------------------------------------------------
class AlignPlaneNodeManip: public MPxManipContainer{
 public:
	//Creators
	AlignPlaneNodeManip();
	virtual ~AlignPlaneNodeManip();
	
 public:
	//Manipulators
	static void*			creator( void );
	static MStatus			initialize( void );
	static inline MTypeId	getId( void ){ return id_; };
	
	virtual MStatus		createChildren( void ) override;
	virtual MStatus		connectToDependNode( const MObject &node ) override;

	virtual void		draw(	M3dView &view, 
								const MDagPath &path, 
								M3dView::DisplayStyle style,
								M3dView::DisplayStatus status) override;

	//CallBack
	MManipData			plugToManipConvCB( unsigned index );
	MManipData			triManipToPlugConvCB( unsigned index );
	MManipData			dirManipToPlugConvCB( unsigned index );
	MManipData			distManipToPlugConvCB( unsigned index );

 protected:
	//Manipulators
	MVector				getParentPlugPointVal( const MMatrix& m, const char* plugName );
	MVector				getParentPlugVecVal( const MMatrix& m, const char* plugName );
	MMatrix				getParentWorldMatrix( void );
	MMatrix				getParentWorldInvMatrix( void );


 protected:
	//Members
	static MTypeId	id_;

	MDagPath	distManip_;
	MDagPath	dirManip_;
	MDagPath	triManip_;

	MDagPath	thisDagPath_;
	MObject		parentNode_;

	MPoint		wPlanePos_;
	MMatrix		wPlaneRotMat_;
	
	double		boxSize_;
};


#endif //ALIGNPLANENODEMANIP_HPP_INCLUDED__