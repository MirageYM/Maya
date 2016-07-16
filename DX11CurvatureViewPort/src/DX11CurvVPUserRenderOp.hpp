/*
  DX11CurvVPUserRenderOp
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/

#pragma once

#if !defined( DX11CURVVPUSERRENDEROP_HPP_INCLUDED__ )
#define DX11CURVVPUSERRENDEROP_HPP_INCLUDED__

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

#include "RenderPassBase.hpp"

#if MAYA_VERSION >= 20160
typedef MHWRender::MRenderTarget* const* PPRenderTarget;
#else
typedef MHWRender::MRenderTarget** PPRenderTarget;
#endif

//--------------------------------------------------------
//! C_DX11CurvVPUserRenderOp
//! 
//
//--------------------------------------------------------
class C_DX11CurvVPUserRenderOp: public MHWRender::MUserRenderOperation{
 public:
	struct CommonShaderParameter{
		XMMATRIX	gWorldView;
		XMMATRIX	gProjection;
		XMMATRIX	gWorldViewProjection;
		FLOAT		gViewWidth;
		FLOAT		gViewHeight;
		FLOAT		gValPower;
		FLOAT		gValMult;
		XMMATRIX	gWorld;
		XMVECTORF32	gColMid;
		XMVECTORF32	gColPos;
		XMVECTORF32	gColNeg;
		XMVECTORF32	gGridWidth;
		XMVECTORF32	gGridOffset;
		XMVECTORF32	gGridDist;
		FLOAT		gGridAlpha;
		FLOAT		gCheckerAlpha;
		FLOAT		gCheckerRepeat;
		FLOAT		gAmbient;
		FLOAT		gDepthLimit;
	};

	enum RenderTargets{
		RTPosition,
		RTNormal,
		RTCurvature,
		RTColor,
		RTCount,
		RTEnd
	};
	
 public:
	//Creators
	C_DX11CurvVPUserRenderOp( const MString& name );
	virtual ~C_DX11CurvVPUserRenderOp();

 public:
	//Manipulators
	virtual void								setPanelName			(	const MString& name ){ panelName_ = name; };
	virtual const MString&						panelName				(	void ){ return panelName_; };
	
	virtual void								initRenderTargets		(	void );
	virtual void								updateRenderTargets		(	void );
	virtual void								releaseRenderTargets	(	void );
	virtual MHWRender::MRenderTarget* 			getOutputRenderBuffer	(	void );
	virtual MHWRender::MRenderTarget* 			getOutputDepthBuffer	(	void );

	virtual void								drawSceneObjects		(	const MHWRender::MDrawContext& context,
																			ID3D11Device* pD3DDevice,
																			ID3D11DeviceContext* pD3DDeviceContext,
																			unsigned int width,
																			unsigned int height );
	virtual void								drawObject				(	const MDagPath& path,
																			const MMatrix& view,
																			const MMatrix& projection );
	
	CommonShaderParameter&						commonShaderParameter	(	void ){ return commonShaderParameter_; };
	
	//MUserRenderOperation Override
	virtual PPRenderTarget	targetOverrideList	(	unsigned int &listSize ) override;
	virtual MStatus								execute				(	const MHWRender::MDrawContext& drawContext ) override;
	virtual const MHWRender::MCameraOverride*	cameraOverride		(	void ) override;


 protected:
	//Members
	//DirectX
	bool										isInit_;
	
	ID3D11Device*								pD3DDevice_;
	ID3D11DeviceContext*						pD3DDeviceContext_;
	unsigned int								width_;
	unsigned int								height_;
	float										valPower_;
	float										valHeight_;
	
	MHWRender::MRenderTarget*					outputRenderBuffer_;
	MHWRender::MRenderTargetDescription			outputRenderBufferDesc_;
	MHWRender::MRenderTarget*					outputDepthBuffer_;
	MHWRender::MRenderTarget*					workDepthBuffer_;
	MHWRender::MRenderTargetDescription			outputDepthBufferDesc_;

	DX11ViewPort::RenderTargetHandleArray		renderTargets_;

	//Shaders
	DX11ViewPort::PassShadersHdl				passPre_;
	DX11ViewPort::PassShadersHdl				pass0_;
	DX11ViewPort::PassShadersHdl				pass1_;
	
	//Buffers
	CommonShaderParameter						commonShaderParameter_;
	ID3D11Buffer*								pCommonShaderParameterCB_;	
	float* 										pVtx_;
	float* 										pNml_;
	float* 										pUv_;
	ID3D11Buffer*								pVertexBuffer_;
	ID3D11Buffer*								pVertexNormalBuffer_;
	ID3D11Buffer*								pVertexUvBuffer_;
	unsigned int* 								pIdx_;
	ID3D11Buffer*								pIndexBuffer_;

	UINT										streamOutOffset_;
	ID3D11Buffer*								pStreamOutBuffer_;

	//MayaVP
	MString										panelName_;
	MHWRender::MCameraOverride					cameraOverride_;
	bool										enableAA_;
	

};

#endif