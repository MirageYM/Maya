/*
  DX11CurvVP_Main
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/

#include <maya/MFnPlugin.h>

#include "DX11CurvVP.hpp"
#include "DX11CurvVPControlCommand.hpp"

#define PLUGIN_VENDOR "MirageWrks"

//--------------------------------------------------------
//! initializePlugin
//--------------------------------------------------------
__declspec(dllexport) MStatus initializePlugin(MObject obj)
{
	MStatus status;
	MFnPlugin plugin( obj, PLUGIN_VENDOR, "1.0", "Any" );

	MHWRender::MRenderer* renderer = MHWRender::MRenderer::theRenderer();
	if( renderer ){
		renderer->registerOverride( C_DX11CurvVP::getInstance() );
	}

	status = plugin.registerCommand( "DX11CurvViewPortControl",
									 C_DX11CurvVPControlCommand::creator,
									 C_DX11CurvVPControlCommand::newSyntax );
	
	return status;
}


//--------------------------------------------------------
//! uninitializePlugin
//--------------------------------------------------------
__declspec(dllexport) MStatus uninitializePlugin(MObject obj)
{
	MStatus status;
	MFnPlugin plugin(obj);

	MHWRender::MRenderer* renderer = MHWRender::MRenderer::theRenderer();
	if( renderer ){
		if( C_DX11CurvVP::hasInstance() ){
			renderer->deregisterOverride( C_DX11CurvVP::getInstance() );
			C_DX11CurvVP::releaseInstance();
		}
	}

	status = plugin.deregisterCommand( "DX11CurvViewPortControl" );
	
	return status;
}

