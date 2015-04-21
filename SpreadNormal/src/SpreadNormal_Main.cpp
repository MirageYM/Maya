/*
  SpreadNormalManip
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/

#include <maya/MFnPlugin.h>

#include "SpreadNormalNode.hpp"
#include "SpreadNormalNodeManip.hpp"
#include "SpreadNormalCmd.hpp"

#define PLUGIN_VENDOR "MirageWrks"


//--------------------------------------------------------
//! initializePlugin
//--------------------------------------------------------
__declspec(dllexport) MStatus initializePlugin(MObject obj)
{
	MStatus status;
	MFnPlugin plugin( obj, PLUGIN_VENDOR, "6.0", "Any" );

	status = plugin.registerNode(	"SpreadNormalNodeManip",
									SpreadNormalNodeManip::getId(), 
									&SpreadNormalNodeManip::creator,
									&SpreadNormalNodeManip::initialize,
									MPxNode::kManipContainer );
	if( !status ){
		MGlobal::displayError( "Error registering SpreadNormalNodeManip node" );
		return status;
	}
	
	status = plugin.registerNode(	"SpreadNormalNode",
									SpreadNormalNode::getId(),
									&SpreadNormalNode::creator,
									&SpreadNormalNode::initialize,
									MPxNode::kDependNode );
	if( !status ){
		MGlobal::displayError( "Error registering SpreadNormalNode node" );
		return status;
	}

	status = plugin.registerCommand(	"SpreadNormalCmd",
										SpreadNormalCmd::creator,
										SpreadNormalCmd::syntaxCreator );
	if( !status ){
		MGlobal::displayError( "Error registering SpreadNormalCmd" );
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

	
	status = plugin.deregisterNode( SpreadNormalNodeManip::getId() );
	if( !status ){
		MGlobal::displayError( "Error deregistering SpreadNormalNodeManip node" );
		return status;
	}
	
	status = plugin.deregisterNode( SpreadNormalNode::getId() );
	if( !status ){
		MGlobal::displayError( "Error deregistering SpreadNormalNode node" );
		return status;
	}
	
	status = plugin.deregisterCommand( "SpreadNormalCmd" );
	if( !status ){
		MGlobal::displayError( "Error deregistering SpreadNormalCmd" );
		return status;
	}

	return status;
}

