/*
  AlignPlaneManip
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/
//C
#include <set>

//Maya
#include <maya/MGlobal.h>
#include <maya/MTypes.h>
#include <maya/MPlug.h>
#include <maya/MDataBlock.h>
#include <maya/MDataHandle.h>
#include <maya/MFnMeshData.h>
#include <maya/MFnTypedAttribute.h>
#include <maya/MFnMatrixAttribute.h>
#include <maya/MFnComponentListData.h>
#include <maya/MDagPath.h>
#include <maya/MItDag.h>
#include <maya/MFnMesh.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MPoint.h>
#include <maya/MPointArray.h>
#include <maya/MFnSingleIndexedComponent.h>
#include <maya/MPxManipContainer.h>


//project
#include "maya_utility.hpp"
#include "AlignPlaneNode.hpp"

using namespace MayaUtility;

//--------------------------------------------------------
//! AlignPlaneNode
//--------------------------------------------------------
MTypeId AlignPlaneNode::id_( 0xb5b222 );


MObject	AlignPlaneNode::inMesh_;
MObject	AlignPlaneNode::outMesh_;
MObject	AlignPlaneNode::inComponent_;

MObject AlignPlaneNode::projNormal_;
MObject AlignPlaneNode::projNormalX_;
MObject AlignPlaneNode::projNormalY_;
MObject AlignPlaneNode::projNormalZ_;

MObject AlignPlaneNode::planePos_;
MObject AlignPlaneNode::planePosX_;
MObject AlignPlaneNode::planePosY_;
MObject AlignPlaneNode::planePosZ_;

MObject AlignPlaneNode::pivotPos_;
MObject AlignPlaneNode::pivotPosX_;
MObject AlignPlaneNode::pivotPosY_;
MObject AlignPlaneNode::pivotPosZ_;

MObject AlignPlaneNode::projScale_;

MObject AlignPlaneNode::worldMatrix_;
MObject AlignPlaneNode::worldInvMatrix_;

//- - - - - - - - - - - - - - - - - -
//
AlignPlaneNode::AlignPlaneNode() {}


//- - - - - - - - - - - - - - - - - -
//
AlignPlaneNode::~AlignPlaneNode() {}


//- - - - - - - - - - - - - - - - - -
//
MStatus AlignPlaneNode::compute( const MPlug& plug, MDataBlock& data ){

	//- - - - - - - - - - - - - - - - - -
	struct planeProj{
		inline MVector operator()( MVector& dir, MVector pos, MVector org ){
			MVector v = pos - org;
			double dot = dir * v;
			return dir * dot + org;
		};
	};
	//- - - - - - - - - - - - - - - - - -
	
	MStatus returnStatus;

	MStatus status = MS::kSuccess;

	MDataHandle stateData = data.outputValue( state, &status );
	CHECK_MSTATUS( status );

	if( stateData.asShort() == 0 ){

		if( plug == outMesh_ ){

			MDataHandle hInMesh = data.inputValue( inMesh_, &status );
			CHECK_MSTATUS( status );
			MDataHandle hOutMesh = data.outputValue( outMesh_, &status );
			CHECK_MSTATUS( status );
			MDataHandle hInComp = data.inputValue( inComponent_, &status );
			CHECK_MSTATUS( status );
			MDataHandle hPlanePos = data.inputValue( planePos_, &status );
			CHECK_MSTATUS( status );
			MDataHandle hProjNoraml = data.inputValue( projNormal_, &status );
			CHECK_MSTATUS( status );
			MDataHandle hPivotPos = data.inputValue( pivotPos_, &status );
			CHECK_MSTATUS( status );
			MDataHandle hScale = data.inputValue( projScale_, &status );
			CHECK_MSTATUS( status );
			MDataHandle hWMat = data.inputValue( worldMatrix_, &status );
			CHECK_MSTATUS( status );
			MDataHandle hWInvMat = data.inputValue( worldInvMatrix_, &status );
			CHECK_MSTATUS( status );

			hOutMesh.set( hInMesh.asMesh() );

			MObject inputMeshObj = hInMesh.asMesh();
			MObject outputMeshObj = hOutMesh.asMesh();
			MObject inCompList = hInComp.data();
			MMatrix matWorld = hWMat.asMatrix();
			MMatrix matInvWorld = hWInvMat.asMatrix();
			
			MPoint projPos = hPlanePos.asVector();
			MPoint wProjPos = projPos * matWorld;
			MVector projNormal = hProjNoraml.asVector();
			MVector wProjNormal = projNormal * matWorld;

			double scale = hScale.asDouble();
			
			if( projNormal.length() > 0.0 ){
				projNormal.normalize();
			}

			//Gather compnent indices
			MIntArray	vertexIndices;
			MFnComponentListData fnCompList( inCompList );

			MFnMesh fnMesh( outputMeshObj );
			
			for( unsigned int i = 0; i < fnCompList.length(); ++i ){
				MObject c = fnCompList[i];
				if( !c.hasFn( MFn::kSingleIndexedComponent ) ){
					continue;
				}
				
				MFnSingleIndexedComponent fnComp( c );
				MIntArray	tmpArray;
				fnComp.getElements( tmpArray );
				if( c.apiType() == MFn::kMeshVertComponent ){
					for( unsigned int j = 0; j < tmpArray.length(); ++j ){
						vertexIndices.append( tmpArray[j] );
					}
				}else if( c.apiType() == MFn::kMeshPolygonComponent ){
					std::set<int> usedVtxIds;

					for( unsigned int j = 0; j < tmpArray.length(); ++j ){
						MIntArray	vtxIds;
						fnMesh.getPolygonVertices( tmpArray[j], vtxIds );
						for( unsigned int k = 0; k < vtxIds.length(); ++k ){
							usedVtxIds.insert( vtxIds[k] );
						}
					}
					for( auto itr = usedVtxIds.begin(); itr != usedVtxIds.end(); ++itr ){
						vertexIndices.append( *itr );
					}
				}
			}

			
			//Projection to plane
			MVector pivot;
			
			#if 0
			MPointArray	points;

			fnMesh.getPoints( points, MSpace::kObject );

			for( unsigned int i = 0; i < vertexIndices.length(); ++i ){
				MPoint newPos = planeProj()( projNormal, projPos, points[ vertexIndices[i] ] );
				MVector d = newPos - pp;
				d *= scale;
				points[ vertexIndices[i] ] = pp + d;
				pivot += points[ vertexIndices[i] ];
			}

			fnMesh.setPoints( points, MSpace::kObject );
			#else
//			fnMesh.syncObject();
			
			MPoint pp;
			for( unsigned int i = 0; i < vertexIndices.length(); ++i ){
				fnMesh.getPoint( vertexIndices[i], pp, MSpace::kObject );
				pivot += pp;
				MPoint newPos = planeProj()( projNormal, projPos, pp );
				MVector d = newPos - pp;
				d *= scale;
				fnMesh.setPoint( vertexIndices[i], pp + d, MSpace::kObject );
			}

			#endif

			pivot = pivot / static_cast< double >( vertexIndices.length() );
			
			hPivotPos.set( pivot );
			hOutMesh.setClean();
		}
	}else{
		MDataHandle inputData = data.inputValue( inMesh_, &status );
		MDataHandle outputData = data.outputValue( outMesh_, &status );
		outputData.set( inputData.asMesh() );
	}

	return MS::kSuccess;
}


//- - - - - - - - - - - - - - - - - -
//
void* AlignPlaneNode::creator(){
	return new AlignPlaneNode();
}

//- - - - - - - - - - - - - - - - - -
//
void AlignPlaneNode::vecPlugCreate(	MObject*		pVecObj,
									MObject*		pVecObjElem[3],
									const char*		pNames[4][2],
									bool			isWriteable,
									bool			isHidden,
									bool			isChannelBox )
{
	MStatus status;

	for( unsigned int i = 0; i < 3; ++i ){
		MFnNumericAttribute fnVecElemAttr;
		*(pVecObjElem[i]) = fnVecElemAttr.create( pNames[i+1][0], pNames[i+1][1], MFnNumericData::kDouble, 0.0, &status );
		fnVecElemAttr.setWritable( isWriteable );
		fnVecElemAttr.setStorable( true );
		fnVecElemAttr.setReadable( true );
		fnVecElemAttr.setChannelBox( isChannelBox );
		fnVecElemAttr.setKeyable( true );
		fnVecElemAttr.setCached( true );
		fnVecElemAttr.setHidden( isHidden );
		status = addAttribute( *(pVecObjElem[i]) );
	}

	MFnNumericAttribute fnVecAttr;
	*pVecObj = fnVecAttr.create( pNames[0][0], pNames[0][1], *(pVecObjElem[0]), *(pVecObjElem[1]), *(pVecObjElem[2]), &status );
	fnVecAttr.setWritable( isWriteable );
	fnVecAttr.setStorable( true );
	fnVecAttr.setReadable( true );
	fnVecAttr.setCached( true );
	fnVecAttr.setHidden( isHidden );
	status = addAttribute( *pVecObj );

}

//- - - - - - - - - - - - - - - - - -
//
MStatus AlignPlaneNode::initialize(){


	MStatus					status;

	{
		MFnTypedAttribute		fnTypedAttr;
		inMesh_ = fnTypedAttr.create( "inMesh", "im", MFnMeshData::kMesh );
		fnTypedAttr.setStorable( true );
		fnTypedAttr.setHidden( true );
		CHECK_MSTATUS( addAttribute( inMesh_ ) );
	}

	{
		MFnTypedAttribute		fnTypedAttr;
		outMesh_ = fnTypedAttr.create( "outMesh", "om", MFnMeshData::kMesh );
		fnTypedAttr.setStorable( false );
		fnTypedAttr.setWritable( false );
		fnTypedAttr.setHidden( true );
		CHECK_MSTATUS( addAttribute( outMesh_ ) );
	}

	{
		MFnTypedAttribute		fnTypedAttr;
		inComponent_ = fnTypedAttr.create( "inComponent", "ic", MFnComponentListData::kComponentList );
		fnTypedAttr.setStorable( true );
		fnTypedAttr.setWritable( true );
		fnTypedAttr.setHidden( false );
		CHECK_MSTATUS( addAttribute( inComponent_ ) );
	}


	//Proj normal
	{
		MObject* o[3] = { &projNormalX_, &projNormalY_, &projNormalZ_ };
		const char* n[4][2] = { { "projNormal", "pn" }, { "projNormalX", "pnx" }, { "projNormalY", "pny" }, { "projNormalZ", "pnz" } };
		vecPlugCreate(	&projNormal_, o, n );
	}

	//Plane pos
	{
		MObject* o[3] = { &planePosX_, &planePosY_, &planePosZ_ };
		const char* n[4][2] = { { "planePos", "p" }, { "planePosX", "px" }, { "planePosY", "py" }, { "planePosZ", "pz" } };
		vecPlugCreate(	&planePos_, o, n );
	}
	
	//pivot
	{
		MObject* o[3] = { &pivotPosX_, &pivotPosY_, &pivotPosZ_ };
		const char* n[4][2] = { { "pivotPos", "pv" }, { "pivotPosX", "pvx" }, { "pivotPosY", "pvy" }, { "pivotPosZ", "pvz" } };
		vecPlugCreate(	&pivotPos_, o, n, false, true, false );
	}

	//Scale
	{
		MFnNumericAttribute fnNumAttr;
		projScale_ = fnNumAttr.create( "projScale", "ps", MFnNumericData::kDouble, 1.0, &status );
		fnNumAttr.setWritable( true );
		fnNumAttr.setStorable( true );
		fnNumAttr.setReadable( true );
		fnNumAttr.setChannelBox( true );
		fnNumAttr.setKeyable( true );
		fnNumAttr.setCached( true );
		fnNumAttr.setHidden( false );
		CHECK_MSTATUS( addAttribute( projScale_ ) );
	}

	//world matrix
	{
		MFnMatrixAttribute	fnMatrix;
		worldMatrix_ = fnMatrix.create( "worldMatrix", "wm" );
		fnMatrix.setStorable( false );
		fnMatrix.setConnectable( true );
		CHECK_MSTATUS( addAttribute( worldMatrix_ ) );
	}
	{
		MFnMatrixAttribute	fnMatrix;
		worldInvMatrix_ = fnMatrix.create( "worldInverseMatrix", "wim" );
		fnMatrix.setStorable( false );
		fnMatrix.setConnectable( true );
		CHECK_MSTATUS( addAttribute( worldInvMatrix_ ) );
	}
	

	CHECK_MSTATUS( attributeAffects( inMesh_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( inComponent_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( projNormal_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( projNormalX_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( projNormalY_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( projNormalZ_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( planePos_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( planePosX_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( planePosY_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( planePosZ_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( projScale_, outMesh_ ) );
	
	CHECK_MSTATUS( attributeAffects( worldMatrix_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( worldInvMatrix_, outMesh_ ) );
	
	CHECK_MSTATUS( attributeAffects( inMesh_, pivotPos_ ) );
	CHECK_MSTATUS( attributeAffects( inComponent_, pivotPos_ ) );

	MPxManipContainer::addToManipConnectTable( getId() );
	
	return MS::kSuccess;

}


