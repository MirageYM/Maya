/*
  RenderPassBase
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/
//C++
#include <assert.h>
#include <memory.h>

#include "RenderPassBase.hpp"

namespace DX11ViewPort{

	size_t BitsPerPixel( DXGI_FORMAT fmt )
	{
		switch( fmt )
		{
		 case DXGI_FORMAT_R32G32B32A32_TYPELESS:
		 case DXGI_FORMAT_R32G32B32A32_FLOAT:
		 case DXGI_FORMAT_R32G32B32A32_UINT:
		 case DXGI_FORMAT_R32G32B32A32_SINT:
			return 128;

		 case DXGI_FORMAT_R32G32B32_TYPELESS:
		 case DXGI_FORMAT_R32G32B32_FLOAT:
		 case DXGI_FORMAT_R32G32B32_UINT:
		 case DXGI_FORMAT_R32G32B32_SINT:
			return 96;

		 case DXGI_FORMAT_R16G16B16A16_TYPELESS:
		 case DXGI_FORMAT_R16G16B16A16_FLOAT:
		 case DXGI_FORMAT_R16G16B16A16_UNORM:
		 case DXGI_FORMAT_R16G16B16A16_UINT:
		 case DXGI_FORMAT_R16G16B16A16_SNORM:
		 case DXGI_FORMAT_R16G16B16A16_SINT:
		 case DXGI_FORMAT_R32G32_TYPELESS:
		 case DXGI_FORMAT_R32G32_FLOAT:
		 case DXGI_FORMAT_R32G32_UINT:
		 case DXGI_FORMAT_R32G32_SINT:
		 case DXGI_FORMAT_R32G8X24_TYPELESS:
		 case DXGI_FORMAT_D32_FLOAT_S8X24_UINT:
		 case DXGI_FORMAT_R32_FLOAT_X8X24_TYPELESS:
		 case DXGI_FORMAT_X32_TYPELESS_G8X24_UINT:
			return 64;

		 case DXGI_FORMAT_R10G10B10A2_TYPELESS:
		 case DXGI_FORMAT_R10G10B10A2_UNORM:
		 case DXGI_FORMAT_R10G10B10A2_UINT:
		 case DXGI_FORMAT_R11G11B10_FLOAT:
		 case DXGI_FORMAT_R8G8B8A8_TYPELESS:
		 case DXGI_FORMAT_R8G8B8A8_UNORM:
		 case DXGI_FORMAT_R8G8B8A8_UNORM_SRGB:
		 case DXGI_FORMAT_R8G8B8A8_UINT:
		 case DXGI_FORMAT_R8G8B8A8_SNORM:
		 case DXGI_FORMAT_R8G8B8A8_SINT:
		 case DXGI_FORMAT_R16G16_TYPELESS:
		 case DXGI_FORMAT_R16G16_FLOAT:
		 case DXGI_FORMAT_R16G16_UNORM:
		 case DXGI_FORMAT_R16G16_UINT:
		 case DXGI_FORMAT_R16G16_SNORM:
		 case DXGI_FORMAT_R16G16_SINT:
		 case DXGI_FORMAT_R32_TYPELESS:
		 case DXGI_FORMAT_D32_FLOAT:
		 case DXGI_FORMAT_R32_FLOAT:
		 case DXGI_FORMAT_R32_UINT:
		 case DXGI_FORMAT_R32_SINT:
		 case DXGI_FORMAT_R24G8_TYPELESS:
		 case DXGI_FORMAT_D24_UNORM_S8_UINT:
		 case DXGI_FORMAT_R24_UNORM_X8_TYPELESS:
		 case DXGI_FORMAT_X24_TYPELESS_G8_UINT:
		 case DXGI_FORMAT_R9G9B9E5_SHAREDEXP:
		 case DXGI_FORMAT_R8G8_B8G8_UNORM:
		 case DXGI_FORMAT_G8R8_G8B8_UNORM:
		 case DXGI_FORMAT_B8G8R8A8_UNORM:
		 case DXGI_FORMAT_B8G8R8X8_UNORM:
		 case DXGI_FORMAT_R10G10B10_XR_BIAS_A2_UNORM:
		 case DXGI_FORMAT_B8G8R8A8_TYPELESS:
		 case DXGI_FORMAT_B8G8R8A8_UNORM_SRGB:
		 case DXGI_FORMAT_B8G8R8X8_TYPELESS:
		 case DXGI_FORMAT_B8G8R8X8_UNORM_SRGB:
			return 32;

		 case DXGI_FORMAT_R8G8_TYPELESS:
		 case DXGI_FORMAT_R8G8_UNORM:
		 case DXGI_FORMAT_R8G8_UINT:
		 case DXGI_FORMAT_R8G8_SNORM:
		 case DXGI_FORMAT_R8G8_SINT:
		 case DXGI_FORMAT_R16_TYPELESS:
		 case DXGI_FORMAT_R16_FLOAT:
		 case DXGI_FORMAT_D16_UNORM:
		 case DXGI_FORMAT_R16_UNORM:
		 case DXGI_FORMAT_R16_UINT:
		 case DXGI_FORMAT_R16_SNORM:
		 case DXGI_FORMAT_R16_SINT:
		 case DXGI_FORMAT_B5G6R5_UNORM:
		 case DXGI_FORMAT_B5G5R5A1_UNORM:
			return 16;

		 case DXGI_FORMAT_R8_TYPELESS:
		 case DXGI_FORMAT_R8_UNORM:
		 case DXGI_FORMAT_R8_UINT:
		 case DXGI_FORMAT_R8_SNORM:
		 case DXGI_FORMAT_R8_SINT:
		 case DXGI_FORMAT_A8_UNORM:
			return 8;

		 case DXGI_FORMAT_R1_UNORM:
			return 1;

		 case DXGI_FORMAT_BC1_TYPELESS:
		 case DXGI_FORMAT_BC1_UNORM:
		 case DXGI_FORMAT_BC1_UNORM_SRGB:
		 case DXGI_FORMAT_BC4_TYPELESS:
		 case DXGI_FORMAT_BC4_UNORM:
		 case DXGI_FORMAT_BC4_SNORM:
			return 4;

		 case DXGI_FORMAT_BC2_TYPELESS:
		 case DXGI_FORMAT_BC2_UNORM:
		 case DXGI_FORMAT_BC2_UNORM_SRGB:
		 case DXGI_FORMAT_BC3_TYPELESS:
		 case DXGI_FORMAT_BC3_UNORM:
		 case DXGI_FORMAT_BC3_UNORM_SRGB:
		 case DXGI_FORMAT_BC5_TYPELESS:
		 case DXGI_FORMAT_BC5_UNORM:
		 case DXGI_FORMAT_BC5_SNORM:
		 case DXGI_FORMAT_BC6H_TYPELESS:
		 case DXGI_FORMAT_BC6H_UF16:
		 case DXGI_FORMAT_BC6H_SF16:
		 case DXGI_FORMAT_BC7_TYPELESS:
		 case DXGI_FORMAT_BC7_UNORM:
		 case DXGI_FORMAT_BC7_UNORM_SRGB:
			return 8;

		/*
		 case DXGI_FORMAT_B4G4R4A4_UNORM:
			return 16;
		*/

		 default:
			return 0;
		}
	}
	
	//--------------------------------------------------------
	//! C_PassShaders
	//--------------------------------------------------------
	//- - - - - - - - - - - - - - - - - -
	//
	HRESULT C_PassShaders::compileShaderFromFile(	LPCSTR		szFileName,
													LPCSTR		szEntryPoint,
													LPCSTR		szShaderModel,
													ID3DBlob**	ppBlobOut )
	{
		HRESULT hr = S_OK;

		DWORD dwShaderFlags = D3DCOMPILE_ENABLE_STRICTNESS;

		ID3DBlob* pErrorBlob = nullptr;
		hr = D3DX11CompileFromFile( szFileName, nullptr, nullptr, szEntryPoint, szShaderModel,
									dwShaderFlags, 0, nullptr, ppBlobOut, &pErrorBlob, nullptr );
		if( FAILED(hr) ){
			if( pErrorBlob ){
				OutputDebugStringA( (char*)pErrorBlob->GetBufferPointer() );
				pErrorBlob->Release();
			}
			return hr;
		}

		if( pErrorBlob ){
			pErrorBlob->Release();
		}

		return S_OK;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_PassShaders::initFromFile(	const std::string&					effectsLocation,
										const std::string&					effectName,
										const std::string&					vsName,
										const std::string&					gsName,
										const std::string&					psName,
										VsInputDescs*						pVsLyaout,
										GsSoDecarationEntries*				pGsStreamDecs,
										ID3D11Device*						pD3DDevice )
	{
		HRESULT hres;
		std::string effectLocation = effectsLocation + "\\" + effectName;

		// Set up vertex shader
		//
		if( vsName.length() > 0 && pVsLyaout && pVsLyaout->size() > 0 ){

			vsInputDescs_ = *pVsLyaout;

			auto maxSlots = 0;
			for( auto itr = vsInputDescs_.begin(); itr != vsInputDescs_.end(); ++itr ){
				if( itr->InputSlot > maxSlots ){
					maxSlots = itr->InputSlot;
				}
			}
			
			vsStrides_.resize( maxSlots + 1 );
			for( auto itr = vsStrides_.begin(); itr != vsStrides_.end(); ++itr ){
				*itr = 0;
			}
			
			for( auto itr = vsInputDescs_.begin(); itr != vsInputDescs_.end(); ++itr ){
				vsStrides_[ itr->InputSlot ] += BitsPerPixel( itr->Format ) / 8;
			}

			ID3DBlob* pVSBlob = nullptr;
			hres = compileShaderFromFile(	effectLocation.c_str(),
											vsName.c_str(),
											"vs_5_0",
											&pVSBlob );
			if( FAILED(hres) ){
				throw std::runtime_error( std::string( "compileShader failed" ) );
			}

			hres = pD3DDevice->CreateVertexShader(	pVSBlob->GetBufferPointer(),
													pVSBlob->GetBufferSize(),
													nullptr,
													&pVertexShader_ );
			if( FAILED(hres) ){
				pVSBlob->Release();
				throw std::runtime_error( std::string( "compileShader failed" ) );
			}

			hres = pD3DDevice->CreateInputLayout(	&( vsInputDescs_[0] ),
													vsInputDescs_.size(),
													pVSBlob->GetBufferPointer(),
													pVSBlob->GetBufferSize(),
													&pVertexLayout_ );
			pVSBlob->Release();
			if( FAILED(hres) ){
				throw std::runtime_error( std::string( "compileShader failed" ) );
			}
		}

		// Set up geometory shader
		//
		if( gsName.length() > 0 ){
			ID3DBlob* pGSBlob = nullptr;

			hres = compileShaderFromFile(	effectLocation.c_str(),
											gsName.c_str(),
											"gs_5_0",
											&pGSBlob );
			if( FAILED(hres) ){
				this->release();
				throw std::runtime_error( std::string( "compileShader failed" ) );
			}

			if( pGsStreamDecs && pGsStreamDecs->size() > 0 ){

				gsSoDecls_ = *pGsStreamDecs;
				gsStride_ = 0;
				unsigned int soStride[] = { 0 };
				for( auto itr = gsSoDecls_.begin(); itr != gsSoDecls_.end(); ++itr ){
					soStride[0] += sizeof( float ) * itr->ComponentCount;
					gsStride_ += sizeof( float ) * itr->ComponentCount;
				}

				OutputDebugStringA( "GS using steam out" );
				UINT	rasterizedStream = 0;
				if( psName.length() < 1 ){
					rasterizedStream = D3D11_SO_NO_RASTERIZED_STREAM;
				}

				hres = pD3DDevice->CreateGeometryShaderWithStreamOutput(	pGSBlob->GetBufferPointer(),
																			pGSBlob->GetBufferSize(),
																			&( gsSoDecls_[0] ),
																			gsSoDecls_.size(),
																			soStride,
																			1,
																			rasterizedStream,
																			nullptr,
																			&pGeometryShader_ );
				if( FAILED(hres) ){
					this->release();
					pGSBlob->Release();
					throw std::runtime_error( std::string( "compileShader failed" ) );
				}
			}else{
				OutputDebugStringA( "GS without steam out" );
				hres = pD3DDevice->CreateGeometryShader(	pGSBlob->GetBufferPointer(),
															pGSBlob->GetBufferSize(),
															nullptr,
															&pGeometryShader_ );
				if( FAILED(hres) ){
					this->release();
					pGSBlob->Release();
					throw std::runtime_error( std::string( "compileShader failed" ) );
				}
			}

		}

		// Set up pixel shader
		//
		if( psName.length() > 0 ){

			ID3DBlob* pPSBlob = nullptr;
			hres = compileShaderFromFile(	effectLocation.c_str(),
											psName.c_str(),
											"ps_5_0",
											&pPSBlob );
			if( FAILED(hres) ){
				this->release();
				throw std::runtime_error( std::string( "compileShader failed" ) );
			}

			hres = pD3DDevice->CreatePixelShader(	pPSBlob->GetBufferPointer(),
													pPSBlob->GetBufferSize(),
													nullptr,
													&pPixelShader_ );
			pPSBlob->Release();
			if( FAILED(hres) ){
				this->release();
				throw std::runtime_error( std::string( "compileShader failed" ) );
			}
		}

		// Create a new effect item
		//
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_PassShaders::release(	void ){

		#define PassShaderReleaseMember( s ) if( s ){ s->Release(); s = nullptr; }

		PassShaderReleaseMember( pVertexShader_ );
		PassShaderReleaseMember( pVertexLayout_ );
		PassShaderReleaseMember( pGeometryShader_ );
		PassShaderReleaseMember( pDomainShader_ );
		PassShaderReleaseMember( pHullShader_ );
		PassShaderReleaseMember( pPixelShader_ );

		#undef PassShaderReleaseMember
	}

	//--------------------------------------------------------
	//! C_RenderTargetInstance
	//--------------------------------------------------------
	//- - - - - - - - - - - - - - - - - -
	//
	C_RenderTargetInstance::C_RenderTargetInstance():
	pTex2d_( nullptr ),
	pRenderTarget_( nullptr ),
	pShaderResourceView_( nullptr )
	{
		memset( &tex2dDesc_, 0, sizeof( D3D11_TEXTURE2D_DESC ) );
		tex2dDesc_.ArraySize = 1;
		tex2dDesc_.BindFlags = D3D11_BIND_RENDER_TARGET | D3D11_BIND_SHADER_RESOURCE;
		tex2dDesc_.Usage = D3D11_USAGE_DEFAULT;
		tex2dDesc_.Format = DXGI_FORMAT_R32G32B32A32_FLOAT;
		tex2dDesc_.Width = 256;
		tex2dDesc_.Height = 256;
		tex2dDesc_.MipLevels = 1;
		tex2dDesc_.SampleDesc.Count = 1;

		memset( &renderTargetDesc_, 0, sizeof( D3D11_RENDER_TARGET_VIEW_DESC ) );
		renderTargetDesc_.Format = tex2dDesc_.Format;
		renderTargetDesc_.ViewDimension = D3D11_RTV_DIMENSION_TEXTURE2D;
		renderTargetDesc_.Texture2D.MipSlice = 0;

	}

	//- - - - - - - - - - - - - - - - - -
	//
	C_RenderTargetInstance::~C_RenderTargetInstance(){
		release();
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderTargetInstance::create( ID3D11Device* pD3DDevice ){
		if( pD3DDevice->CreateTexture2D( &tex2dDesc_, nullptr, &pTex2d_ ) != S_OK ){
			throw std::runtime_error( std::string( "CreateTexture2D failed" ) );
		}

		if( pD3DDevice->CreateRenderTargetView( pTex2d_, &renderTargetDesc_, &pRenderTarget_ ) != S_OK ){
			throw std::runtime_error( std::string( "CreateRenderTargetView failed" ) );
		}

		D3D11_SHADER_RESOURCE_VIEW_DESC desc;
		desc.Format = tex2dDesc_.Format;
		desc.ViewDimension = D3D11_SRV_DIMENSION_TEXTURE2D;
		desc.Texture2D.MostDetailedMip = 0;
		desc.Texture2D.MipLevels = tex2dDesc_.MipLevels;
		pD3DDevice->CreateShaderResourceView( pTex2d_, &desc, &pShaderResourceView_ );

	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderTargetInstance::release( void ){
		if( pRenderTarget_ ){
			pRenderTarget_->Release();
			pRenderTarget_ = nullptr;
		}

		if( pTex2d_ ){
			pTex2d_->Release();
			pTex2d_ = nullptr;
		}

		if( pShaderResourceView_ ){
			pShaderResourceView_->Release();
			pShaderResourceView_ = nullptr;
		}
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderTargetInstance::clear( void ){

	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderTargetInstance::setSize(	unsigned int	width,	unsigned int	height ){

		tex2dDesc_.Width = width;
		tex2dDesc_.Height = height;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderTargetInstance::resize(	unsigned int	width,	unsigned int	height, ID3D11Device* pD3DDevice ){

		if( tex2dDesc_.Width != width || tex2dDesc_.Height != height ){
			tex2dDesc_.Width = width;
			tex2dDesc_.Height = height;

			if( pRenderTarget_ || pTex2d_ ){
				release();
				create( pD3DDevice );
			}
		}
	}



	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderTargetInstance::setFormat(	DXGI_FORMAT		format ){
		tex2dDesc_.Format = format;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	const D3D11_TEXTURE2D_DESC&	C_RenderTargetInstance::getTexture2dDesc(	void ) const{
		return tex2dDesc_;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderTargetInstance::setTexture2dDesc(	const D3D11_TEXTURE2D_DESC& desc ){
		tex2dDesc_ = desc;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	const D3D11_RENDER_TARGET_VIEW_DESC& C_RenderTargetInstance::getRenderTargetDesc(	void ) const{
		return renderTargetDesc_;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderTargetInstance::setRenderTargetDesc(	const D3D11_RENDER_TARGET_VIEW_DESC& desc ){
		renderTargetDesc_ = desc;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	const ID3D11Texture2D* C_RenderTargetInstance::getTexture2d(	void ) const{
		return pTex2d_;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	const ID3D11RenderTargetView*	C_RenderTargetInstance::getRenderTarget(	void ) const{
		return pRenderTarget_;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	ID3D11Texture2D* C_RenderTargetInstance::getTexture2d(	void ){
		return pTex2d_;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	ID3D11RenderTargetView*	C_RenderTargetInstance::getRenderTarget(	void ){
		return pRenderTarget_;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderTargetInstance::setTexture2d(	ID3D11Texture2D* p ){
		pTex2d_ = p;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderTargetInstance::setRenderTarget(	ID3D11RenderTargetView* p ){
		pRenderTarget_ = p;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	const ID3D11ShaderResourceView*	C_RenderTargetInstance::getShaderResource(	void ) const {
		return pShaderResourceView_;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	ID3D11ShaderResourceView*	C_RenderTargetInstance::getShaderResource(	void ){
		return pShaderResourceView_;
	}

	//--------------------------------------------------------
	//! C_RenderPassBase
	//--------------------------------------------------------
	//- - - - - - - - - - - - - - - - - -
	//
	C_RenderPassBase::C_RenderPassBase():
	pD3DDevice_( nullptr ),
	pD3DDeviceContext_( nullptr ),
	width_( 256 ),
	height_( 256 ),
	pDepthStencilView_( nullptr ),
	createOwnDepth_( false ),
	pDepthTex2d_( nullptr ),
	pConstantBuffer_( nullptr ),
	pVertexBuffer_( nullptr ),
	pIndexBuffer_( nullptr ),
	pStreamOutBuffer_( nullptr ),
	streamOutOffset_( 0 )
	{

	}

	//- - - - - - - - - - - - - - - - - -
	//
	C_RenderPassBase::~C_RenderPassBase(){
		pRenderTargetInfoArray_.clear();
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderPassBase::init(	ID3D11Device* d3dDevice, ID3D11DeviceContext* d3dContext ){

		pD3DDevice_ = d3dDevice;
		pD3DDeviceContext_ = d3dContext;

	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderPassBase::createBuffers(	void ){
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderPassBase::preDraw(	void ){

	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderPassBase::postDraw(	void ){

	}

	//- - - - - - - - - - - - - - - - - -
	//
	PassShadersHdl	C_RenderPassBase::getShaderHandle	(	void ){
		return passShaderHdl_;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderPassBase::setD3D11Device(	ID3D11Device* p ){
		pD3DDevice_ = p;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderPassBase::setD3D11DeviceContext	(	ID3D11DeviceContext* p ){
		pD3DDeviceContext_ = p;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderPassBase::setSize(	unsigned int width,
									unsigned int height )
	{
		width_ = width;
		height_ = height;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void* C_RenderPassBase::getShaderParameterPtr( void ){
		return nullptr;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	const void* C_RenderPassBase::getShaderParameterPtr( void ) const{
		return nullptr;
	}

	//- - - - - - - - - - - - - - - - - -
	//
	void C_RenderPassBase::setShaderParameter( const void* non ){

	}
}