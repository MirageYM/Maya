/*
  AlignPlaneManip
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/

#include <maya/MIOStream.h>
#include <stdio.h>
#include <stdlib.h>

#include <maya/MFn.h>
#include <maya/MPxNode.h>
#include <maya/MPxManipContainer.h>
#include <maya/MPxSelectionContext.h>
#include <maya/MPxContextCommand.h>
#include <maya/MModelMessage.h>
#include <maya/MFnPlugin.h>
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

// Manipulators
#include <maya/MFnScaleManip.h>
#include <maya/MFnRotateManip.h>
#include <maya/MFnDirectionManip.h>
#include <maya/MFnDistanceManip.h>
#include <maya/MFnFreePointTriadManip.h>


#pragma once

#if !defined( ALIGNPLANEMANIP_HPP_INCLUDED__ )
#define ALIGNPLANEMANIP_HPP_INCLUDED__


//--------------------------------------------------------
//! initializePlugin
//--------------------------------------------------------
__declspec(dllexport) MStatus initializePlugin( MObject obj );

//--------------------------------------------------------
//! uninitializePlugin
//--------------------------------------------------------
__declspec(dllexport) MStatus uninitializePlugin( MObject obj );


//--------------------------------------------------------
//! plug2MVector
//--------------------------------------------------------
MVector plug2MVector( const MPlug& plug ){
	if( plug.numChildren() == 3 ){
		
		double x,y,z;
		MPlug rx = plug.child( 0 );
		MPlug ry = plug.child( 1 );
		MPlug rz = plug.child( 2 );
		rx.getValue( x );
		ry.getValue( y );
		rz.getValue( z );
		MVector result( x, y, z );
		
		return result;
	}else{
		MGlobal::displayError( "Expected 3 children for plug "+MString(plug.name()) );
		MVector result( 0.0, 0.0, 0.0 );
		return result;
	}
}


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
	static void*		creator( void );
	static MStatus		initialize( void );
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
	virtual MManipData manipToPlugConversion( unsigned index ) override;
	virtual MManipData plugToManipConversion( unsigned index ) override;
	virtual MStatus doRelease( void ) override;

 public:
	//Members
	static MTypeId id;

 protected:
	//Members
	MDagPath	fScaleManip_;
	MDagPath	fDirManip_;
	MDagPath	fTriManip_;
	
	MDagPath meshDagPath_;
	MObject component_;

	MPoint centroid_;
	MPoint planePoint_;
	MVector normal_;

	int numComponents_;
	MPointArray initialPositionsW_;
	MPointArray initialPositionsL_;
	MPointArray initialPoints_;
	MMatrix trsMatrix_;
	MMatrix invTrsMatrix_;
	
	bool resetPos_;
	bool resetDir_;

};

//--------------------------------------------------------
//! AlighPlaneContextObject
//! 
//
//--------------------------------------------------------
class AlighPlaneContextObject : public MPxSelectionContext{

 public:
	//Creatros
	AlighPlaneContextObject();

 public:
	//Manipulators
	virtual void	toolOnSetup( MEvent &event ) override;
	virtual void	toolOffCleanup( void ) override;

	// Callback issued when selection list changes
	static void updateManipulators( void* data );

 protected:
	//Members
	MCallbackId id1;
};

//--------------------------------------------------------
//! AlighPlaneContext
//! 
//
//--------------------------------------------------------
class AlighPlaneContext : public MPxContextCommand{
 public:
	//Creators
	inline AlighPlaneContext(){};
	virtual MPxContext* makeObj( void ) override;

 public:
	//Static manipulators
	static void* creator( void );
};


#endif //ALIGNPLANEMANIP_HPP_INCLUDED__