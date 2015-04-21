/*
  SpreadNormalManip
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/
//C
#include <set>
#include <vector>
#include <map>

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
#include "SpreadNormalNode.hpp"

using namespace MayaUtility;

//--------------------------------------------------------
//! SpreadNormalNode
//--------------------------------------------------------
MTypeId SpreadNormalNode::id_( 0xb5b232 );


MObject	SpreadNormalNode::inMesh_;
MObject	SpreadNormalNode::outMesh_;
MObject	SpreadNormalNode::inComponent_;

MObject SpreadNormalNode::pivotPos_;
MObject SpreadNormalNode::pivotPosX_;
MObject SpreadNormalNode::pivotPosY_;
MObject SpreadNormalNode::pivotPosZ_;

MObject SpreadNormalNode::blendRatio_;
MObject SpreadNormalNode::sharedVtxMode_;

MObject SpreadNormalNode::worldMatrix_;
MObject SpreadNormalNode::worldInvMatrix_;

//- - - - - - - - - - - - - - - - - -
//
SpreadNormalNode::SpreadNormalNode() {}


//- - - - - - - - - - - - - - - - - -
//
SpreadNormalNode::~SpreadNormalNode() {}


//- - - - - - - - - - - - - - - - - -
//
MStatus SpreadNormalNode::compute( const MPlug& plug, MDataBlock& data ){

	//- - - - - - - - - - - - - - - - - -
	auto planeProj = [&]( MVector& dir, MVector projPos, MPoint org ){
		MVector v = projPos - org;
		double dot = dir * v;
		return dir * dot + org;
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
			MDataHandle hPivotPos = data.inputValue( pivotPos_, &status );
			CHECK_MSTATUS( status );
			MDataHandle hBrendRatio = data.inputValue( blendRatio_, &status );
			CHECK_MSTATUS( status );
			MDataHandle hWMat = data.inputValue( worldMatrix_, &status );
			CHECK_MSTATUS( status );
			MDataHandle hWInvMat = data.inputValue( worldInvMatrix_, &status );
			CHECK_MSTATUS( status );
			MDataHandle hSharedVtxMode = data.inputValue( sharedVtxMode_, &status );
			CHECK_MSTATUS( status );

			hOutMesh.set( hInMesh.asMesh() );

			MObject inputMeshObj = hInMesh.asMesh();
			MObject outputMeshObj = hOutMesh.asMesh();
			MObject inCompList = hInComp.data();
			MMatrix matWorld = hWMat.asMatrix();
			MMatrix matInvWorld = hWInvMat.asMatrix();
			
			MPoint pivotPos = hPivotPos.asVector();
			MPoint wPivotPos = pivotPos * matWorld;
			double blendRatio = hBrendRatio.asDouble();
			int sharedVtxMode = hSharedVtxMode.asInt();

			//Gather compnent indices
			MFnComponentListData fnCompList( inCompList );

			MFnMesh fnInMesh( inputMeshObj );
			MFnMesh fnMesh( outputMeshObj );
			
			MIntArray	vertexCount;
			MIntArray	vertexList;
			fnMesh.getVertices( vertexCount, vertexList );

			MFloatVectorArray	normals;
			MFloatVectorArray	initialNormals;
			fnInMesh.getNormals( normals );
			fnInMesh.getNormals( initialNormals );

			MIntArray normalCounts;
			MIntArray normalIds;
			fnMesh.getNormalIds( normalCounts, normalIds );


			//Make Lookpu tables first.
			std::map< int, std::set< int > >		vtxToFaceIdLUT;
			std::map< std::pair< int,int >, int >	vtxFaceToNormalIdLUT;
			typedef std::pair<int,int> VtxFace;
			std::set< VtxFace >	selectedFaceVtxInfo;
			
			int currentIndex = 0;
			for( int faceCnt = 0; faceCnt < vertexCount.length(); ++faceCnt ){
				for( int faceVtxCnt = 0; faceVtxCnt < vertexCount[ faceCnt ]; ++faceVtxCnt ){
					if( vtxToFaceIdLUT.count( vertexList[ currentIndex ] ) <= 0 ){
						vtxToFaceIdLUT[ vertexList[ currentIndex ] ] = std::set< int >();
					}
					vtxToFaceIdLUT[ vertexList[ currentIndex ] ].insert( faceCnt );
					vtxFaceToNormalIdLUT[ VtxFace( vertexList[ currentIndex ], faceCnt ) ] = normalIds[ currentIndex ];
					++currentIndex;
				}
			}

			//Gather target vertex, face and normal indices
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
						selectedFaceVtxInfo.insert( VtxFace( tmpArray[j], -1 ) );
					}
				}else if( c.apiType() == MFn::kMeshPolygonComponent ){
					for( unsigned int j = 0; j < tmpArray.length(); ++j ){
						MIntArray	vtxIds;
						fnMesh.getPolygonVertices( tmpArray[j], vtxIds );
						for( unsigned int k = 0; k < vtxIds.length(); ++k ){
							selectedFaceVtxInfo.insert( VtxFace( vtxIds[k], tmpArray[j] ) );
						}
					}
				}
			}

			std::set< int >	normalChk;	//normal processing check

			//spread normals
			//-------------------
			auto blendNormal = [&]( int vId, int fId ){
				
				int normalId = vtxFaceToNormalIdLUT[ VtxFace( vId, fId ) ];
				if( normalChk.count( normalId ) > 0 ){
					return;
				}

				MPoint pp;
				fnMesh.getPoint( vId, pp, MSpace::kObject );
				MVector d = pp - pivotPos;
				d.normalize();

				MVector n;
				n = normals[ normalId ];
				n *= ( 1.0f - fabs( blendRatio ) );
				n += d * blendRatio;
				n.normalize();
				if( sharedVtxMode ){
					normals[ normalId ] = n;
					normalChk.insert( normalId );
				}else{
					fnMesh.setFaceVertexNormal( n, fId, vId );
					//We don't need normal processing check here.
				}
			};
			//-------------------

			MIntArray lockVtxList;
			for( auto itr = selectedFaceVtxInfo.begin(); itr != selectedFaceVtxInfo.end(); ++itr ){
				if( itr->second < 0 ){
					int vtxId = itr->first;
					for( auto lutItr = vtxToFaceIdLUT[ vtxId ].begin(); lutItr != vtxToFaceIdLUT[ vtxId ].end(); ++lutItr ){
						int faceId = *lutItr;
						blendNormal( vtxId, faceId );
						lockVtxList.append( vtxId );
					}
				}else{
					int vtxId = itr->first;
					int faceId = itr->second;
					blendNormal( vtxId, faceId );
					lockVtxList.append( vtxId );
				}
			}

			if( sharedVtxMode ){
				fnMesh.setNormals( normals, MSpace::kObject );
			}
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
void* SpreadNormalNode::creator(){
	return new SpreadNormalNode();
}

//- - - - - - - - - - - - - - - - - -
//
void SpreadNormalNode::vecPlugCreate(	MObject*		pVecObj,
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
MStatus SpreadNormalNode::initialize(){


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
	
	//pivot
	{
		MObject* o[3] = { &pivotPosX_, &pivotPosY_, &pivotPosZ_ };
		const char* n[4][2] = { { "pivotPos", "pv" }, { "pivotPosX", "pvx" }, { "pivotPosY", "pvy" }, { "pivotPosZ", "pvz" } };
		vecPlugCreate(	&pivotPos_, o, n );
	}

	//Scale
	{
		MFnNumericAttribute fnNumAttr;
		blendRatio_ = fnNumAttr.create( "blendRatio", "br", MFnNumericData::kDouble, 1.0, &status );
		fnNumAttr.setWritable( true );
		fnNumAttr.setStorable( true );
		fnNumAttr.setReadable( true );
		fnNumAttr.setChannelBox( true );
		fnNumAttr.setKeyable( true );
		fnNumAttr.setCached( true );
		fnNumAttr.setHidden( false );
		CHECK_MSTATUS( addAttribute( blendRatio_ ) );
	}

	//Mode
	{
		MFnNumericAttribute fnNumAttr;
		sharedVtxMode_ = fnNumAttr.create( "sharedVertexMode", "svm", MFnNumericData::kInt, 1, &status );
		fnNumAttr.setWritable( true );
		fnNumAttr.setStorable( true );
		fnNumAttr.setReadable( true );
		fnNumAttr.setChannelBox( true );
		fnNumAttr.setKeyable( true );
		fnNumAttr.setCached( true );
		fnNumAttr.setHidden( false );
		CHECK_MSTATUS( addAttribute( sharedVtxMode_ ) );
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
	CHECK_MSTATUS( attributeAffects( pivotPos_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( pivotPosX_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( pivotPosY_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( pivotPosZ_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( blendRatio_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( sharedVtxMode_, outMesh_ ) );
	
	CHECK_MSTATUS( attributeAffects( worldMatrix_, outMesh_ ) );
	CHECK_MSTATUS( attributeAffects( worldInvMatrix_, outMesh_ ) );

	MPxManipContainer::addToManipConnectTable( getId() );
	
	return MS::kSuccess;

}


