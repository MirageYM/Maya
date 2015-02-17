/*
  AlignPlaneManip
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/

#include <maya/MFnPlugin.h>

#include "AlignPlaneManip.hpp"
#include "AlignPlaneNode.hpp"
#include "AlignPlaneNodeManip.hpp"
#include "AlignPlaneCmd.hpp"

#define PLUGIN_VENDOR "MirageWrks"


//--------------------------------------------------------
//! initializePlugin
//--------------------------------------------------------
__declspec(dllexport) MStatus initializePlugin(MObject obj)
{
	MStatus status;
	MFnPlugin plugin( obj, PLUGIN_VENDOR, "6.0", "Any" );

	status = plugin.registerContextCommand(	"AlignPlaneContext",
											&AlignPlaneContext::creator );
	if( !status ){
		MGlobal::displayError( "Error registering AlignPlaneContext command" );
		return status;
	}

	/*
	status = plugin.registerNode(	"AlignPlaneManip",
									AlignPlaneManip::getId(), 
									&AlignPlaneManip::creator,
									&AlignPlaneManip::initialize,
									MPxNode::kManipContainer );
	if( !status ){
		MGlobal::displayError( "Error registering AlignPlaneManip node" );
		return status;
	}
	*/

	status = plugin.registerNode(	"AlignPlaneNodeManip",
									AlignPlaneNodeManip::getId(), 
									&AlignPlaneNodeManip::creator,
									&AlignPlaneNodeManip::initialize,
									MPxNode::kManipContainer );
	if( !status ){
		MGlobal::displayError( "Error registering AlignPlaneNodeManip node" );
		return status;
	}
	
	status = plugin.registerNode(	"AlignPlaneNode",
									AlignPlaneNode::getId(),
									&AlignPlaneNode::creator,
									&AlignPlaneNode::initialize,
									MPxNode::kDependNode );
	if( !status ){
		MGlobal::displayError( "Error registering AlignPlaneNode node" );
		return status;
	}

	status = plugin.registerCommand(	"AlignPlaneCmd",
										AlignPlaneCmd::creator,
										AlignPlaneCmd::syntaxCreator );
	if( !status ){
		MGlobal::displayError( "Error registering AlignPlaneCmd" );
		return status;
	}

	
	

	return status;
}


//--------------------------------------------------------
//! uninitializePlugin
//--------------------------------------------------------
__declspec(dllexport) MStatus uninitializePlugin(MObject obj)
{
	MStatus status;
	MFnPlugin plugin(obj);

	/*
	status = plugin.deregisterContextCommand( "AlignPlaneContext" );
	if( !status ){
		MGlobal::displayError( "Error deregistering AlignPlaneContext command" );
		return status;
	}

	status = plugin.deregisterNode( AlignPlaneManip::getId() );
	if( !status ){
		MGlobal::displayError( "Error deregistering AlignPlaneManip node" );
		return status;
	}
	*/
	
	status = plugin.deregisterNode( AlignPlaneNodeManip::getId() );
	if( !status ){
		MGlobal::displayError( "Error deregistering AlignPlaneNodeManip node" );
		return status;
	}
	
	status = plugin.deregisterNode( AlignPlaneNode::getId() );
	if( !status ){
		MGlobal::displayError( "Error deregistering AlignPlaneNode node" );
		return status;
	}
	
	status = plugin.deregisterCommand( "AlignPlaneCmd" );
	if( !status ){
		MGlobal::displayError( "Error deregistering AlignPlaneCmd" );
		return status;
	}

	return status;
}

