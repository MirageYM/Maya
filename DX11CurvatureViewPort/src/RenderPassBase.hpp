/*
  RenderPassBase
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/

#pragma once

#if !defined( RENDERPASSBASE_HPP_INCLUDED__ )
#define RENDERPASSBASE_HPP_INCLUDED__

//C
#include <stdio.h>
#include <stdlib.h>
#include <vector>
#include <memory>
#include <list>
#include <map>
#include <string>
#include <stdexcept>

// Includes for DX
#include <d3d11.h>
#include <d3dx11.h>
#include <d3dcompiler.h>
#include <DirectXMath.h>
using namespace DirectX;

namespace DX11ViewPort{

	//--------------------------------------------------------
	//! C_PassShaders
	//!
	//
	//--------------------------------------------------------
	class C_PassShaders{
	 public:
		using VsInputDescs = std::vector< D3D11_INPUT_ELEMENT_DESC >;
		using GsSoDecarationEntries = std::vector< D3D11_SO_DECLARATION_ENTRY >;
		
	 public:
		//Creators
		inline C_PassShaders():
			pVertexShader_( nullptr ),
			pVertexLayout_( nullptr ),
			pGeometryShader_( nullptr ),
			pDomainShader_( nullptr ),
			pHullShader_( nullptr ),
			pPixelShader_( nullptr )
		{

		};

	 public:
		//Manipulators
		HRESULT compileShaderFromFile(	LPCSTR		szFileName,
										LPCSTR		szEntryPoint,
										LPCSTR		szShaderModel,
										ID3DBlob**	ppBlobOut );

		void initFromFile	(	const std::string&					fileBasePath,
								const std::string&					fileName,
								const std::string&					vsName,
								const std::string&					gsName,
								const std::string&					psName,
								VsInputDescs*						vsLyaout,
								GsSoDecarationEntries*				gsStreamDecs,
								ID3D11Device*						pD3DDevice );

		void release		( void );

		ID3D11VertexShader*				getVertexShader		( void ){ return pVertexShader_; };
		const ID3D11VertexShader*		getVertexShader		( void ) const{ return pVertexShader_; };
		ID3D11GeometryShader*			getGeometryShader	( void ){ return pGeometryShader_; };
		const ID3D11GeometryShader*		getGeometryShader	( void ) const{ return pGeometryShader_; };
		ID3D11PixelShader*				getPixelShader		( void ){ return pPixelShader_; };
		const ID3D11PixelShader*		getPixelShader		( void ) const{ return pPixelShader_; };

		ID3D11InputLayout*				getVertexLayout		( void ){ return pVertexLayout_; };
		const ID3D11InputLayout*		getVertexLayout		( void ) const{ return pVertexLayout_; };

		unsigned int					getVSSlotSize		( void ){ return vsStrides_.size(); };
		unsigned int					getVSStride			( unsigned int slotIndex = 0  ){ return vsStrides_[ slotIndex ]; };
		auto&							getVSStrides		( void ){ return vsStrides_; };
		const auto&						getVSStrides		( void ) const{ return vsStrides_; };
		unsigned int					getGSStride			( void ){ return gsStride_; };
		VsInputDescs&					getVsInputDescs		( void ){ return vsInputDescs_; };
		const VsInputDescs&				getVsInputDescs		( void ) const{ return vsInputDescs_; };
		GsSoDecarationEntries&			getGsSoDecls		( void ){ return gsSoDecls_; };
		const GsSoDecarationEntries&	getGsSoDecls		( void ) const{ return gsSoDecls_; };

	 protected:
		//Members
		ID3D11VertexShader*		pVertexShader_;
		ID3D11InputLayout*		pVertexLayout_;
		
		ID3D11GeometryShader*	pGeometryShader_;
		ID3D11DomainShader*		pDomainShader_;
		ID3D11HullShader*		pHullShader_;
		ID3D11PixelShader*		pPixelShader_;

		VsInputDescs			vsInputDescs_;
		GsSoDecarationEntries	gsSoDecls_;

		std::vector< unsigned int >		vsStrides_;
		unsigned int			gsStride_;
	};

	typedef std::shared_ptr< C_PassShaders >	PassShadersHdl;
	typedef std::shared_ptr< PassShadersHdl >	PassShadersPtrArray;

	//--------------------------------------------------------
	//! C_RenderTargetInstance
	//!
	//
	//--------------------------------------------------------
	class C_RenderTargetInstance{
	 public:
		C_RenderTargetInstance();
		virtual ~C_RenderTargetInstance();

	 public:
		//Manipulators
		virtual void	create		(	ID3D11Device* pD3DDevice );
		virtual void	release		(	void );
		virtual void	clear		(	void );
		virtual void	setSize		(	unsigned int	width,
										unsigned int	height );
		virtual void	resize		(	unsigned int	width,
										unsigned int	height,
										ID3D11Device*	pD3DDevice );
		virtual void	setFormat	(	DXGI_FORMAT		format );

		virtual const D3D11_TEXTURE2D_DESC&				getTexture2dDesc	(	void ) const;
		virtual void									setTexture2dDesc	(	const D3D11_TEXTURE2D_DESC& desc );
		virtual const D3D11_RENDER_TARGET_VIEW_DESC&	getRenderTargetDesc	(	void ) const;
		virtual void									setRenderTargetDesc	(	const D3D11_RENDER_TARGET_VIEW_DESC& desc );
		virtual const ID3D11Texture2D*					getTexture2d		(	void ) const;
		virtual const ID3D11RenderTargetView*			getRenderTarget		(	void ) const;
		virtual ID3D11Texture2D*						getTexture2d		(	void );
		virtual ID3D11RenderTargetView*					getRenderTarget		(	void );
		virtual void									setTexture2d		(	ID3D11Texture2D* p );
		virtual void									setRenderTarget		(	ID3D11RenderTargetView* p );
		virtual const ID3D11ShaderResourceView*			getShaderResource	(	void ) const;
		virtual ID3D11ShaderResourceView*				getShaderResource	(	void );

	 protected:
		//Members
		D3D11_TEXTURE2D_DESC			tex2dDesc_;
		D3D11_RENDER_TARGET_VIEW_DESC	renderTargetDesc_;
		ID3D11Texture2D*				pTex2d_;
		ID3D11RenderTargetView*			pRenderTarget_;
		ID3D11ShaderResourceView*		pShaderResourceView_;
	};

	typedef std::shared_ptr< C_RenderTargetInstance >	RenderTargetHandle;
	typedef std::vector< RenderTargetHandle >			RenderTargetHandleArray;

	//--------------------------------------------------------
	//! C_RenderTargetInstance
	//!
	//
	//--------------------------------------------------------
	class C_RenderTargetInstanceUnmanaged: public C_RenderTargetInstance{
	 public:
		C_RenderTargetInstanceUnmanaged(): C_RenderTargetInstance(){};
		virtual ~C_RenderTargetInstanceUnmanaged(){};

	 public:
		//Manipulators
		virtual void	create		(	ID3D11Device* pD3DDevice ) override {};
		virtual void	release		(	void ) override {};
		virtual void	clear		(	void ) override {};
		virtual void	setSize		(	unsigned int	width,
										unsigned int	height ) override {};
		virtual void	resize		(	unsigned int	width,
										unsigned int	height,
										ID3D11Device*	pD3DDevice ) override {};
		virtual void	setFormat	(	DXGI_FORMAT		format ) override {};

	};

	//--------------------------------------------------------
	//! C_RenderPassBase
	//!
	//
	//--------------------------------------------------------
	class C_RenderPassBase{
	 public:
		//Creators
		virtual ~C_RenderPassBase();
		
	 protected:
		//Creators
		C_RenderPassBase();


	 public:
		//Manipulators
		virtual void	init			(	ID3D11Device* d3dDevice,
											ID3D11DeviceContext* d3dContext );
		virtual void	createBuffers	(	void );
		virtual void	preDraw			(	void );
		virtual void	postDraw		(	void );

		virtual void	setShader		(	void ) = 0;
	
		virtual void	setSize			(	unsigned int width,
											unsigned int height );
		
		virtual PassShadersHdl	getShaderHandle	(	void );
		
		virtual void	setD3D11Device			(	ID3D11Device* p );
		virtual void	setD3D11DeviceContext	(	ID3D11DeviceContext* p );

		virtual RenderTargetHandleArray&	renderTargetHandleArray( void ){ return pRenderTargetInfoArray_; };
		virtual ID3D11DepthStencilView*		depthStencil( void ){ return pDepthStencilView_; };
		virtual void						setDepthStencil( ID3D11DepthStencilView* p ){ pDepthStencilView_ = p; };

		virtual ID3D11Buffer*				getStreamOutBuffer	( void ){ return pStreamOutBuffer_; };
		virtual void						setStreamOutBuffer	( ID3D11Buffer* p ){ pStreamOutBuffer_ = p; };

		virtual void*		getShaderParameterPtr	(	void );
		virtual const void*	getShaderParameterPtr	(	void ) const;
		virtual void		setShaderParameter		(	const void* non );

	 protected:
		//Members
		PassShadersHdl				passShaderHdl_;
		ID3D11Device*				pD3DDevice_;
		ID3D11DeviceContext*		pD3DDeviceContext_;
		unsigned int				width_;
		unsigned int				height_;
		
		RenderTargetHandleArray		pRenderTargetInfoArray_;
		
		ID3D11Texture2D*			pDepthTex2d_;
		D3D11_TEXTURE2D_DESC		depthTex2dDesc_;
		ID3D11DepthStencilView* 	pDepthStencilView_;
		bool						createOwnDepth_;
		
		ID3D11Buffer*				pConstantBuffer_;
		
		ID3D11Buffer*				pVertexBuffer_;
		ID3D11Buffer*				pIndexBuffer_;
		ID3D11Buffer*				pStreamOutBuffer_;
		UINT						streamOutOffset_;

		C_PassShaders::VsInputDescs				inputDesc_;
		C_PassShaders::GsSoDecarationEntries	gsDecl_;
		
	};
}

#endif