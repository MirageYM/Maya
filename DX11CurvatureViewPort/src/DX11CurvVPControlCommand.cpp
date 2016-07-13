/*
  DX11CurvVPControlCommand
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/
//Maya
#include <maya/MGlobal.h>

//project
#include "DX11CurvVP.hpp"
#include "DX11CurvVPControlCommand.hpp"


MSyntax C_DX11CurvVPControlCommand::newSyntax()
{
	MSyntax syntax;

	syntax.addFlag( "hs", "heatMapScale", MSyntax::kDouble );
	syntax.addFlag( "vp", "valPower", MSyntax::kDouble );
	syntax.addFlag( "vm", "valMult", MSyntax::kDouble );
	syntax.addFlag( "cmr", "colorMidR", MSyntax::kDouble );
	syntax.addFlag( "cmg", "colorMidG", MSyntax::kDouble );
	syntax.addFlag( "cmb", "colorMidB", MSyntax::kDouble );
	syntax.addFlag( "cpr", "colorPosR", MSyntax::kDouble );
	syntax.addFlag( "cpg", "colorPosG", MSyntax::kDouble );
	syntax.addFlag( "cpb", "colorPosB", MSyntax::kDouble );
	syntax.addFlag( "cnr", "colorNegR", MSyntax::kDouble );
	syntax.addFlag( "cng", "colorNegG", MSyntax::kDouble );
	syntax.addFlag( "cnb", "colorNegB", MSyntax::kDouble );
	syntax.addFlag( "gwx", "gridWidthX", MSyntax::kDouble );
	syntax.addFlag( "gwy", "gridWidthY", MSyntax::kDouble );
	syntax.addFlag( "gwz", "gridWidthZ", MSyntax::kDouble );
	syntax.addFlag( "gdx", "gridDistX", MSyntax::kDouble );
	syntax.addFlag( "gdy", "gridDistY", MSyntax::kDouble );
	syntax.addFlag( "gdz", "gridDistZ", MSyntax::kDouble );
	syntax.addFlag( "gox", "gridOffsetX", MSyntax::kDouble );
	syntax.addFlag( "goy", "gridOffsetY", MSyntax::kDouble );
	syntax.addFlag( "goz", "gridOffsetZ", MSyntax::kDouble );
	syntax.addFlag( "ga", "gridAlpha", MSyntax::kDouble );
	syntax.addFlag( "ca", "checkerAlpha", MSyntax::kDouble );
	syntax.addFlag( "cr", "checkerRepeat", MSyntax::kDouble );
	syntax.addFlag( "amb", "ambient", MSyntax::kDouble );

	syntax.addArg( MSyntax::kString );

	return syntax;
}

MStatus C_DX11CurvVPControlCommand::parseArgsAndSet( const MArgList& args )
{
	MStatus			status;
	MArgDatabase	argData(syntax(), args);

	auto SetFloatParam = [&]( const char* flagName, const char* vpParamName ){
		if( argData.isFlagSet( flagName ) ){
			double val;
			argData.getFlagArgument( flagName, 0, val );
			C_DX11CurvVP::getInstance()->setShaderParam( vpParamName, val );
		}
	};

	SetFloatParam( "hs", "gHeatMapScale" );
	SetFloatParam( "vp", "gValPower" );
	SetFloatParam( "vm", "gValMult" );
	SetFloatParam( "cmr", "gColMidR" );
	SetFloatParam( "cmg", "gColMidG" );
	SetFloatParam( "cmb", "gColMidB" );
	SetFloatParam( "cpr", "gColPosR" );
	SetFloatParam( "cpg", "gColPosG" );
	SetFloatParam( "cpb", "gColPosB" );
	SetFloatParam( "cnr", "gColNegR" );
	SetFloatParam( "cng", "gColNegG" );
	SetFloatParam( "cnb", "gColNegB" );
	SetFloatParam( "gwx", "gGridWidthX" );
	SetFloatParam( "gwy", "gGridWidthY" );
	SetFloatParam( "gwz", "gGridWidthZ" );
	SetFloatParam( "gox", "gGridOffsetX" );
	SetFloatParam( "goy", "gGridOffsetY" );
	SetFloatParam( "goz", "gGridOffsetZ" );
	SetFloatParam( "gdx", "gGridDistX" );
	SetFloatParam( "gdy", "gGridDistY" );
	SetFloatParam( "gdz", "gGridDistZ" );
	SetFloatParam( "ga", "gGridAlpha" );
	SetFloatParam( "ca", "gCheckerAlpha" );
	SetFloatParam( "cr", "gCheckerRepeat" );
	SetFloatParam( "amb", "gAmbient" );
	
	return MS::kSuccess;
}

MStatus C_DX11CurvVPControlCommand::doIt(const MArgList& args)
{
	if (!C_DX11CurvVP::hasInstance() ){
		return MStatus::kFailure;
	}

	MStatus status;

	status = parseArgsAndSet( args );
	if (!status){
		return status;
	}

	return status;
}

void* C_DX11CurvVPControlCommand::creator()
{
	return (void *) (new C_DX11CurvVPControlCommand);
}
