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


//Maya
#include <maya/MFnNumericAttribute.h>

//project
#include "maya_utility.hpp"
#include "AlignPlaneManip.hpp"

using namespace MayaUtility;

//--------------------------------------------------------
//! AlignPlaneManip
//--------------------------------------------------------
MTypeId AlignPlaneManip::id( 0xb5b221 );

//- - - - - - - - - - - - - - - - - -
//
AlignPlaneManip::AlignPlaneManip() : numComponents_( 0 ), resetPos_( true ), resetDir_( true )
{

}

//- - - - - - - - - - - - - - - - - -
//
AlignPlaneManip::~AlignPlaneManip(){
	initialPositionsW_.clear();
	initialPositionsL_.clear();
	initialPoints_.clear();
}


//- - - - - - - - - - - - - - - - - -
//
void *AlignPlaneManip::creator( void ){
	 return new AlignPlaneManip();
}


//- - - - - - - - - - - - - - - - - -
//
MStatus AlignPlaneManip::initialize( void ){ 
	MStatus stat;
	stat = MPxManipContainer::initialize();
	return stat;
}


//- - - - - - - - - - - - - - - - - -
//
MStatus AlignPlaneManip::createChildren( void ){
	MStatus stat = MStatus::kSuccess;

//	fScaleManip_ = addScaleManip( "scaleManip", "scale" );
	fTriManip_ = addFreePointTriadManip( "triManip", "tri" );
	fDirManip_ = addDirectionManip( "dirManip", "dir" );
//	MFnDistanceManip fnDirManip( fDirManip_ );
//	fnDirManip.setScalingFactor( 0.0 );
	
	return stat;
}


//- - - - - - - - - - - - - - - - - -
//
MStatus AlignPlaneManip::connectToDependNode( const MObject &node ){
	MStatus stat;
	
	MFnComponent componentFn( component_ );
	MFnDependencyNode nodeFn( node );
	
	numComponents_ = componentFn.elementCount();
	initialPositionsW_.setLength( numComponents_ );
	initialPositionsL_.setLength( numComponents_ );
	initialPoints_.setLength( numComponents_ );
	normal_[0] = normal_[1] = normal_[2] = 0.0;

	MFnTransform transform( meshDagPath_.transform() );
	trsMatrix_ = transform.transformation().asMatrix();
	invTrsMatrix_ = transform.transformation().asMatrixInverse();
	trsMatrix_ = meshDagPath_.inclusiveMatrix();
	invTrsMatrix_ = meshDagPath_.inclusiveMatrixInverse();
	
	unsigned int cnt = 0;
	MItMeshVertex iter( meshDagPath_, component_ );
	for( ; !iter.isDone(); iter.next(), ++cnt ){
		
		if ( cnt >= static_cast< unsigned int >( numComponents_ ) ){
			MGlobal::displayWarning( "More components found than expected." );
			break;
		}
		initialPositionsW_[ cnt ] = iter.position( MSpace::kWorld );
		initialPositionsL_[ cnt ] = iter.position( MSpace::kObject );
		centroid_ += iter.position( MSpace::kWorld );

		{
			MVector v;
			iter.getNormal( v, MSpace::kWorld );
			normal_ += v;
		}

		MPlug verticesArrayPlug = nodeFn.findPlug( "pnts", &stat );
		if ( verticesArrayPlug.isNull() ){
			MGlobal::displayError( "not mesh?" );
			return MS::kFailure;
		}

		MPlug vtxPlug = verticesArrayPlug.elementByLogicalIndex( iter.index(), &stat );
		if( vtxPlug.isNull() ){
			MGlobal::displayError( "no vertices" );
			return MS::kFailure;
		}
			
		initialPoints_[ cnt ] = plug2MVector<MVector>( vtxPlug );
		unsigned int plugIndex = addManipToPlugConversion( vtxPlug );
		
		if( plugIndex != static_cast< unsigned int >( cnt ) ){
			MGlobal::displayError("Unexpected plug index returned.");
			return MS::kFailure;
		}
	}
	
	
	centroid_ = centroid_ / numComponents_;
	normal_.normalize();
	
	MFnFreePointTriadManip fnTriManip( fTriManip_ );
	fnTriManip.setDirection( normal_ );
	fnTriManip.setPoint( centroid_ );

	MFnDirectionManip fnDirManip( fDirManip_ );
	fnDirManip.setStartPoint( centroid_ );
	fnDirManip.setDirection( normal_ );
	fnDirManip.setDrawStart( false );
	fnDirManip.setNormalizeDirection( true );

	resetPos_ = true;
	resetDir_ = true;

	addPlugToManipConversion( fnTriManip.pointIndex() );
	addPlugToManipConversion( fnDirManip.directionIndex() );
	

	finishAddingManips();
	MPxManipContainer::connectToDependNode( node );
	
	return stat;
}


//- - - - - - - - - - - - - - - - - -
//
void AlignPlaneManip::draw(	M3dView &view, 
							const MDagPath &path, 
							M3dView::DisplayStyle style,
							M3dView::DisplayStatus status)
{
	MPxManipContainer::draw(view, path, style, status);
}

//- - - - - - - - - - - - - - - - - -
//
MManipData AlignPlaneManip::plugToManipConversion( unsigned index ){
	MObject obj = MObject::kNullObj;

	MFnFreePointTriadManip fnTriManip( fTriManip_ );
	MFnDirectionManip fnDirManip( fDirManip_ );

	if( 0 ){


	}else if( index == fnTriManip.pointIndex() ){
		
		MFnNumericData numericData;
		obj = numericData.create( MFnNumericData::k3Double );
		
		if( resetPos_ ){
			numericData.setData( centroid_.x, centroid_.y, centroid_.z );
			resetPos_ = false;
			fnTriManip.setDirection( normal_ );
//			fnDirManip.setStartPoint( centroid_ );
//			fnDirManip.setDirection( normal_ );
		}else{
			MPoint v;
			getConverterManipValue( fnTriManip.pointIndex(), v );
			numericData.setData( v.x, v.y, v.z );
			fnTriManip.setDirection( normal_ );
//			fnDirManip.setStartPoint( v );
//			fnDirManip.setDirection( normal_ );
		}
		
		return MManipData( obj );

	}else if( index == fnDirManip.directionIndex() ){

		MFnNumericData numericData;
		obj = numericData.create( MFnNumericData::k3Double );
		
		#if 1
		if( resetDir_){
			numericData.setData( normal_.x, normal_.y, normal_.z );
			resetDir_ = false;
		}else{
			MVector v;
			getConverterManipValue( fnDirManip.directionIndex(), v );
			v.normalize();
			numericData.setData( v.x, v.y, v.z );
			normal_ = v;
		}
		#else
		numericData.setData( normal_.x, normal_.y, normal_.z );
		#endif
		
		return MManipData( obj );
		
	}else{
		MGlobal::displayError("Invalid index in plugToManipConversion()!");

		// For invalid indices, return vector of 0's
		MFnNumericData numericData;
		obj = numericData.create( MFnNumericData::k3Double );
		numericData.setData( 0.0, 0.0, 0.0);

		return obj;
	}
}

//- - - - - - - - - - - - - - - - - -
//
MStatus AlignPlaneManip::doRelease( void ){
	
	return MS::kSuccess;
}

//- - - - - - - - - - - - - - - - - -
//
MManipData AlignPlaneManip::manipToPlugConversion( unsigned index ){

	auto planeProj = [&]( MVector& dir, MVector pos, MVector org ){
		MVector v = pos - org;
		double dot = dir * v;
		return dir * dot + org;
	};
	
	MObject obj = MObject::kNullObj;

	MFnFreePointTriadManip fnTriManip( fTriManip_ );
	MFnDistanceManip fnDirManip( fDirManip_ );

	/*
	{
		MVector n;
		getConverterManipValue( fnDirManip.directionIndex(), n );
		n.normalize();
		normal_ = n;
	}
	  */

	if( index < static_cast< unsigned int >( numComponents_ ) ){
		MVector v;
		getConverterManipValue( fnTriManip.pointIndex(), v );

		MVector projPos = planeProj( normal_, v, initialPositionsW_[ index ] );
		MVector pointDW = projPos - initialPositionsW_[ index ];
		MVector pointD = pointDW * invTrsMatrix_;
		MVector newPosition = initialPoints_[ index ] + pointD;
		
		MFnNumericData numericData;
		obj = numericData.create( MFnNumericData::k3Double );
		numericData.setData( newPosition.x, newPosition.y, newPosition.z );

		return MManipData(obj);
	}else{
		MGlobal::displayError("Invalid index in callback!");
	}

	MFnNumericData numericData;
	obj = numericData.create( MFnNumericData::k3Double );
	numericData.setData( 0.0, 0.0, 0.0 );

	return obj;
}


//--------------------------------------------------------
//! AlignPlaneContextObject
//--------------------------------------------------------
//- - - - - - - - - - - - - - - - - -
//
AlignPlaneContextObject::AlignPlaneContextObject(){
	MString str( "" );
	setTitleString( str );
}

//- - - - - - - - - - - - - - - - - -
//
AlignPlaneContextObject::~AlignPlaneContextObject(){
}

//- - - - - - - - - - - - - - - - - -
//
void AlignPlaneContextObject::toolOnSetup( MEvent& ){
	MString str( "" );
	setHelpString(str);

	updateManipulators(this);
	MStatus status;
	id1 = MModelMessage::addCallback(MModelMessage::kActiveListModified,
									 updateManipulators, 
									 this, &status);
	if (!status) {
		MGlobal::displayError( "Model addCallback failed" );
	}
}


//- - - - - - - - - - - - - - - - - -
//
void AlignPlaneContextObject::toolOffCleanup( void ){
	MStatus status;
	status = MModelMessage::removeCallback(id1);
	if (!status) {
		MGlobal::displayError("Model remove callback failed");
	}
	MPxContext::toolOffCleanup();
}


//- - - - - - - - - - - - - - - - - -
//
void AlignPlaneContextObject::updateManipulators( void* data ){
	MStatus stat = MStatus::kSuccess;
	
	AlignPlaneContextObject * ctxPtr = reinterpret_cast< AlignPlaneContextObject* >( data );
	ctxPtr->deleteManipulators(); 

	MSelectionList list;
	stat = MGlobal::getActiveSelectionList(list);
	MItSelectionList iter( list, MFn::kInvalid, &stat );

	if( MS::kSuccess == stat ){
		for (; !iter.isDone(); iter.next()) {

			MDagPath dagPath;
			MObject components;
			iter.getDagPath( dagPath, components );

			if ( components.isNull() || !components.hasFn(MFn::kComponent )){
				MGlobal::displayWarning("Object in selection list is not a component.");
				continue;
			}

			// Add manipulator to the selected object
			//
			MString manipName ("AlignPlaneManip");
			MObject manipObject;
			AlignPlaneManip* manipulator = reinterpret_cast< AlignPlaneManip* >( AlignPlaneManip::newManipulator( manipName, manipObject) );

			if( manipulator ){
				// Add the manipulator
				ctxPtr->addManipulator( manipObject );

				// Connect the manipulator to the object in the selection list.
				manipulator->setMeshDagPath( dagPath );
				manipulator->setComponentObject( components );
				if ( !manipulator->connectToDependNode( dagPath.node() ) ){
					MGlobal::displayWarning("Error connecting manipulator to object");
				}
			} 
		}
	}
}


//--------------------------------------------------------
//! AlignPlaneContext
//--------------------------------------------------------
//- - - - - - - - - - - - - - - - - -
//
MPxContext *AlignPlaneContext::makeObj( void ){
	return new AlignPlaneContextObject();
}

//- - - - - - - - - - - - - - - - - -
//
void *AlignPlaneContext::creator( void ){
	return new AlignPlaneContext;
}



