/*
  DX11CurvVPUserRenderOp
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
#include <maya/MFnMesh.h>


#include "DX11CurvVPUserRenderOp.hpp"
#include "DebugPrintf.hpp"

using namespace DirectX;

//--------------------------------------------------------
//! C_DX11CurvVPUserRenderOp
//--------------------------------------------------------
//- - - - - - - - - - - - - - - - - -
//
C_DX11CurvVPUserRenderOp::C_DX11CurvVPUserRenderOp( const MString& name ):
	MUserRenderOperation( name ),
	outputRenderBuffer_( nullptr ),
	outputDepthBuffer_( nullptr ),
	workDepthBuffer_( nullptr ),
	pCommonShaderParameterCB_( nullptr ),
	pVtx_( nullptr ),
	pNml_( nullptr ),
	pUv_( nullptr ),
	pVertexBuffer_( nullptr ),
	pVertexNormalBuffer_( nullptr ),
	pVertexUvBuffer_( nullptr ),
	pIdx_( nullptr ),
	pIndexBuffer_( nullptr ),
	pStreamOutBuffer_( nullptr ),
	isInit_( false )

{

	commonShaderParameter_.gValPower = 1.0f;
	commonShaderParameter_.gValMult = 1.0f;
	commonShaderParameter_.gColMid = { 1.0f, 1.0f, 1.0f, 1.0f };
	commonShaderParameter_.gColPos = { 1.0f, 0.0f, 0.0f, 1.0f };
	commonShaderParameter_.gColNeg = { 0.0f, 0.0f, 1.0f, 1.0f };
	commonShaderParameter_.gGridWidth = { 0.002f, 0.002f, 0.002f, 0.0f };
	commonShaderParameter_.gGridOffset = { 0.0f, 0.0f, 0.0f, 0.0f };
	commonShaderParameter_.gGridDist = { 0.1f, 0.1f, 0.1f, 0.0f };
	commonShaderParameter_.gGridAlpha = 0.1f;
	commonShaderParameter_.gCheckerAlpha = 0.9f;
	commonShaderParameter_.gCheckerRepeat = 10.0f;
	commonShaderParameter_.gAmbient = 0.5f;
	commonShaderParameter_.gDepthLimit = 0.001f;
	
	try{
		MHWRender::MRenderer *theRenderer = MHWRender::MRenderer::theRenderer();
		theRenderer->outputTargetSize( width_, height_ );
		
		pD3DDevice_ = (ID3D11Device *)theRenderer->GPUDeviceHandle();
		pD3DDevice_->GetImmediateContext( &pD3DDeviceContext_ );
		
	}catch(...){
		std::cout << "Error" << std::endl;
		return;
	}

	std::string shaderBasePath;
	{
		MString path;
		MGlobal::executeCommand( MString( "pluginInfo -q -p \"DX11CurvatureViewPort\";" ), path );

		if( path.length() <= 0 ){
			std::cout << "plugInfo Error" << std::endl;
			return;
		}

		MStringArray splitPath;
		path.split( '/', splitPath );

		path = "";

		for( unsigned int i = 0; i < splitPath.length() - 1; ++i ){
			path += splitPath[i] + "\\";
		}

		shaderBasePath = path.asChar();
	}
	
	//passPre
	try{
		passPre_ = DX11ViewPort::PassShadersHdl( new DX11ViewPort::C_PassShaders() );
		
		DX11ViewPort::C_PassShaders::VsInputDescs inputDesc;
		DX11ViewPort::C_PassShaders::GsSoDecarationEntries gsDecl;
		
		inputDesc.push_back( D3D11_INPUT_ELEMENT_DESC( { "POSITION", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 0, D3D11_INPUT_PER_VERTEX_DATA, 0 } ) );
		inputDesc.push_back( D3D11_INPUT_ELEMENT_DESC( { "TEXCOORD", 0, DXGI_FORMAT_R32G32B32_FLOAT, 1, 0, D3D11_INPUT_PER_VERTEX_DATA, 0 } ) );
		inputDesc.push_back( D3D11_INPUT_ELEMENT_DESC( { "TEXCOORD", 1, DXGI_FORMAT_R32G32_FLOAT, 2, 0, D3D11_INPUT_PER_VERTEX_DATA, 0 } ) );

		passPre_->initFromFile(	shaderBasePath,
								"EdgeCurv.hlsl",
								"vsPre",
								"",
								"psPre",
								&inputDesc,
								nullptr,
								pD3DDevice_ );

	}catch(...){
		std::cout << "Error" << std::endl;
		return;
	}
	
	//pass0
	try{
		pass0_ = DX11ViewPort::PassShadersHdl( new DX11ViewPort::C_PassShaders() );
		
		DX11ViewPort::C_PassShaders::VsInputDescs inputDesc;
		DX11ViewPort::C_PassShaders::GsSoDecarationEntries gsDecl;
		
		inputDesc.push_back( D3D11_INPUT_ELEMENT_DESC( { "POSITION", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 0, D3D11_INPUT_PER_VERTEX_DATA, 0 } ) );
		inputDesc.push_back( D3D11_INPUT_ELEMENT_DESC( { "TEXCOORD", 0, DXGI_FORMAT_R32G32B32_FLOAT, 1, 0, D3D11_INPUT_PER_VERTEX_DATA, 0 } ) );
		inputDesc.push_back( D3D11_INPUT_ELEMENT_DESC( { "TEXCOORD", 1, DXGI_FORMAT_R32G32_FLOAT, 2, 0, D3D11_INPUT_PER_VERTEX_DATA, 0 } ) );
		
		pass0_->initFromFile(	shaderBasePath,
								"EdgeCurv.hlsl",
								"vs0",
								"gs0tri",
								"ps0",
								&inputDesc,
								nullptr,
								pD3DDevice_ );

	}catch(...){
		std::cout << "Error" << std::endl;
		return;
	}
	
	//pass1
	try{
		pass1_ = DX11ViewPort::PassShadersHdl( new DX11ViewPort::C_PassShaders() );
		
		DX11ViewPort::C_PassShaders::VsInputDescs inputDesc;
		DX11ViewPort::C_PassShaders::GsSoDecarationEntries gsDecl;
		
		inputDesc.push_back( D3D11_INPUT_ELEMENT_DESC( { "POSITION", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 0, D3D11_INPUT_PER_VERTEX_DATA, 0 } ) );
		inputDesc.push_back( D3D11_INPUT_ELEMENT_DESC( { "TEXCOORD", 0, DXGI_FORMAT_R32G32B32_FLOAT, 1, 0, D3D11_INPUT_PER_VERTEX_DATA, 0 } ) );
		inputDesc.push_back( D3D11_INPUT_ELEMENT_DESC( { "TEXCOORD", 1, DXGI_FORMAT_R32G32_FLOAT, 2, 0, D3D11_INPUT_PER_VERTEX_DATA, 0 } ) );

		pass1_->initFromFile(	shaderBasePath,
								"EdgeCurv.hlsl",
								"vs1",
								"",
								"ps1",
								&inputDesc,
								nullptr,
								pD3DDevice_ );

	}catch(...){
		std::cout << "Error" << std::endl;
		return;
	}
	

	isInit_ = true;
}

//- - - - - - - - - - - - - - - - - -
//
C_DX11CurvVPUserRenderOp::~C_DX11CurvVPUserRenderOp(){
	
	MHWRender::MRenderer *theRenderer = MHWRender::MRenderer::theRenderer();
	const MHWRender::MRenderTargetManager* targetManager = theRenderer->getRenderTargetManager();
	
	if( outputRenderBuffer_ ){
		targetManager->releaseRenderTarget( outputRenderBuffer_ );
		outputRenderBuffer_ = nullptr;
	}

	if( outputDepthBuffer_ ){
		targetManager->releaseRenderTarget( outputDepthBuffer_ );
		outputDepthBuffer_ = nullptr;
	}
	if( workDepthBuffer_ ){
		targetManager->releaseRenderTarget( workDepthBuffer_ );
		workDepthBuffer_ = nullptr;
	}

	if( pCommonShaderParameterCB_ ){
		pCommonShaderParameterCB_->Release();
	}
	
	if( pVtx_ ){
		delete[] pVtx_;
	}
	if( pNml_ ){
		delete[] pNml_;
	}
	if( pUv_ ){
		delete[] pUv_;
	}

	if( pVertexBuffer_ ){
		pVertexBuffer_->Release();
	}
	
	if( pVertexNormalBuffer_ ){
		pVertexNormalBuffer_->Release();
	}

	if( pVertexUvBuffer_ ){
		pVertexUvBuffer_->Release();
	}
	
	if( pIdx_ ){
		delete[] pIdx_;
	}

	if( pIndexBuffer_ ){
		pIndexBuffer_->Release();
	}

	if( pStreamOutBuffer_ ){
		pStreamOutBuffer_->Release();
	}

}

//- - - - - - - - - - - - - - - - - -
//
void C_DX11CurvVPUserRenderOp::initRenderTargets(	void ){

	if( !isInit_ ){
		return;
	}
	
	MHWRender::MRenderer *theRenderer = MHWRender::MRenderer::theRenderer();
	theRenderer->outputTargetSize( width_, height_ );
	pD3DDevice_ = (ID3D11Device *)theRenderer->GPUDeviceHandle();
	
	if( !outputRenderBuffer_ ){
		const MHWRender::MRenderTargetManager* targetManager = theRenderer->getRenderTargetManager();
		outputRenderBufferDesc_.setWidth( width_ );
		outputRenderBufferDesc_.setHeight( height_ );
		outputRenderBufferDesc_.setName( MString( "useroutput" ) );
		outputRenderBufferDesc_.setRasterFormat( MHWRender::kR32G32B32A32_FLOAT );
		outputRenderBuffer_ = targetManager->acquireRenderTarget( outputRenderBufferDesc_ );
	}

	if( !outputRenderBuffer_ ){
		throw std::runtime_error( "outputBuffer acquire failure" );
	}
	
	if( !outputDepthBuffer_ ){
		const MHWRender::MRenderTargetManager* targetManager = theRenderer->getRenderTargetManager();
		outputDepthBufferDesc_.setWidth( width_ );
		outputDepthBufferDesc_.setHeight( height_ );
		outputDepthBufferDesc_.setName( MString( "userdepth" ) );
		outputDepthBufferDesc_.setRasterFormat( MHWRender::kD24S8 );
		outputDepthBuffer_ = targetManager->acquireRenderTarget( outputDepthBufferDesc_ );
	}

	if( !outputDepthBuffer_ ){
		throw std::runtime_error( "outputBuffer acquire failure" );
	}

	if( !workDepthBuffer_ ){
		const MHWRender::MRenderTargetManager* targetManager = theRenderer->getRenderTargetManager();
		outputDepthBufferDesc_.setWidth( width_ );
		outputDepthBufferDesc_.setHeight( height_ );
		outputDepthBufferDesc_.setName( MString( "workdepth" ) );
		outputDepthBufferDesc_.setRasterFormat( MHWRender::kD24S8 );
		workDepthBuffer_ = targetManager->acquireRenderTarget( outputDepthBufferDesc_ );
	}

	if( !workDepthBuffer_ ){
		throw std::runtime_error( "outputBuffer acquire failure" );
	}
	
	for( int i = 0; i < static_cast<int>( RTEnd ); ++i ){
		if( renderTargets_.size()  <= i ){
			renderTargets_.push_back( DX11ViewPort::RenderTargetHandle( new DX11ViewPort::C_RenderTargetInstance() ) );
			renderTargets_[i]->create( pD3DDevice_ );
		}
		renderTargets_[i]->resize( width_, height_, pD3DDevice_ );
	}

}

	
//- - - - - - - - - - - - - - - - - -
//
void C_DX11CurvVPUserRenderOp::updateRenderTargets( void ){
	MHWRender::MRenderer *theRenderer = MHWRender::MRenderer::theRenderer();
	if( !theRenderer ){
		return;
	}
	pD3DDevice_ = (ID3D11Device *)theRenderer->GPUDeviceHandle();

	if( !outputRenderBuffer_ ){
		return;
	}

	theRenderer->outputTargetSize( width_, height_ );
	
	outputRenderBuffer_->targetDescription( outputRenderBufferDesc_ );
	if( outputRenderBufferDesc_.width() != width_ || outputRenderBufferDesc_.height() != height_ ){
		outputRenderBufferDesc_.setWidth( width_ );
		outputRenderBufferDesc_.setHeight( height_ );
		outputRenderBuffer_->updateDescription( outputRenderBufferDesc_ );

	}
	outputDepthBuffer_->targetDescription( outputDepthBufferDesc_ );
	if( outputDepthBufferDesc_.width() != width_ || outputDepthBufferDesc_.height() != height_ ){
		outputDepthBufferDesc_.setWidth( width_ );
		outputDepthBufferDesc_.setHeight( height_ );
		outputDepthBuffer_->updateDescription( outputDepthBufferDesc_ );
		workDepthBuffer_->updateDescription( outputDepthBufferDesc_ );
	}

	for( auto itr = renderTargets_.begin(); itr != renderTargets_.end(); ++itr ){
		(*itr)->resize( width_, height_, pD3DDevice_ );
	}

}

//- - - - - - - - - - - - - - - - - -
//
MHWRender::MRenderTarget* C_DX11CurvVPUserRenderOp::getOutputRenderBuffer(	void ){
	
	return outputRenderBuffer_;
}

//- - - - - - - - - - - - - - - - - -
//
MHWRender::MRenderTarget* C_DX11CurvVPUserRenderOp::getOutputDepthBuffer(	void ){
	
	return outputDepthBuffer_;
}

//- - - - - - - - - - - - - - - - - -
//
void C_DX11CurvVPUserRenderOp::releaseRenderTargets( void ){
	MHWRender::MRenderer *theRenderer = MHWRender::MRenderer::theRenderer();
	const MHWRender::MRenderTargetManager* targetManager = theRenderer->getRenderTargetManager();
	
	if( outputRenderBuffer_ ){
		targetManager->releaseRenderTarget( outputRenderBuffer_ );
		outputRenderBuffer_ = nullptr;
	}

	if( outputDepthBuffer_ ){
		targetManager->releaseRenderTarget( outputDepthBuffer_ );
		outputDepthBuffer_ = nullptr;
	}

	if( workDepthBuffer_ ){
		targetManager->releaseRenderTarget( workDepthBuffer_ );
		workDepthBuffer_ = nullptr;
	}
	
	renderTargets_.clear();
}

//- - - - - - - - - - - - - - - - - -
//
void C_DX11CurvVPUserRenderOp::drawSceneObjects( const MHWRender::MDrawContext& context,
											ID3D11Device* pD3DDevice,
											ID3D11DeviceContext* pD3DDeviceContext,
											unsigned int width,
											unsigned int height )
{
	
	if( !isInit_ ){
		return;
	}
	
	MStatus status;
	
	//matrix
	MMatrix view = context.getMatrix(MHWRender::MFrameContext::kWorldViewMtx );
	MMatrix projection = context.getMatrix(MHWRender::MFrameContext::kProjectionMtx );
	D3D11_VIEWPORT vp;
	vp.Width = (float)( width );
	vp.Height = (float)( height );
	vp.MinDepth = 0.0f;
	vp.MaxDepth = 1.0f;
	vp.TopLeftX = 0;
	vp.TopLeftY = 0;
	pD3DDeviceContext->RSSetViewports( 1, &vp );

	//traverse scene
	MDrawTraversal *trav = new MDrawTraversal;
	trav->enableFiltering( true );
	MDagPath cameraPath;
	M3dView m3dView;
	M3dView::getM3dViewFromModelPanel( panelName_, m3dView );
	m3dView.getCamera( cameraPath );
	trav->setFrustum( cameraPath, width, height );	//need for scene culling

	trav->traverse();
	
	//clear target

	static const float clearColor[4] = { 0.0f, 0.0f, 0.0f, 1.0f };
	ID3D11RenderTargetView* pv = reinterpret_cast< ID3D11RenderTargetView* >( outputRenderBuffer_->resourceHandle() );
	//pD3DDeviceContext_->ClearRenderTargetView( pv, clearColor );
	for( int i = 0; i < static_cast<int>( RTEnd ); ++i ){
		pD3DDeviceContext_->ClearRenderTargetView( renderTargets_[ i ]->getRenderTarget(), clearColor );
	}
	
	ID3D11DepthStencilView* pd = reinterpret_cast< ID3D11DepthStencilView* >( outputDepthBuffer_->resourceHandle() );
	pD3DDeviceContext_->ClearDepthStencilView( pd, D3D11_CLEAR_DEPTH, 1.0f, 0.0f );
	pd = reinterpret_cast< ID3D11DepthStencilView* >( workDepthBuffer_->resourceHandle() );
	pD3DDeviceContext_->ClearDepthStencilView( pd, D3D11_CLEAR_DEPTH, 1.0f, 0.0f );
	
	pD3DDeviceContext_->OMSetRenderTargets( 1, &pv, pd );
	
	for( unsigned int i = 0; i < trav->numberOfItems(); ++i ){
		MDagPath path;
		trav->itemPath( i, path );
		if( !path.isValid() ){
			continue;
		}

		if( !path.hasFn( MFn::kMesh ) ){
			continue;
		}

		drawObject(  path, view, projection );

	}
}

//- - - - - - - - - - - - - - - - - -
//
void C_DX11CurvVPUserRenderOp::drawObject(	const MDagPath& path,
						const MMatrix& view,
						const MMatrix& projection )
{
	
	if( !isInit_ ){
		return;
	}
	
	MStatus status;
	
	MMatrix  matrix = path.inclusiveMatrix();

	MMatrix wv = matrix * view;

	MMatrix matWVP = matrix * view * projection;

	commonShaderParameter_.gWorld = XMMatrixSet(
		matrix[0][0],matrix[1][0],matrix[2][0],matrix[3][0],
		matrix[0][1],matrix[1][1],matrix[2][1],matrix[3][1],
		matrix[0][2],matrix[1][2],matrix[2][2],matrix[3][2],
		matrix[0][3],matrix[1][3],matrix[2][3],matrix[3][3] );
	
	commonShaderParameter_.gWorldView = XMMatrixSet(
		wv[0][0],wv[1][0],wv[2][0],wv[3][0],
		wv[0][1],wv[1][1],wv[2][1],wv[3][1],
		wv[0][2],wv[1][2],wv[2][2],wv[3][2],
		wv[0][3],wv[1][3],wv[2][3],wv[3][3] );
	
	commonShaderParameter_.gProjection = XMMatrixSet(
		projection[0][0],projection[1][0],projection[2][0],projection[3][0],
		projection[0][1],projection[1][1],projection[2][1],projection[3][1],
		projection[0][2],projection[1][2],projection[2][2],projection[3][2],
		projection[0][3],projection[1][3],projection[2][3],projection[3][3] );
	
	commonShaderParameter_.gWorldViewProjection = XMMatrixSet(
		matWVP[0][0],matWVP[1][0],matWVP[2][0],matWVP[3][0],
		matWVP[0][1],matWVP[1][1],matWVP[2][1],matWVP[3][1],
		matWVP[0][2],matWVP[1][2],matWVP[2][2],matWVP[3][2],
		matWVP[0][3],matWVP[1][3],matWVP[2][3],matWVP[3][3] );

	commonShaderParameter_.gViewWidth = width_;
	commonShaderParameter_.gViewHeight = height_;

	//get Vertex and Index buffer
	MHWRender::MGeometryRequirements geomRequirements;

	MFnMesh fnMesh( path );

	MHWRender::MVertexBufferDescriptor posDesc("", MHWRender::MGeometry::kPosition, MHWRender::MGeometry::kFloat, 3);
	geomRequirements.addVertexRequirement(posDesc);
	MHWRender::MVertexBufferDescriptor nmlDesc("", MHWRender::MGeometry::kNormal, MHWRender::MGeometry::kFloat, 3);
	geomRequirements.addVertexRequirement(nmlDesc);
	MHWRender::MVertexBufferDescriptor uvDesc( fnMesh.currentUVSetName().asChar(), MHWRender::MGeometry::kTexture, MHWRender::MGeometry::kFloat, 2);
	geomRequirements.addVertexRequirement(uvDesc);

	size_t srcVertexElementWidth = 8;

	MHWRender::MIndexBufferDescriptor triDesc( MHWRender::MIndexBufferDescriptor::kTriangle, MString(),	MHWRender::MGeometry::kTriangles, 3 );
	geomRequirements.addIndexingRequirement( triDesc );
	
	MHWRender::MGeometryExtractor extractor( geomRequirements, path, MHWRender::kPolyGeom_Normal, &status );

	int triCnt =  extractor.primitiveCount( triDesc );
	int vtxCnt = extractor.vertexCount();
	if( triCnt <= 0 || vtxCnt <= 0 ){
		return;
	}

	if( pVtx_ ){
		delete[] pVtx_;
	}
	pVtx_ = new float[ vtxCnt * 3 ];
	extractor.populateVertexBuffer( pVtx_, vtxCnt, posDesc );

	if( pNml_ ){
		delete[] pNml_;
	}
	pNml_ = new float[ vtxCnt * 3 ];
	extractor.populateVertexBuffer( pNml_, vtxCnt, nmlDesc );
	
	if( pUv_ ){
		delete[] pUv_;
	}
	pUv_ = new float[ vtxCnt * 2 ];
	extractor.populateVertexBuffer( pUv_, vtxCnt, uvDesc );
	
	if( pIdx_ ){
		delete[] pIdx_;
	}
	pIdx_ = new unsigned int[ triCnt * 3 ];
	status = extractor.populateIndexBuffer( pIdx_, triCnt, triDesc );

	//render state
	ID3D11RasterizerState* pPrevRSState;
	pD3DDeviceContext_->RSGetState( &pPrevRSState );
	D3D11_RASTERIZER_DESC rsDesc;
	pPrevRSState->GetDesc( &rsDesc );
	ID3D11RasterizerState* pNewRSState;
	

	//depth state
	ID3D11DepthStencilState* pPrevDSState;
	UINT prevStencilRef;
	pD3DDeviceContext_->OMGetDepthStencilState( &pPrevDSState, &prevStencilRef );
	D3D11_DEPTH_STENCIL_DESC dsDesc;
	pPrevDSState->GetDesc( &dsDesc );
	ID3D11DepthStencilState* pNewDepthState;

	//Blend state
	ID3D11BlendState* pPrevBlendState;
	float prevBlendFactor[4];
	UINT prevSampleMask;
	pD3DDeviceContext_->OMGetBlendState( &pPrevBlendState, prevBlendFactor, &prevSampleMask );
	D3D11_BLEND_DESC blDesc;
	pPrevBlendState->GetDesc( &blDesc );
	ID3D11BlendState* pNewBlendState;
	
	
	auto BlendEnable = [&](){
		for( unsigned int i = 0; i < 8; ++i ){
			blDesc.RenderTarget[i].BlendEnable = true;
			blDesc.RenderTarget[i].SrcBlend = D3D11_BLEND_ONE;
			blDesc.RenderTarget[i].DestBlend = D3D11_BLEND_ONE;
			blDesc.RenderTarget[i].SrcBlendAlpha = D3D11_BLEND_ONE;
			blDesc.RenderTarget[i].DestBlendAlpha = D3D11_BLEND_ONE;
			blDesc.RenderTarget[i].BlendOp = D3D11_BLEND_OP_ADD;
			blDesc.RenderTarget[i].BlendOpAlpha = D3D11_BLEND_OP_ADD;
		}
	};

	auto BlendDisable = [&](){
		for( unsigned int i = 0; i < 8; ++i ){
			blDesc.RenderTarget[i].BlendEnable = false;
			blDesc.RenderTarget[i].SrcBlend = D3D11_BLEND_ONE;
			blDesc.RenderTarget[i].DestBlend = D3D11_BLEND_ZERO;
			blDesc.RenderTarget[i].SrcBlendAlpha = D3D11_BLEND_ONE;
			blDesc.RenderTarget[i].DestBlendAlpha = D3D11_BLEND_ZERO;
			blDesc.RenderTarget[i].BlendOp = D3D11_BLEND_OP_ADD;
			blDesc.RenderTarget[i].BlendOpAlpha = D3D11_BLEND_OP_ADD;
		}
	};
	
	//Vertex Buffer
	HRESULT hr;
	if( pVertexBuffer_ ){
		pVertexBuffer_->Release();
	}
	{
		D3D11_BUFFER_DESC bd;
		ZeroMemory( &bd, sizeof(bd) );
		bd.Usage = D3D11_USAGE_DEFAULT;
		bd.ByteWidth = sizeof( float ) * 3 * vtxCnt;
		bd.BindFlags = D3D11_BIND_VERTEX_BUFFER;
		bd.CPUAccessFlags = 0;
		D3D11_SUBRESOURCE_DATA initData;
		ZeroMemory( &initData, sizeof(initData) );
		initData.pSysMem = pVtx_;
		if( pD3DDevice_->CreateBuffer( &bd, &initData, &pVertexBuffer_ ) != S_OK ){
			throw std::runtime_error( std::string( "VertexBuffer create failed" ) );
		}
	}

	if( pVertexNormalBuffer_ ){
		pVertexNormalBuffer_->Release();
	}
	{
		D3D11_BUFFER_DESC bd;
		ZeroMemory( &bd, sizeof(bd) );
		bd.Usage = D3D11_USAGE_DEFAULT;
		bd.ByteWidth = sizeof( float ) * 3 * vtxCnt;
		bd.BindFlags = D3D11_BIND_VERTEX_BUFFER;
		bd.CPUAccessFlags = 0;
		D3D11_SUBRESOURCE_DATA initData;
		ZeroMemory( &initData, sizeof(initData) );
		initData.pSysMem = pNml_;
		if( pD3DDevice_->CreateBuffer( &bd, &initData, &pVertexNormalBuffer_ ) != S_OK ){
			throw std::runtime_error( std::string( "VertexBuffer create failed" ) );
		}
	}
	if( pVertexUvBuffer_ ){
		pVertexUvBuffer_->Release();
	}
	{
		D3D11_BUFFER_DESC bd;
		ZeroMemory( &bd, sizeof(bd) );
		bd.Usage = D3D11_USAGE_DEFAULT;
		bd.ByteWidth = sizeof( float ) * 2 * vtxCnt;
		bd.BindFlags = D3D11_BIND_VERTEX_BUFFER;
		bd.CPUAccessFlags = 0;
		D3D11_SUBRESOURCE_DATA initData;
		ZeroMemory( &initData, sizeof(initData) );
		initData.pSysMem = pUv_;
		if( pD3DDevice_->CreateBuffer( &bd, &initData, &pVertexUvBuffer_ ) != S_OK ){
			throw std::runtime_error( std::string( "VertexBuffer create failed" ) );
		}
	}
	//Index Buffer
	if( pIndexBuffer_ ){
		pIndexBuffer_->Release();
	}
	{
		D3D11_BUFFER_DESC bd;
		ZeroMemory( &bd, sizeof(bd) );
		bd.Usage = D3D11_USAGE_DEFAULT;
		bd.ByteWidth = sizeof( unsigned int ) * 3 * triCnt;
		bd.BindFlags = D3D11_BIND_INDEX_BUFFER;
		bd.CPUAccessFlags = 0;
		D3D11_SUBRESOURCE_DATA initData;
		initData.pSysMem = pIdx_;
		if( pD3DDevice_->CreateBuffer( &bd, &initData, &pIndexBuffer_ ) != S_OK ){
			throw std::runtime_error( std::string( "VertexBuffer create failed" ) );
		}
	}
	
	//SO Buffer
	#if 0
	if( pStreamOutBuffer_ ){
		pStreamOutBuffer_->Release();
	}
	{
		D3D11_BUFFER_DESC bd;
		ZeroMemory( &bd, sizeof(bd) );

		bd.ByteWidth = pass0_->getGSStride() * triCnt * 3;
		bd.Usage = D3D11_USAGE_DEFAULT;
		bd.BindFlags = D3D11_BIND_VERTEX_BUFFER | D3D11_BIND_STREAM_OUTPUT;
		bd.CPUAccessFlags = 0;
		bd.MiscFlags = 0;
		float iData[] = { 1.0f, 2.0f, 5.0f, 3.0f, 9.0f, 2.0f, 0.1f, 0.2f };
		D3D11_SUBRESOURCE_DATA initData;
		initData.pSysMem = iData;
		hr = pD3DDevice_->CreateBuffer( &bd, nullptr, &pStreamOutBuffer_ );
	}
	#endif
	
	//common constant buffer
	if( !pCommonShaderParameterCB_ ){
		D3D11_BUFFER_DESC bd;
		ZeroMemory( &bd, sizeof(bd) );
		bd.Usage = D3D11_USAGE_DEFAULT;
		bd.ByteWidth = sizeof( CommonShaderParameter );
		bd.BindFlags = D3D11_BIND_CONSTANT_BUFFER;
		bd.CPUAccessFlags = 0;
		if( pD3DDevice_->CreateBuffer( &bd, NULL, &pCommonShaderParameterCB_ ) != S_OK ){
			throw std::runtime_error( std::string( "CreateBuffer failed" ) );
		}
	}
	pD3DDeviceContext_->UpdateSubresource( pCommonShaderParameterCB_, 0, NULL, &commonShaderParameter_, 0, 0 );
	
	//Sampler state
	ID3D11SamplerState* pPointSamplerState;
	ID3D11SamplerState* pBilinerSamplerState;
	{
		D3D11_SAMPLER_DESC sd;
		ZeroMemory( &sd, sizeof( sd ) );
		sd.Filter = D3D11_FILTER_MIN_MAG_MIP_POINT;
		sd.MaxAnisotropy = 1;
		sd.ComparisonFunc = D3D11_COMPARISON_ALWAYS;
		sd.AddressU = D3D11_TEXTURE_ADDRESS_CLAMP;
		sd.AddressV = D3D11_TEXTURE_ADDRESS_CLAMP;
		sd.AddressW = D3D11_TEXTURE_ADDRESS_CLAMP;
		sd.MaxLOD = D3D11_FLOAT32_MAX;
		if( pD3DDevice_->CreateSamplerState( &sd, &pPointSamplerState ) != S_OK ){
			throw std::runtime_error( std::string( "SamplerState failed" ) );
		}

		sd.Filter = D3D11_FILTER_MIN_MAG_MIP_LINEAR;
		if( pD3DDevice_->CreateSamplerState( &sd, &pBilinerSamplerState ) != S_OK ){
			throw std::runtime_error( std::string( "SamplerState failed" ) );
		}
			
	}

	auto SetSamplers = [&](){
		ID3D11SamplerState* pSamplers[] = { pPointSamplerState, pBilinerSamplerState };
		pD3DDeviceContext_->VSSetSamplers( 0, 2, pSamplers );
		pD3DDeviceContext_->GSSetSamplers( 0, 2, pSamplers );
		pD3DDeviceContext_->PSSetSamplers( 0, 2, pSamplers );
	};
	
	//passPre
	//draw
	if( 1 ){
		//update
		//rasterState
		rsDesc.FillMode = D3D11_FILL_SOLID;
		rsDesc.CullMode = D3D11_CULL_NONE;
		rsDesc.MultisampleEnable = false;
		rsDesc.AntialiasedLineEnable = false;
		rsDesc.DepthBias = 0;
		rsDesc.DepthBiasClamp = 0.0f;
		rsDesc.SlopeScaledDepthBias = 0.0f;
		rsDesc.DepthClipEnable = true;
		rsDesc.ScissorEnable = true;
		pD3DDevice_->CreateRasterizerState( &rsDesc, &pNewRSState );
		pD3DDeviceContext_->RSSetState( pNewRSState );

		//setDepthState
		dsDesc.DepthEnable = true;
		dsDesc.StencilEnable = false;
		dsDesc.DepthFunc = D3D11_COMPARISON_LESS_EQUAL;
		dsDesc.DepthWriteMask = D3D11_DEPTH_WRITE_MASK_ALL;
		pD3DDevice_->CreateDepthStencilState( &dsDesc, &pNewDepthState );
		pD3DDeviceContext_->OMSetDepthStencilState( pNewDepthState, 1 );

		//setBlendState
		BlendDisable();
		pD3DDevice_->CreateBlendState( &blDesc, &pNewBlendState );
		float blendFactor[4] = { 1.0f, 1.0f, 1.0f, 1.0f };
		pD3DDeviceContext_->OMSetBlendState( pNewBlendState, blendFactor, 0xffffffff );

		//set shader
		streamOutOffset_ = 0;
		pD3DDeviceContext_->VSSetShader( passPre_->getVertexShader(), nullptr, 0 );
		pD3DDeviceContext_->VSSetConstantBuffers( 0, 1, &pCommonShaderParameterCB_ );
		pD3DDeviceContext_->IASetInputLayout( passPre_->getVertexLayout() );
		pD3DDeviceContext_->GSSetShader( nullptr, nullptr, 0 );
		pD3DDeviceContext_->PSSetShader( passPre_->getPixelShader(), nullptr, 0 );
		pD3DDeviceContext_->PSSetConstantBuffers( 0, 1, &pCommonShaderParameterCB_ );
		SetSamplers();

		//render target
		ID3D11DepthStencilView* pd = reinterpret_cast< ID3D11DepthStencilView* >( workDepthBuffer_->resourceHandle() );
		pD3DDeviceContext_->ClearDepthStencilView( pd, D3D11_CLEAR_DEPTH, 1.0f, 0.0f );
		
		pD3DDeviceContext_->OMSetRenderTargets( 0, nullptr, pd );

		//SO
		pD3DDeviceContext_->SOSetTargets( 0, nullptr, nullptr );
		
		//draw
		unsigned int strides[] = { pass0_->getVSStride(0), pass0_->getVSStride(1), pass0_->getVSStride(2) };
		unsigned int offsets[] = { 0, 0, 0 };
		ID3D11Buffer* vb[] = { pVertexBuffer_, pVertexNormalBuffer_, pVertexUvBuffer_ };
		
		pD3DDeviceContext_->IASetVertexBuffers( 0, 3, vb, strides , offsets );
		pD3DDeviceContext_->IASetIndexBuffer( pIndexBuffer_, DXGI_FORMAT_R32_UINT, 0 );
		pD3DDeviceContext_->IASetPrimitiveTopology( D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST );

		pD3DDeviceContext_->DrawIndexed( triCnt * 3, 0, 0 );

	}
	
	//pass0
	//accumulate per face curvature
	if( 1 ){
		//update
		
		//rasterState
		rsDesc.FillMode = D3D11_FILL_SOLID;
		rsDesc.CullMode = D3D11_CULL_NONE;
		rsDesc.MultisampleEnable = false;
		rsDesc.AntialiasedLineEnable = false;
		rsDesc.DepthBias = 0;
		rsDesc.DepthBiasClamp = 0.0f;
		rsDesc.SlopeScaledDepthBias = 0.0f;
		rsDesc.DepthClipEnable = false;
		rsDesc.ScissorEnable = false;
		pD3DDevice_->CreateRasterizerState( &rsDesc, &pNewRSState );
		pD3DDeviceContext_->RSSetState( pNewRSState );

		//setDepthState
		dsDesc.DepthEnable = true;
		dsDesc.StencilEnable = false;
		dsDesc.DepthFunc = D3D11_COMPARISON_LESS_EQUAL;
		dsDesc.DepthWriteMask = D3D11_DEPTH_WRITE_MASK_ALL;
		pD3DDevice_->CreateDepthStencilState( &dsDesc, &pNewDepthState );
		pD3DDeviceContext_->OMSetDepthStencilState( pNewDepthState, 1 );

		//setBlendState
		BlendEnable();
		pD3DDevice_->CreateBlendState( &blDesc, &pNewBlendState );
		float blendFactor[4] = { 1.0f, 1.0f, 1.0f, 1.0f };
		pD3DDeviceContext_->OMSetBlendState( pNewBlendState, blendFactor, 0xffffffff );

		//set shader
		streamOutOffset_ = 0;
		pD3DDeviceContext_->VSSetShader( pass0_->getVertexShader(), nullptr, 0 );
		pD3DDeviceContext_->VSSetConstantBuffers( 0, 1, &pCommonShaderParameterCB_ );
		pD3DDeviceContext_->IASetInputLayout( pass0_->getVertexLayout() );
		pD3DDeviceContext_->GSSetShader( pass0_->getGeometryShader(), nullptr, 0 );
		pD3DDeviceContext_->GSSetConstantBuffers( 0, 1, &pCommonShaderParameterCB_ );
		pD3DDeviceContext_->PSSetShader( pass0_->getPixelShader(), nullptr, 0 );
		pD3DDeviceContext_->PSSetConstantBuffers( 0, 1, &pCommonShaderParameterCB_ );
		SetSamplers();

		//render target
		ID3D11DepthStencilView* pd = reinterpret_cast< ID3D11DepthStencilView* >( workDepthBuffer_->resourceHandle() );
		
		ID3D11RenderTargetView* rv[] = { renderTargets_[RTCurvature]->getRenderTarget() };
		static const float clearColor[4] = { 0.0f, 0.0f, 0.0f, 1.0f };
		ID3D11RenderTargetView* pv = reinterpret_cast< ID3D11RenderTargetView* >( renderTargets_[RTCurvature]->getRenderTarget() );
		pD3DDeviceContext_->ClearRenderTargetView( pv, clearColor );
		
		pD3DDeviceContext_->OMSetRenderTargets( 1, rv, pd );

		//SO
		//pD3DDeviceContext_->SOSetTargets( 1, &pStreamOutBuffer_, &streamOutOffset_ );

		//draw
		unsigned int strides[] = { pass0_->getVSStride(0), pass0_->getVSStride(1), pass0_->getVSStride(2) };
		unsigned int offsets[] = { 0, 0, 0 };
		ID3D11Buffer* vb[] = { pVertexBuffer_, pVertexNormalBuffer_, pVertexUvBuffer_ };
		
		pD3DDeviceContext_->IASetVertexBuffers( 0, 3, vb, strides , offsets );
		pD3DDeviceContext_->IASetIndexBuffer( pIndexBuffer_, DXGI_FORMAT_R32_UINT, 0 );
		pD3DDeviceContext_->IASetPrimitiveTopology( D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST );

		pD3DDeviceContext_->DrawIndexed( triCnt * 3, 0, 0 );

	}
	
	//pass1
	//draw
	if( 1 ){
		//update
		//rasterState
		rsDesc.FillMode = D3D11_FILL_SOLID;
		rsDesc.CullMode = D3D11_CULL_NONE;
		rsDesc.MultisampleEnable = true;
		rsDesc.AntialiasedLineEnable = false;
		rsDesc.DepthBias = 0;
		rsDesc.DepthBiasClamp = 0.0f;
		rsDesc.SlopeScaledDepthBias = 0.0f;
		rsDesc.DepthClipEnable = true;
		rsDesc.ScissorEnable = true;
		pD3DDevice_->CreateRasterizerState( &rsDesc, &pNewRSState );
		pD3DDeviceContext_->RSSetState( pNewRSState );

		//setDepthState
		dsDesc.DepthEnable = true;
		dsDesc.StencilEnable = false;
		dsDesc.DepthFunc = D3D11_COMPARISON_LESS_EQUAL;
		dsDesc.DepthWriteMask = D3D11_DEPTH_WRITE_MASK_ALL;
		pD3DDevice_->CreateDepthStencilState( &dsDesc, &pNewDepthState );
		pD3DDeviceContext_->OMSetDepthStencilState( pNewDepthState, 1 );

		//setBlendState
		BlendDisable();
		pD3DDevice_->CreateBlendState( &blDesc, &pNewBlendState );
		float blendFactor[4] = { 1.0f, 1.0f, 1.0f, 1.0f };
		pD3DDeviceContext_->OMSetBlendState( pNewBlendState, blendFactor, 0xffffffff );

		//set shader
		streamOutOffset_ = 0;
		pD3DDeviceContext_->VSSetShader( pass1_->getVertexShader(), nullptr, 0 );
		pD3DDeviceContext_->VSSetConstantBuffers( 0, 1, &pCommonShaderParameterCB_ );
		pD3DDeviceContext_->IASetInputLayout( pass1_->getVertexLayout() );
		pD3DDeviceContext_->GSSetShader( nullptr, nullptr, 0 );
		pD3DDeviceContext_->PSSetShader( pass1_->getPixelShader(), nullptr, 0 );
		pD3DDeviceContext_->PSSetConstantBuffers( 0, 1, &pCommonShaderParameterCB_ );
		SetSamplers();

		//render target
		ID3D11DepthStencilView* pd = reinterpret_cast< ID3D11DepthStencilView* >( outputDepthBuffer_->resourceHandle() );

		ID3D11RenderTargetView* pv = reinterpret_cast< ID3D11RenderTargetView* >( outputRenderBuffer_->resourceHandle() );
		pD3DDeviceContext_->OMSetRenderTargets( 1, &pv, pd );

		//SO
		pD3DDeviceContext_->SOSetTargets( 0, nullptr, nullptr );

		//Texture
		ID3D11ShaderResourceView* pResources[] = {
			renderTargets_[ RTCurvature ]->getShaderResource(),
		};
		pD3DDeviceContext_->VSSetShaderResources( 0, 1, pResources );
		
		//draw
		unsigned int strides[] = { pass0_->getVSStride(0), pass0_->getVSStride(1), pass0_->getVSStride(2) };
		unsigned int offsets[] = { 0, 0, 0 };
		ID3D11Buffer* vb[] = { pVertexBuffer_, pVertexNormalBuffer_, pVertexUvBuffer_ };
		
		pD3DDeviceContext_->IASetVertexBuffers( 0, 3, vb, strides , offsets );
		pD3DDeviceContext_->IASetIndexBuffer( pIndexBuffer_, DXGI_FORMAT_R32_UINT, 0 );
		pD3DDeviceContext_->IASetPrimitiveTopology( D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST );

		pD3DDeviceContext_->DrawIndexed( triCnt * 3, 0, 0 );

	}
	
	pD3DDeviceContext_->OMSetDepthStencilState( pPrevDSState, 1 );
	pD3DDeviceContext_->RSSetState( pPrevRSState );
	pD3DDeviceContext_->OMSetBlendState( pPrevBlendState, prevBlendFactor, prevSampleMask );

}

//- - - - - - - - - - - - - - - - - -
//
PPRenderTarget C_DX11CurvVPUserRenderOp::targetOverrideList( unsigned int &listSize ){
	if( outputRenderBuffer_ ){
		listSize = 1;
		return &outputRenderBuffer_;
	}else{
		listSize = 0;
		return nullptr;
	}
}

//- - - - - - - - - - - - - - - - - -
//
MStatus C_DX11CurvVPUserRenderOp::execute(	const MHWRender::MDrawContext& context ){

	if( !isInit_ ){
		DebugPrintf( "!isInit_" );
		return MStatus::kFailure;
	}
	
	MStatus status;

	MHWRender::MRenderer *theRenderer = MHWRender::MRenderer::theRenderer();
	if( !theRenderer ){
		return MS::kFailure;
	}

	theRenderer->outputTargetSize( width_, height_ );

	pD3DDevice_ = (ID3D11Device *)theRenderer->GPUDeviceHandle();
	pD3DDevice_->GetImmediateContext( &pD3DDeviceContext_ );

	drawSceneObjects( context, pD3DDevice_, pD3DDeviceContext_, width_, height_ );
	
	return MStatus::kSuccess;

}

//- - - - - - - - - - - - - - - - - -
//
const MHWRender::MCameraOverride* C_DX11CurvVPUserRenderOp::cameraOverride( void ){
	M3dView view;
	if ( panelName_.length() && ( M3dView::getM3dViewFromModelPanel( panelName_, view ) == MStatus::kSuccess) )
	{
		view.getCamera( cameraOverride_.mCameraPath );
		return &cameraOverride_;
	}
	return nullptr;

}
