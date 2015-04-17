/*
  AlignPlaneManip
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
#include "AlignPlaneNodeManip.hpp"

using namespace MayaUtility;

//--------------------------------------------------------
//! AlignPlaneNodeManip
//--------------------------------------------------------
MTypeId AlignPlaneNodeManip::id_( 0xb5b223 );

//- - - - - - - - - - - - - - - - - -
//
AlignPlaneNodeManip::AlignPlaneNodeManip()
{

}

//- - - - - - - - - - - - - - - - - -
//
AlignPlaneNodeManip::~AlignPlaneNodeManip(){
}


//- - - - - - - - - - - - - - - - - -
//
void *AlignPlaneNodeManip::creator( void ){
	 return new AlignPlaneNodeManip();
}


//- - - - - - - - - - - - - - - - - -
//
MStatus AlignPlaneNodeManip::initialize( void ){ 
	MStatus stat;
	stat = MPxManipContainer::initialize();
	return stat;
}


//- - - - - - - - - - - - - - - - - -
//
MStatus AlignPlaneNodeManip::createChildren( void ){
	MStatus stat = MStatus::kSuccess;

	triManip_ = addFreePointTriadManip( "triManip", "tri" );
	dirManip_ = addDirectionManip( "dirManip", "dir" );
	distManip_ = addDistanceManip( "distManip", "dist" );
	boxSize_ = 2.0f;
	
	return stat;
}


//- - - - - - - - - - - - - - - - - -
//
MStatus AlignPlaneNodeManip::connectToDependNode( const MObject &node ){
	MStatus status;
	
	DebugPrintf( "nodeType:%s", node.apiTypeStr() );
	DebugPrintf( "name:%s", MFnDependencyNode( node ).name().asChar() );
	
	parentNode_ = node;
	MFnDependencyNode fnParentNode( parentNode_ );
	MPlug trsPlug = fnParentNode.findPlug( "planePos", &status );
	MPlug normalPlug = fnParentNode.findPlug( "projNormal", &status );
	MPlug pivotPlug = fnParentNode.findPlug( "pivotPos", &status );
	MPlug scalePlug = fnParentNode.findPlug( "projScale", &status );

	//Tri
	MFnFreePointTriadManip fnTriManip( triManip_ );
	fnTriManip.setGlobalTriadPlane( MFnFreePointTriadManip::kViewPlane );
	addPlugToManipConversionCallback( fnTriManip.pointIndex(), (plugToManipConversionCallback)&AlignPlaneNodeManip::plugToManipConvCB );
	addManipToPlugConversionCallback( trsPlug,  (manipToPlugConversionCallback)&AlignPlaneNodeManip::triManipToPlugConvCB );

	//Dir
	MFnDirectionManip fnDirManip( dirManip_ );
	fnDirManip.setNormalizeDirection( false );
	addPlugToManipConversionCallback( fnDirManip.directionIndex(), (plugToManipConversionCallback)&AlignPlaneNodeManip::plugToManipConvCB );
	addPlugToManipConversionCallback( fnDirManip.startPointIndex(), (plugToManipConversionCallback)&AlignPlaneNodeManip::plugToManipConvCB );
	addPlugToManipConversionCallback( fnDirManip.endPointIndex(), (plugToManipConversionCallback)&AlignPlaneNodeManip::plugToManipConvCB );
	addManipToPlugConversionCallback( normalPlug,  (manipToPlugConversionCallback)&AlignPlaneNodeManip::dirManipToPlugConvCB );

	//Dist
	MFnDistanceManip fnDistManip( distManip_ );
	addPlugToManipConversionCallback( fnDistManip.distanceIndex(), (plugToManipConversionCallback)&AlignPlaneNodeManip::plugToManipConvCB );
	addManipToPlugConversionCallback( scalePlug,  (manipToPlugConversionCallback)&AlignPlaneNodeManip::distManipToPlugConvCB );
	

	finishAddingManips();
	MPxManipContainer::connectToDependNode( node );

	return MS::kSuccess;
}


//- - - - - - - - - - - - - - - - - -
//
void AlignPlaneNodeManip::draw(	M3dView &view, 
								const MDagPath &path, 
								M3dView::DisplayStyle style,
								M3dView::DisplayStatus status)
{
	
	MPxManipContainer::draw( view, path, style, status );
	view.beginGL();
	glPushAttrib( GL_CURRENT_BIT );

	glMatrixMode( GL_MODELVIEW );
	glPushMatrix();
	
	glTranslated( wPlanePos_[0], wPlanePos_[1], wPlanePos_[2] );
	glMultMatrixd( wPlaneRotMat_[0] );

	glDisable( GL_LIGHTING );
	glEnable( GL_BLEND );
	glEnable( GL_DEPTH_TEST );
	glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );

	glBegin( GL_QUADS );
	{
		glColor4f( 0.7f, 0.15f, 0.15f, 0.3f );
		glVertex3f( -boxSize_, -0.0001f, -boxSize_ );
		glVertex3f( -boxSize_, -0.0001f, boxSize_ );
		glVertex3f( boxSize_, -0.0001f, boxSize_ );
		glVertex3f( boxSize_, -0.0001f, -boxSize_ );
	}
	glEnd();

	glPopMatrix();

	glPopAttrib();
	view.endGL();

}


//- - - - - - - - - - - - - - - - - -
//
MVector AlignPlaneNodeManip::getParentPlugPointVal( const MMatrix& m, const char* plugName ){
	MStatus status;

	MFnDependencyNode fnParentNode( parentNode_ );
	MPlug trsPlug = fnParentNode.findPlug( plugName, &status );

	MPoint p = plug2MVector<MPoint>( trsPlug );

	p = p * m;

	return MVector( p );
}
	
//- - - - - - - - - - - - - - - - - -
//
MVector AlignPlaneNodeManip::getParentPlugVecVal( const MMatrix& m, const char* plugName ){
	MStatus status;

	MFnDependencyNode fnParentNode( parentNode_ );
	MPlug trsPlug = fnParentNode.findPlug( plugName, &status );

	MVector p = plug2MVector<MVector>( trsPlug );

	p = p * m;

	return MVector( p );
}

//- - - - - - - - - - - - - - - - - -
//
MMatrix AlignPlaneNodeManip::getParentWorldMatrix( void ){
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
MMatrix AlignPlaneNodeManip::getParentWorldInvMatrix( void ){
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
MManipData AlignPlaneNodeManip::plugToManipConvCB( unsigned index ){
	

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
		MVector p = getParentPlugPointVal( getParentWorldMatrix(), "planePos" );
		MVector pv = getParentPlugPointVal( getParentWorldMatrix(), "pivotPos" );
		MVector n = getParentPlugVecVal( getParentWorldMatrix(), "projNormal" );
		wPlanePos_ = MPoint( p );
		
		MVector nn = n;
		nn.normalize();
		MVector v = p - pv;
		double d = nn * v;

		fnDirManip.setStartPoint( MPoint( pv ) );
		fnDistManip.setStartPoint( MPoint( pv ) );
		
		fnNumericData.setData( p[0], p[1], p[2] );
		return MManipData( obj );

	//Dir
	}else if( index == fnDirManip.startPointIndex() ){
		MObject obj = fnNumericData.create( MFnNumericData::k3Double );
		MVector p = getParentPlugPointVal( getParentWorldMatrix(), "pivotPos" );
		
		fnNumericData.setData( p[0], p[1], p[2] );
		return MManipData( obj );
		
	}else if( index == fnDirManip.endPointIndex() ){
		MObject obj = fnNumericData.create( MFnNumericData::k3Double );
		MVector p = getParentPlugPointVal( getParentWorldMatrix(), "pivotPos" );
		MVector n = getParentPlugVecVal( getParentWorldMatrix(), "projNormal" );
		p += n;
		
		fnNumericData.setData( p[0], p[1], p[2] );
		return MManipData( obj );
		
	}else if( index == fnDirManip.directionIndex() ){
		MObject obj = fnNumericData.create( MFnNumericData::k3Double );
		MVector n = getParentPlugVecVal( getParentWorldMatrix(), "projNormal" );

		fnNumericData.setData( n[0], n[1], n[2] );

		n.normalize();
		fnDistManip.setDirection( n );

		MVector refVec( 0.0, 1.0, 0.0 );
		MVector rVec = refVec ^ n;
		MTransformationMatrix rotMat;
		rotMat.setToRotationAxis( rVec, acos( n.y ) );
		MEulerRotation er = rotMat.eulerRotation();
		wPlaneRotMat_ = er.asMatrix();

		fnTriManip.setDirection( er.asVector() );
		
		return MManipData( obj );

	//Dist
	}else if( index == fnDistManip.distanceIndex() ){
		MFnDependencyNode fnParentNode( parentNode_ );
		MPlug p = fnParentNode.findPlug( "projScale" );
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
MManipData AlignPlaneNodeManip::triManipToPlugConvCB( unsigned index ){

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
MManipData AlignPlaneNodeManip::dirManipToPlugConvCB( unsigned index ){

	MStatus status;

	MFnNumericData fnNumericData;

	MFnDirectionManip fnDirManip( dirManip_ );
	MObject obj = fnNumericData.create( MFnNumericData::k3Double );
	MVector p;
	getConverterManipValue( fnDirManip.directionIndex(), p );
	MMatrix m = getParentWorldInvMatrix();
	p = p * m;

	fnNumericData.setData( p[0], p[1], p[2] );
	return MManipData( obj );
}

//- - - - - - - - - - - - - - - - - -
//
MManipData AlignPlaneNodeManip::distManipToPlugConvCB( unsigned index ){

	MStatus status;
	MFnDistanceManip fnDistManip( distManip_ );

	double val;
	getConverterManipValue( fnDistManip.distanceIndex(), val );
	return MManipData( val );
}
