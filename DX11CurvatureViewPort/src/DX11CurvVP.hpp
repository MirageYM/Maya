/*
  DX11CurvVP
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/

#pragma once

#if !defined( DX11CURVVP_HPP_INCLUDED__ )
#define DX11CURVVP_HPP_INCLUDED__

#include <maya/MIOStream.h>
//C
#include <stdio.h>
#include <stdlib.h>
#include <vector>
#include <memory>
#include <list>
#include <map>

// Includes for DX
#include <d3d11.h>
#include <d3dx11.h>
#include <d3dcompiler.h>
#include <DirectXMath.h>

//Maya
#include <maya/MGlobal.h>
#include <maya/MString.h>
#include <maya/MColor.h>
#include <maya/MViewport2Renderer.h>
#include <maya/MRenderTargetManager.h>
#include <maya/MShaderManager.h>
#include <maya/MDrawContext.h>
#include <maya/MStateManager.h>

#if MAYA_VERSION >= 20160
typedef MHWRender::MRenderTarget* const* PPRenderTarget;
#else
typedef MHWRender::MRenderTarget** PPRenderTarget;
#endif
//--------------------------------------------------------
//! C_DX11CurvVP
//! 
//
//--------------------------------------------------------
class C_DX11CurvVP: public MHWRender::MRenderOverride{
 public:
	//Enumerations
	enum
	{
		kUserOpCurv = 0,
		kPresentOp,
		kOperationCount
	};

 protected:
	//Creators
	C_DX11CurvVP( const MString& name );
	virtual ~C_DX11CurvVP();

 public:
	//Manipulators
	virtual MHWRender::DrawAPI				supportedDrawAPIs		( void ) const override;
	virtual bool							startOperationIterator	( void ) override;
	virtual MHWRender::MRenderOperation*	renderOperation			( void ) override;
	virtual bool							nextRenderOperation		( void ) override;
	virtual MStatus							setup					( const MString& destination ) override;
	virtual MStatus							cleanup					( void ) override;
	
	virtual void							setShaderParam			( const MString& paramName,
																	  double val );
	
	inline virtual MString					uiName		( void ) const override{ return uiName_; };

	static bool								hasInstance( void ){ return C_DX11CurvVP::instance_ ? true : false; };
	static C_DX11CurvVP*						getInstance	( void );
	static void								releaseInstance( void );

 protected:
	//Manipulators
	virtual void							updateRenderTargets		( void );
	virtual void							updateParameters		( void );
	virtual void							updatePass				( const MString& panelName );
	

 protected:
	//Members
	MString							uiName_;
	MHWRender::MRenderOperation*	renderOperations_[kOperationCount];
	MString							renderOperationsNames_[kOperationCount];
	bool							renderOperationsEnabled_[kOperationCount];
	int								currentOperation_;

	static C_DX11CurvVP*				instance_;
	
};

//--------------------------------------------------------
//! C_PresentOp
//! 
//
//--------------------------------------------------------
class C_PresentOp : public MHWRender::MPresentTarget{
 public:
	//Creators
	C_PresentOp( const MString &name ): MPresentTarget( name ), pTarget_( nullptr ){};
	virtual ~C_PresentOp(){};

 public:
	//Manipulators
	void setRenderTarget( MHWRender::MRenderTarget *target ){
		pTarget_ = target;
	};
	
	//MPresentTarget Override
	virtual PPRenderTarget targetOverrideList( unsigned int &listSize ) override{
		if( pTarget_ ){
			listSize = 1;
			return &pTarget_;
		}else{
			listSize = 0;
			return nullptr;
		}
	};
	
	
 protected:
	//Members
	MHWRender::MRenderTarget *pTarget_;
};

#endif