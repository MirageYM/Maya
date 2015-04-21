/*
  SpreadNormalManip
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/
//C
#include <set>

//Maya
#include <maya/MPlugArray.h>
#include <maya/MFnMesh.h>
#include <maya/MFnComponentListData.h>
#include <maya/MFnComponent.h>
#include <maya/MSelectionList.h>
#include <maya/MItSelectionList.h>
#include <maya/MItMeshPolygon.h>
#include <maya/MSelectionList.h>
#include <maya/MFnDependencyNode.h>
#include <maya/MFnSingleIndexedComponent.h>

//project
#include "maya_utility.hpp"
#include "SpreadNormalNode.hpp"
#include "SpreadNormalCmd.hpp"

using namespace MayaUtility;

//--------------------------------------------------------
//! SpreadNormalCmd
//--------------------------------------------------------

//- - - - - - - - - - - - - - - - - -
//
SpreadNormalCmd::SpreadNormalCmd(): hasTweak_( false ), hasHistory_( false ), isRecordHistory_( 1 ){

	modifyParams_.center_[0] = modifyParams_.center_[1] = modifyParams_.center_[2] = 0.0;
}


//- - - - - - - - - - - - - - - - - -
//
SpreadNormalCmd::~SpreadNormalCmd(){}


//- - - - - - - - - - - - - - - - - -
//
MSyntax SpreadNormalCmd::syntaxCreator( void ){
	MSyntax		syntax;
	return syntax;
}

//- - - - - - - - - - - - - - - - - -
//
void* SpreadNormalCmd::creator( void ){

	return new SpreadNormalCmd();

}

//- - - - - - - - - - - - - - - - - -
//
MStatus SpreadNormalCmd::doIt( const MArgList& arg ){

	tweakIndexArray_.clear();
	tweakVectorArray_.clear();
	
	return performCmd();
}

//- - - - - - - - - - - - - - - - - -
//
MStatus SpreadNormalCmd::undoIt( void ){
	return performUndoCmd();
}

//- - - - - - - - - - - - - - - - - -
//
MStatus SpreadNormalCmd::redoIt( void ){

	MStatus status;
	
	if( !hasHistory_ ){
		status = dagModifier_.doIt();
		CHECK_MSTATUS( status );
	}

	status = dgModifier_.doIt();
	CHECK_MSTATUS( status );

	if( hasTweak_ ){
		cleanupShapeTweakPnts();
	}

	return MS::kSuccess;

}

//- - - - - - - - - - - - - - - - - -
//
bool SpreadNormalCmd::isUndoable( void ) const{
	return true;
}

//- - - - - - - - - - - - - - - - - -
//
MStatus SpreadNormalCmd::performCmd( void ){

	
	MGlobal::executeCommand( "constructionHistory -q -tgl", isRecordHistory_ );
	if( !isRecordHistory_ ){
		#if 1
		displayWarning( "constructionHistory is off. This command will make constructionHistory" );
		#else
		displayError( "constructionHistory is off. This command require constructionHistory turned on" );
		return MS::kFailure;
		#endif
	}
	
	MStatus status;
	
	MSelectionList selList;
	MGlobal::getActiveSelectionList( selList );
	initialSelList_ = selList;
	MItSelectionList selListIter( selList );
	selListIter.setFilter( MFn::kMesh );

	MFnComponentListData fnCompList;
	fnCompList.create();

	int cnt = 0;

	MGlobal::executeCommand( "polyNormalPerVertex -fn true;", false, true );

	for( ; !selListIter.isDone(); selListIter.next() ){
		MDagPath dagPath;
		MObject component;
		selListIter.getDagPath( dagPath, component );

		if( component.apiType() == MFn::kMeshVertComponent ){
			if( cnt == 0 ){
				fnCompList.add( component );
				MFnSingleIndexedComponent fnComp( component );

				targetInfo_.selDagPath_ = dagPath;
				dagPath.extendToShape();
				targetInfo_.targetMeshShapeDagPath_ = dagPath;
				targetInfo_.initialMeshShape_ = dagPath.node();

				++cnt;
			}else{
				displayWarning( "Multiple selection not supoorted." );
				return MS::kFailure;
			}
		}else if( component.apiType() == MFn::kMeshPolygonComponent ){
			if( cnt == 0 ){
				fnCompList.add( component );
				MFnSingleIndexedComponent fnComp( component );

				targetInfo_.selDagPath_ = dagPath;
				dagPath.extendToShape();
				targetInfo_.targetMeshShapeDagPath_ = dagPath;
				targetInfo_.initialMeshShape_ = dagPath.node();

				++cnt;
			}else{
				displayWarning( "Multiple selection not supoorted." );
				return MS::kFailure;
			}
		}
	}

	if( cnt != 1 ){
		return MS::kFailure;
	}
	targetInfo_.selCompList_ = fnCompList.object();

	if( createModifierNode() != MS::kSuccess ){
		return MS::kFailure;
	}

	getInitialParam();
	setInitialParamToNode();

	MGlobal::select( targetInfo_.thisNode_, MGlobal::kReplaceList );
	MGlobal::executeCommand( "ShowManipulators;" );

	return MS::kSuccess;
}


//- - - - - - - - - - - - - - - - - -
//
MStatus SpreadNormalCmd::performUndoCmd( void ){

	MStatus status;
	status = rollbackNodeConnection();
	CHECK_MSTATUS( status );
	
	rollbackTweak();

	MGlobal::setActiveSelectionList( initialSelList_ );
	
	return MS::kSuccess;
}

//- - - - - - - - - - - - - - - - - -
//
MStatus SpreadNormalCmd::createModifierNode( void ){

	MStatus status;
	
	//Check MeshNode
	MFnDagNode fnDagMeshShape( targetInfo_.targetMeshShapeDagPath_.node() );
	if( fnDagMeshShape.parentCount() <= 0 ){
		displayWarning( "No parent transform" );
		return MS::kFailure;
	}
	targetInfo_.transformNode_ = fnDagMeshShape.parent( 0 );

	//create node
	targetInfo_.thisNode_ = dgModifier_.createNode( SpreadNormalNode::getId(), &status );
	CHECK_MSTATUS( status );

	//set param
	MObject compAttr = MFnDependencyNode( targetInfo_.thisNode_ ).attribute( "inComponent" );
	MPlug thisNodeInCompPlug( targetInfo_.thisNode_, compAttr );
	status = thisNodeInCompPlug.setValue( targetInfo_.selCompList_ );
	CHECK_MSTATUS( status );

	MPlug thisNodeInMeshPlug = MFnDependencyNode( targetInfo_.thisNode_ ).findPlug( "inMesh" );
	MPlug thisNodeOutMeshPlug = MFnDependencyNode( targetInfo_.thisNode_ ).findPlug( "outMesh" );
	MPlug thisNodeWMatPlug = MFnDependencyNode( targetInfo_.thisNode_ ).findPlug( "worldMatrix" );
	MPlug thisNodeWInvMatPlug = MFnDependencyNode( targetInfo_.thisNode_ ).findPlug( "worldInverseMatrix" );

	//src/dst plug
	MPlugArray	tempPlugArray;
	
	//reconnect upstream
	MFnDagNode	fnMeshShape( targetInfo_.targetMeshShapeDagPath_ );
	targetInfo_.meshShapeNodeDstPlug_ = fnMeshShape.findPlug( "inMesh" );
	targetInfo_.meshShapeNodeDstAttr_ = targetInfo_.meshShapeNodeDstPlug_.attribute();
	targetInfo_.meshShapeNodeDstPlug_.connectedTo( tempPlugArray, true, false );

	if( tempPlugArray.length() > 1 ){
		displayWarning( "upstream mesh node > 1" );
		return MS::kFailure;
	}else{

		if( !targetInfo_.meshShapeNodeDstPlug_.isConnected() ){
			hasHistory_ = false;
			
			//No history. duplicate current.
			MObject tmpUpstreamTrs = fnDagMeshShape.duplicate( false, false );
			MFnDagNode	fnDagTmpUpstreamTrs( tmpUpstreamTrs );

			if( fnDagTmpUpstreamTrs.childCount() <= 0 ){
				displayWarning( "duplicate failure" );
				return MS::kFailure;
			}
			targetInfo_.upstreamNode_ = fnDagTmpUpstreamTrs.child( 0 );

			status = dagModifier_.reparentNode( targetInfo_.upstreamNode_, targetInfo_.transformNode_ );
			CHECK_MSTATUS( status );

			status = dagModifier_.doIt();
			CHECK_MSTATUS( status );

			MFnDagNode fnUpstreamNode( targetInfo_.upstreamNode_ );
			fnUpstreamNode.setIntermediateObject( true );
			targetInfo_.upstreamSrcAttr_ = fnUpstreamNode.attribute( "outMesh" );
			targetInfo_.upstreamSrcPlug_ = fnUpstreamNode.findPlug( "outMesh", status );
			CHECK_MSTATUS( status );

			status = dagModifier_.deleteNode( tmpUpstreamTrs );
			CHECK_MSTATUS( status );
			status = dagModifier_.doIt();
			CHECK_MSTATUS( status );

			fnUpstreamNode.getPath( targetInfo_.cachedDagPath_ );

		}else{
			hasHistory_ = true;
			
			targetInfo_.upstreamSrcPlug_ = tempPlugArray[0];
			targetInfo_.upstreamSrcAttr_ = tempPlugArray[0].attribute();
			targetInfo_.upstreamNode_ = tempPlugArray[0].node();
			dgModifier_.disconnect( targetInfo_.upstreamSrcPlug_, targetInfo_.meshShapeNodeDstPlug_ );
		}

	}

	//Tweak check
	createTweakNode();
	cleanupShapeTweakPnts();
	
	if( !targetInfo_.tweakNode_.isNull() ){
		{
			MPlug dstPlug( targetInfo_.tweakNode_, targetInfo_.tweakNodeDstAttr_ );
			status = dgModifier_.connect( targetInfo_.upstreamSrcPlug_, dstPlug );
			CHECK_MSTATUS( status );
		}
		
		{
			MPlug srcPlug( targetInfo_.tweakNode_, targetInfo_.tweakNodeSrcAttr_ );
			MPlug dstPlug( targetInfo_.thisNode_, thisNodeInMeshPlug );
			status = dgModifier_.connect( srcPlug, dstPlug );
			CHECK_MSTATUS( status );
		}
		
	}else{
		dgModifier_.connect( targetInfo_.upstreamSrcPlug_, thisNodeInMeshPlug );
	}

	targetInfo_.meshShapeNodeDstPlug_ = fnMeshShape.findPlug( "inMesh" );
	targetInfo_.meshShapeNodeDstAttr_ = targetInfo_.meshShapeNodeDstPlug_.attribute();
	dgModifier_.connect( thisNodeOutMeshPlug, targetInfo_.meshShapeNodeDstPlug_ );

	MPlug srcWorldMatPlug = fnMeshShape.findPlug( "worldMatrix" );
	MPlug srcWorldInvMatPlug = fnMeshShape.findPlug( "worldInverseMatrix" );
		
	dgModifier_.connect( srcWorldMatPlug.elementByLogicalIndex(0), thisNodeWMatPlug );
	dgModifier_.connect( srcWorldInvMatPlug.elementByLogicalIndex(0), thisNodeWInvMatPlug );

	dgModifier_.doIt();

	return MS::kSuccess;

}

//- - - - - - - - - - - - - - - - - -
//
void SpreadNormalCmd::createTweakNode( void ){

	MFnDependencyNode	fnMeshShape( targetInfo_.targetMeshShapeDagPath_.node() );
	MPlug tweakPlug = fnMeshShape.findPlug( "pnts" );

	//Check Tweak vals
	for( unsigned int i = 0; i < tweakPlug.numElements(); ++i ){
		MPlug tweakElem = tweakPlug.elementByPhysicalIndex( i );
		MVector p = plug2MVector<MVector>( tweakElem );
		if( p.x != 0.0f || p.y != 0.0f || p.z != 0.0f ){
			hasTweak_ = true;
			break;
		}
	}

	//Tweak node
	if( !hasTweak_ ){
		return;
	}

	MIntArray			tweakSrcConnectionCountArray;
	MPlugArray			tweakSrcConnectionPlugArray;
	MIntArray			tweakDstConnectionCountArray;
	MPlugArray			tweakDstConnectionPlugArray;

	MObjectArray	tweakDataArray;

	//create tweak node
	targetInfo_.tweakNode_ = dgModifier_.createNode( "polyTweak" );
	MFnDependencyNode	fnTweakNode( targetInfo_.tweakNode_ );
	targetInfo_.tweakNodeSrcAttr_ = fnTweakNode.attribute( "output" );
	targetInfo_.tweakNodeDstAttr_ = fnTweakNode.attribute( "inputPolymesh" );
	MObject tweakNodeTweakAttr = fnTweakNode.attribute( "tweak" );
	
	//scan tweak plugs, gather information for Undo, then disconnect
	for( unsigned int i = 0; i < tweakPlug.numElements(); ++i ){
		MPlug tweakElem = tweakPlug.elementByPhysicalIndex( i );
		if( tweakElem.isNull() ){
			continue;
		}

		MObject	tweakData;
		tweakElem.getValue( tweakData );
		tweakDataArray.append( tweakData );
		MVector v = plug2MVector<MVector>( tweakElem );
		tweakIndexArray_.append( tweakElem.logicalIndex() );
		tweakVectorArray_.append( v );

		for( unsigned int j = 0; j < tweakElem.numChildren(); ++j ){
			MPlug tweakElemChild = tweakElem.child( j );
			if( tweakElemChild.isConnected() ){

				MPlugArray	tmpPlugArray;
				//As src plug
				if( tweakElemChild.connectedTo( tmpPlugArray, false, true ) ){
					tweakSrcConnectionCountArray.append( tmpPlugArray.length() );

					for( unsigned k = 0; k < tmpPlugArray.length(); ++k ){
						tweakSrcConnectionPlugArray.append( tmpPlugArray[i] );
						dgModifier_.disconnect( tweakElemChild, tmpPlugArray[i] );
					}
				}else{
					tweakSrcConnectionCountArray.append( 0 );
				}

				tmpPlugArray.clear();
				//As dst plug
				if( tweakElemChild.connectedTo( tmpPlugArray, true, false ) ){
					tweakDstConnectionCountArray.append( 1 );
					tweakDstConnectionPlugArray.append( tmpPlugArray[0] );
					dgModifier_.disconnect( tmpPlugArray[0], tweakElemChild );
				}else{
					tweakDstConnectionCountArray.append( 0 );
				}

			}else{
				tweakSrcConnectionCountArray.append( 0 );
				tweakDstConnectionCountArray.append( 0 );
			}
		}

	}

	// connect
	MPlug polyTweakPlug( targetInfo_.tweakNode_, tweakNodeTweakAttr );
	int srcOffset = 0;
	int dstOffset = 0;
	for( unsigned int i = 0; i < tweakIndexArray_.length(); ++i ){
		MPlug tweakElem = polyTweakPlug.elementByLogicalIndex( tweakIndexArray_[i] );
		tweakElem.setValue( tweakDataArray[i] );

		for( unsigned int j = 0; j < tweakElem.numChildren(); ++j ){
			MPlug tweakElemChild = tweakElem.child( j );
			if( tweakSrcConnectionCountArray[ i * tweakElem.numChildren() + j ] > 0 ){
				for( int k = 0; k < tweakSrcConnectionCountArray[ i * tweakElem.numChildren() + j ]; ++k ){
					dgModifier_.connect( tweakElemChild, tweakSrcConnectionPlugArray[ srcOffset ] );
					++srcOffset;
				}
			}
			if( tweakDstConnectionCountArray[ i * tweakElem.numChildren() + j ] > 0 ){
				dgModifier_.connect( tweakDstConnectionPlugArray[ dstOffset ], tweakElemChild );
				++dstOffset;
			}
		}
	}

}

//- - - - - - - - - - - - - - - - - -
//
void SpreadNormalCmd::cleanupShapeTweakPnts( void ){

	//cleanup pnts
	MFnDependencyNode fnDepMeshShape( targetInfo_.targetMeshShapeDagPath_.node() );

	MFnNumericData fnNumData;
	fnNumData.create( MFnNumericData::k3Float );
	fnNumData.setData( 0.0f, 0.0f, 0.0f );
	MObject v = fnNumData.object();

	MPlug p = fnDepMeshShape.findPlug( "pnts" );
	if( !p.isNull() ){
		for( unsigned int i = 0; i < tweakIndexArray_.length(); ++i ){
			MPlug tweakElem = p.elementByLogicalIndex( tweakIndexArray_[i] );
			tweakElem.setValue( v );
		}
	}

	if( !hasHistory_ ){
		MFnDependencyNode fnUpstreamShape( targetInfo_.upstreamNode_ );
		p = fnUpstreamShape.findPlug( "pnts" );
		if( !p.isNull() ){
			for( unsigned int i = 0; i < tweakIndexArray_.length(); ++i ){
				MPlug tweakElem = p.elementByLogicalIndex( tweakIndexArray_[i] );
				tweakElem.setValue( v );
			}
		}
	}
}

//- - - - - - - - - - - - - - - - - -
//
MStatus SpreadNormalCmd::rollbackTweak( void ){
	
	if( hasTweak_ ){

		MFnDagNode	fnMeshShape( targetInfo_.targetMeshShapeDagPath_.node() );
		MPlug p = fnMeshShape.findPlug( "pnts" );
		
		if( !p.isNull() ){
			for( unsigned int i = 0; i < tweakIndexArray_.length(); ++i ){

				MFnNumericData fnNumData;
				fnNumData.create( MFnNumericData::k3Float );
				fnNumData.setData( tweakVectorArray_[i][0], tweakVectorArray_[i][1], tweakVectorArray_[i][2] );
				
				MPlug tweakElem = p.elementByLogicalIndex( tweakIndexArray_[i] );
				tweakElem.setValue( fnNumData.object() );
			}
		}
	}
	return MS::kSuccess;
}

//- - - - - - - - - - - - - - - - - -
//
MStatus SpreadNormalCmd::rollbackCachedMesh( void ){

	if( !hasHistory_ ){
		MFnDependencyNode	fnMeshShape( targetInfo_.targetMeshShapeDagPath_.node() );
		MFnDependencyNode	fnCachedMeshShape( targetInfo_.cachedDagPath_.node() );

		MPlug meshDstPlug = fnMeshShape.findPlug( "inMesh" );
		MPlug meshSrcPlug = fnMeshShape.findPlug( "outMesh" );
		MPlug cachedSrcPlug = fnCachedMeshShape.findPlug( "outMesh" );

		#if 0
		if( hasTweak_ ){
			MDGModifier	dgModifier;
			dgModifier.connect( cachedSrcPlug, meshDstPlug );
			dgModifier.doIt();

			MString cmd = MString( "dgeval " ) + fnMeshShape.name() + ".inMesh";
			MGlobal::executeCommand( cmd, false, false );

			dgModifier.undoIt();
			
		}else{
			MObject meshData;
			cachedSrcPlug.getValue( meshData );
			meshSrcPlug.setValue( meshData );
		}
		#else
		MObject meshData;
		cachedSrcPlug.getValue( meshData );
		meshSrcPlug.setValue( meshData );
		#endif
		
	}

	return MS::kSuccess;

}
	
//- - - - - - - - - - - - - - - - - -
//
MStatus SpreadNormalCmd::rollbackNodeConnection( void ){

	MStatus status;
	
	status = dgModifier_.undoIt();
	CHECK_MSTATUS( status );


	if( !hasHistory_ ){
		rollbackCachedMesh();
		status = dagModifier_.undoIt();
		CHECK_MSTATUS( status );
	}

	return MS::kSuccess;
}

//- - - - - - - - - - - - - - - - - -
//
void SpreadNormalCmd::getInitialParam( void ){

	MFnMesh	fnMesh( targetInfo_.targetMeshShapeDagPath_ );
	MMatrix m = targetInfo_.selDagPath_.inclusiveMatrix();

	MPointArray	points;
	fnMesh.getPoints( points, MSpace::kObject );

	MFnComponentListData fnCompList( targetInfo_.selCompList_ );

	MVector faceNormals;
	bool useFaceNormal = false;
	MIntArray	selVertexIndices;
	
	for( unsigned int cnt = 0; cnt < fnCompList.length(); ++cnt ){
		MObject c = fnCompList[cnt];
		if( c.apiType() == MFn::kMeshVertComponent ){

			MFnSingleIndexedComponent fnComp( c );
			fnComp.getElements( selVertexIndices );

		}else if( c.apiType() == MFn::kMeshPolygonComponent ){
			MIntArray	faceIds;
			std::set<int> usedVtxIds;

			MFnSingleIndexedComponent fnComp( c );
			fnComp.getElements( faceIds );

			if( faceIds.length () > 0 ){
				useFaceNormal = true;

				for( unsigned int i = 0; i < faceIds.length(); ++i ){
					MIntArray	vtxIds;
					fnMesh.getPolygonVertices( faceIds[i], vtxIds );
					for( unsigned int j = 0; j < vtxIds.length(); ++j ){
						usedVtxIds.insert( vtxIds[j] );
					}
					MVector n;
					fnMesh.getPolygonNormal( faceIds[i], n, MSpace::kObject );
					faceNormals += n;
				}

				for( auto itr = usedVtxIds.begin(); itr != usedVtxIds.end(); ++itr ){
					selVertexIndices.append( *itr );
				}
			}
		}
	}


	for( unsigned int i = 0; i < selVertexIndices.length(); ++i ){
		modifyParams_.center_ += points[ selVertexIndices[i] ];
	}

	modifyParams_.center_ /= static_cast< double >( selVertexIndices.length() );

}

//- - - - - - - - - - - - - - - - - -
//
void SpreadNormalCmd::setInitialParamToNode( void ){


	MFnDependencyNode( targetInfo_.thisNode_ ).findPlug( "pivotPosX" ).setValue( modifyParams_.center_[0] );
	MFnDependencyNode( targetInfo_.thisNode_ ).findPlug( "pivotPosY" ).setValue( modifyParams_.center_[1] );
	MFnDependencyNode( targetInfo_.thisNode_ ).findPlug( "pivotPosZ" ).setValue( modifyParams_.center_[2] );
	
}

