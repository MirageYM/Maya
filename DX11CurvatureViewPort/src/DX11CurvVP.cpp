/*
  DX11CurvVP
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/
//C++
#include <assert.h>

//Maya
#include <maya/M3dView.h>
#include <maya/MDrawTraversal.h>
#include <maya/MHWGeometry.h>
#include <maya/MGeometryExtractor.h>
#include <maya/MDagPath.h>
#include <maya/MFnDagNode.h>
#include <maya/MGeometryExtractor.h>


#include "DX11CurvVP.hpp"
#include "DX11CurvVPUserRenderOp.hpp"
typedef C_DX11CurvVPUserRenderOp CurvatureClass;

//--------------------------------------------------------
//! C_DX11CurvVP
//--------------------------------------------------------

C_DX11CurvVP* C_DX11CurvVP::instance_ = nullptr;

//- - - - - - - - - - - - - - - - - -
//
C_DX11CurvVP::C_DX11CurvVP( const MString& name ):
	MRenderOverride( name ),
	uiName_( "DX11CurvVP" )
{
	
	for( unsigned int i = 0; i < kOperationCount; ++i ){
		renderOperations_[i] = nullptr;
		renderOperationsEnabled_[i] = true;
	}

	renderOperations_[kUserOpCurv] = new CurvatureClass( "user" );
	renderOperations_[kPresentOp] = new C_PresentOp( "present" );

	currentOperation_ = -1;
}

//- - - - - - - - - - - - - - - - - -
//
C_DX11CurvVP::~C_DX11CurvVP(){
	
	for( unsigned int i = 0; i < kOperationCount; ++i ){
		if( renderOperations_[i] ){
			delete renderOperations_[i];
			renderOperations_[i] = nullptr;
		}
	}

}

//- - - - - - - - - - - - - - - - - -
//
C_DX11CurvVP* C_DX11CurvVP::getInstance( void ){
	if( !C_DX11CurvVP::instance_ ){
		C_DX11CurvVP::instance_ = new C_DX11CurvVP( "DX11CurvVP" );
	}
	return C_DX11CurvVP::instance_;
}

//- - - - - - - - - - - - - - - - - -
//
void C_DX11CurvVP::releaseInstance( void ){
	if( C_DX11CurvVP::instance_ ){
		delete C_DX11CurvVP::instance_;
		C_DX11CurvVP::instance_ = nullptr;
	}
}

//- - - - - - - - - - - - - - - - - -
//
MHWRender::DrawAPI C_DX11CurvVP::supportedDrawAPIs( void ) const{
	return ( MHWRender::kDirectX11 );
}

//- - - - - - - - - - - - - - - - - -
//
bool C_DX11CurvVP::startOperationIterator( void ){
	currentOperation_ = 0;
	return true;

}

//- - - - - - - - - - - - - - - - - -
//
MHWRender::MRenderOperation* C_DX11CurvVP::renderOperation( void ){
	
	if( currentOperation_ >= 0 && currentOperation_ < kOperationCount ){
		while( !renderOperations_[currentOperation_] || !renderOperationsEnabled_[currentOperation_] ){
			currentOperation_++;
			if( currentOperation_ >= kOperationCount ){
				return nullptr;
			}
		}

		if( renderOperations_[currentOperation_] ){
			return renderOperations_[currentOperation_];
		}
	}
	return nullptr;

}

//- - - - - - - - - - - - - - - - - -
//
bool C_DX11CurvVP::nextRenderOperation( void ){

	currentOperation_++;
	if( currentOperation_ < kOperationCount ){
		return true;
	}
	
	return false;
}

//- - - - - - - - - - - - - - - - - -
//
MStatus C_DX11CurvVP::setup( const MString& destination ){

	try{
		updateRenderTargets();
		updateParameters();
		updatePass( destination );
	}catch(...){
		return MStatus::kFailure;
	}
		

	if( renderOperationsEnabled_[ kUserOpCurv ] && renderOperations_[ kUserOpCurv ] ){
		reinterpret_cast<CurvatureClass*>( renderOperations_[kUserOpCurv] )->setPanelName( destination );
	}

	return MStatus::kSuccess;

}

//- - - - - - - - - - - - - - - - - -
//
void C_DX11CurvVP::updateRenderTargets( void ){

	if( !reinterpret_cast<CurvatureClass*>( renderOperations_[kUserOpCurv] )->getOutputRenderBuffer() ){
		try{
			reinterpret_cast<CurvatureClass*>( renderOperations_[kUserOpCurv] )->initRenderTargets();
		}catch(...){
			throw;
		}
	}
	MHWRender::MRenderTarget* output = nullptr;
	if( renderOperationsEnabled_[ kUserOpCurv ] && renderOperations_[ kUserOpCurv ] ){
		output = reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->getOutputRenderBuffer();
	}
	reinterpret_cast<C_PresentOp*>( renderOperations_[kPresentOp] )->setRenderTarget( output );
}

//- - - - - - - - - - - - - - - - - -
//
void C_DX11CurvVP::updateParameters( void ){



}

//- - - - - - - - - - - - - - - - - -
//
void C_DX11CurvVP::updatePass( const MString& destination ){

	if( renderOperationsEnabled_[ kUserOpCurv ] && renderOperations_[ kUserOpCurv ] ){
		reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->setPanelName( destination );
	}

}

//- - - - - - - - - - - - - - - - - -
//
MStatus C_DX11CurvVP::cleanup( void ){
	currentOperation_ = -1;
	reinterpret_cast<C_PresentOp*>( renderOperations_[kPresentOp] )->setRenderTarget( nullptr );
	#if 1
	//avoid crush when plugin re-initialized.
	if( renderOperationsEnabled_[ kUserOpCurv ] && renderOperations_[ kUserOpCurv ] ){
		reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->releaseRenderTargets();
	}
	#endif
	return MStatus::kSuccess;
}

//- - - - - - - - - - - - - - - - - -
//
void C_DX11CurvVP::setShaderParam( const MString& paramName, double val ){

	if( paramName == MString( "gValPower" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gValPower = val;
		}
	}
	if( paramName == MString( "gValMult" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gValMult = val;
		}
	}
	if( paramName == MString( "gColMidR" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gColMid.f[0] = val;
		}
	}
	if( paramName == MString( "gColMidG" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gColMid.f[1] = val;
		}
	}
	if( paramName == MString( "gColMidB" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gColMid.f[2] = val;
		}
	}
	if( paramName == MString( "gColPosR" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gColPos.f[0] = val;
		}
	}
	if( paramName == MString( "gColPosG" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gColPos.f[1] = val;
		}
	}
	if( paramName == MString( "gColPosB" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gColPos.f[2] = val;
		}
	}
	if( paramName == MString( "gColNegR" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gColNeg.f[0] = val;
		}
	}
	if( paramName == MString( "gColNegG" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gColNeg.f[1] = val;
		}
	}
	if( paramName == MString( "gColNegB" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gColNeg.f[2] = val;
		}
	}

	if( paramName == MString( "gGridWidthX" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gGridWidth.f[0] = val;
		}
	}
	if( paramName == MString( "gGridWidthY" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gGridWidth.f[1] = val;
		}
	}
	if( paramName == MString( "gGridWidthZ" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gGridWidth.f[2] = val;
		}
	}
	if( paramName == MString( "gGridOffsetX" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gGridOffset.f[0] = val;
		}
	}
	if( paramName == MString( "gGridOffsetY" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gGridOffset.f[1] = val;
		}
	}
	if( paramName == MString( "gGridOffsetZ" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gGridOffset.f[2] = val;
		}
	}
	if( paramName == MString( "gGridDistX" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gGridDist.f[0] = val;
		}
	}
	if( paramName == MString( "gGridDistY" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gGridDist.f[1] = val;
		}
	}
	if( paramName == MString( "gGridDistZ" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gGridDist.f[2] = val;
		}
	}
	if( paramName == MString( "gGridAlpha" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gGridAlpha = val;
		}
	}
	if( paramName == MString( "gCheckerAlpha" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gCheckerAlpha = val;
		}
	}
	if( paramName == MString( "gCheckerRepeat" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gCheckerRepeat = val;
		}
	}
	if( paramName == MString( "gAmbient" ) ){
		if( renderOperations_[ kUserOpCurv ] ){
			reinterpret_cast<CurvatureClass*>( renderOperations_[ kUserOpCurv ] )->commonShaderParameter().gAmbient = val;
		}
	}

}
