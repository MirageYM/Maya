/*
  SpreadNormalManip
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/
//Maya
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnMatrixData.h>
#include <maya/MEulerRotation.h>
#include <maya/MTransformationMatrix.h>

//OpenGL
#pragma comment( lib, "opengl32" )
#pragma comment( lib, "glu32" )
#if !defined( SDK_HAS_MGL_ )
#include <gl/gl.h>
#include <gl/glu.h>
#endif

//project
#include "maya_utility.hpp"
#include "SpreadNormalNodeManip.hpp"

using namespace MayaUtility;

//--------------------------------------------------------
//! SpreadNormalNodeManip
//--------------------------------------------------------
MTypeId SpreadNormalNodeManip::id_( 0xb5b233 );

//- - - - - - - - - - - - - - - - - -
//
SpreadNormalNodeManip::SpreadNormalNodeManip()
{

}

//- - - - - - - - - - - - - - - - - -
//
SpreadNormalNodeManip::~SpreadNormalNodeManip(){
}


//- - - - - - - - - - - - - - - - - -
//
void *SpreadNormalNodeManip::creator( void ){
	 return new SpreadNormalNodeManip();
}


//- - - - - - - - - - - - - - - - - -
//
MStatus SpreadNormalNodeManip::initialize( void ){ 
	MStatus stat;
	stat = MPxManipContainer::initialize();
	return stat;
}


//- - - - - - - - - - - - - - - - - -
//
MStatus SpreadNormalNodeManip::createChildren( void ){
	MStatus stat = MStatus::kSuccess;

	triManip_ = addFreePointTriadManip( "triManip", "tri" );
	distManip_ = addDistanceManip( "distManip", "dist" );
	boxSize_ = 2.0f;
	
	return stat;
}


//- - - - - - - - - - - - - - - - - -
//
MStatus SpreadNormalNodeManip::connectToDependNode( const MObject &node ){
	MStatus status;
	
	parentNode_ = node;
	MFnDependencyNode fnParentNode( parentNode_ );
	MPlug trsPlug = fnParentNode.findPlug( "pivotPos", &status );
	MPlug scalePlug = fnParentNode.findPlug( "blendRatio", &status );

	//Tri
	MFnFreePointTriadManip fnTriManip( triManip_ );
	fnTriManip.setGlobalTriadPlane( MFnFreePointTriadManip::kViewPlane );
	addPlugToManipConversionCallback( fnTriManip.pointIndex(), (plugToManipConversionCallback)&SpreadNormalNodeManip::plugToManipConvCB );
	addManipToPlugConversionCallback( trsPlug,  (manipToPlugConversionCallback)&SpreadNormalNodeManip::triManipToPlugConvCB );

	//Dist
	MFnDistanceManip fnDistManip( distManip_ );
	addPlugToManipConversionCallback( fnDistManip.distanceIndex(), (plugToManipConversionCallback)&SpreadNormalNodeManip::plugToManipConvCB );
	addManipToPlugConversionCallback( scalePlug,  (manipToPlugConversionCallback)&SpreadNormalNodeManip::distManipToPlugConvCB );
	

	finishAddingManips();
	MPxManipContainer::connectToDependNode( node );

	return MS::kSuccess;
}


//- - - - - - - - - - - - - - - - - -
//
void SpreadNormalNodeManip::draw(	M3dView &view, 
								const MDagPath &path, 
								M3dView::DisplayStyle style,
								M3dView::DisplayStatus status)
{
	
	MPxManipContainer::draw( view, path, style, status );
}


//- - - - - - - - - - - - - - - - - -
//
MVector SpreadNormalNodeManip::getParentPlugPointVal( const MMatrix& m, const char* plugName ){
	MStatus status;

	MFnDependencyNode fnParentNode( parentNode_ );
	MPlug trsPlug = fnParentNode.findPlug( plugName, &status );

	MPoint p = plug2MVector<MPoint>( trsPlug );

	p = p * m;

	return MVector( p );
}
	
//- - - - - - - - - - - - - - - - - -
//
MVector SpreadNormalNodeManip::getParentPlugVecVal( const MMatrix& m, const char* plugName ){
	MStatus status;

	MFnDependencyNode fnParentNode( parentNode_ );
	MPlug trsPlug = fnParentNode.findPlug( plugName, &status );

	MVector p = plug2MVector<MVector>( trsPlug );

	p = p * m;

	return MVector( p );
}

//- - - - - - - - - - - - - - - - - -
//
MMatrix SpreadNormalNodeManip::getParentWorldMatrix( void ){
	MStatus status;

	MFnDependencyNode fnParentNode( parentNode_ );
	MPlug worldMatPlug = fnParentNode.findPlug( "worldMatrix" );
	MObject worldMatObj;
	worldMatPlug.getValue( worldMatObj );
	MFnMatrixData fnMatData( worldMatObj );
	return fnMatData.matrix();
}

//- - - - - - - - - - - - - - - - - -
//
MMatrix SpreadNormalNodeManip::getParentWorldInvMatrix( void ){
	MStatus status;

	MFnDependencyNode fnParentNode( parentNode_ );
	MPlug worldMatPlug = fnParentNode.findPlug( "worldInverseMatrix" );
	MObject worldMatObj;
	worldMatPlug.getValue( worldMatObj );
	MFnMatrixData fnMatData( worldMatObj );
	return fnMatData.matrix();
}

//- - - - - - - - - - - - - - - - - -
//
MManipData SpreadNormalNodeManip::plugToManipConvCB( unsigned index ){
	

	MStatus status;

	MObject obj = MObject::kNullObj;
	MFnNumericData fnNumericData;
	
	MFnFreePointTriadManip fnTriManip( triManip_ );
	MFnDirectionManip fnDirManip( dirManip_ );
	MFnDistanceManip fnDistManip( distManip_ );

	if( 0 ){

	//Tri
	}else if( index == fnTriManip.pointIndex() ){
		MObject obj = fnNumericData.create( MFnNumericData::k3Double );
		MVector p = getParentPlugPointVal( getParentWorldMatrix(), "pivotPos" );
		pivotPos_ = MPoint( p );
		fnDistManip.setStartPoint( MPoint( p ) );
		
		fnNumericData.setData( p[0], p[1], p[2] );
		return MManipData( obj );

	}else if( index == fnDistManip.distanceIndex() ){
		MFnDependencyNode fnParentNode( parentNode_ );
		MPlug p = fnParentNode.findPlug( "blendRatio" );
		double val;
		p.getValue( val );
		return MManipData( val );
		
	}else{
		MGlobal::displayError("Invalid index in plugToManipConvCB()!");
		fnNumericData.setData( 0.0, 0.0, 0.0 );

		return obj;
	}
}

//- - - - - - - - - - - - - - - - - -
//
MManipData SpreadNormalNodeManip::triManipToPlugConvCB( unsigned index ){

	MStatus status;

	MFnNumericData fnNumericData;
	MFnFreePointTriadManip fnTriManip( triManip_ );

	MObject obj = fnNumericData.create( MFnNumericData::k3Double );
	MVector p;
	getConverterManipValue( fnTriManip.pointIndex(), p );
	MMatrix m = getParentWorldInvMatrix();
	p = MPoint( p ) * m;

	fnNumericData.setData( p[0], p[1], p[2] );
	return MManipData( obj );
}


//- - - - - - - - - - - - - - - - - -
//
MManipData SpreadNormalNodeManip::distManipToPlugConvCB( unsigned index ){

	MStatus status;
	MFnDistanceManip fnDistManip( distManip_ );

	double val;
	getConverterManipValue( fnDistManip.distanceIndex(), val );
	return MManipData( val );
}
