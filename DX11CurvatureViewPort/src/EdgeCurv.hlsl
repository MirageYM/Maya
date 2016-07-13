cbuffer CommonShaderParameter:register( b0 ){
	matrix	gWorldView				:packoffset( c0 );
	matrix	gProjection				:packoffset( c4 );
	matrix	gWorldViewProjection	:packoffset( c8 );
	float	gViewWidth				:packoffset( c12 );
	float	gViewHeight				:packoffset( c12.y );
	float	gValPower				:packoffset( c12.z );
	float	gValMult				:packoffset( c12.w );
	matrix	gWorld					:packoffset( c13 );
	float4	gColMid					:packoffset( c17 );
	float4	gColPos					:packoffset( c18 );
	float4	gColNeg					:packoffset( c19 );
	float4	gGridWidth				:packoffset( c20 );
	float4	gGridOffset				:packoffset( c21 );
	float4	gGridDist				:packoffset( c22 );
	float	gGridAlpha				:packoffset( c23 );
	float	gCheckerAlpha			:packoffset( c23.y );
	float	gCheckerRepeat			:packoffset( c23.z );
	float	gAmbient				:packoffset( c23.w );
};

SamplerState ClampedPointSampler: register( s0 );
SamplerState ClampedBilinerSampler: register( s1 );

Texture2D gCurvatureTexture: register( t0 );
static const float	PAI = 3.14159265f;

//--------------------------------------------------------
//Input - Output
//--------------------------------------------------------
struct VS_In{
	float3	localPos	:POSITION;
	float3	normal		:TEXCOORD0;
	float2	uv			:TEXCOORD1;
};


struct PSPre_In{
	float4	Pos			:SV_POSITION;
};

struct GS0_In{
	float4	Pos			:SV_POSITION;
	float4	localPos	:POSITION;
	float4	wvPos		:TEXCOORD0;
	float4	wPos		:TEXCOORD2;
	float4	normal		:TEXCOORD1;
};

struct PS0_In{
	float4	Pos			:SV_POSITION;
	float4	wvPos		:TEXCOORD0;
	float4	localPos	:POSITION;
	float4	curvature	:TEXCOORD1;
};

struct PS0_Out{
	float4	curvature	:SV_TARGET0;
};

struct PS1_In{
	float4	Pos			:SV_POSITION;
	float4	wvPos		:TEXCOORD0;
	float4	localPos	:POSITION;
	float4	curvature	:TEXCOORD1;
	float4	wPos		:TEXCOORD2;
	float4	normal		:TEXCOORD3;
	float2	uv			:TEXCOORD4;
};

struct PS1_Out{
	float4	color		:SV_TARGET0;
};

//--------------------------------------------------------
//toTexPreSV
//--------------------------------------------------------
int2 toTexPreSV( float4 pos, float2 offset ){
	pos /= pos.w;
	float2 ndc = 0.5f * float2( pos.x, -pos.y ) + 0.5f;
	ndc.x *= gViewWidth;
	ndc.y *= gViewHeight;
	ndc.x += 0.5f / gViewWidth;
	ndc.y -= 0.5f / gViewHeight;
	ndc.x += offset.x / gViewWidth;
	ndc.y += offset.y / gViewHeight;
	int2 ret = floor( ndc );
	return ret;
}

//--------------------------------------------------------
//toTexPreSV
//--------------------------------------------------------
int2 svToPos( float4 pos, float2 offset ){
	pos /= pos.w;
	float2 ndc = 0.5f * float2( pos.x, -pos.y ) + 0.5f;
	ndc.x *= gViewWidth;
	ndc.y *= gViewHeight;
	ndc.x += 0.5f / gViewWidth;
	ndc.y -= 0.5f / gViewHeight;
	ndc.x += offset.x;
	ndc.y += offset.y;
	int2 ret = floor( ndc );
	return ret;
}

//--------------------------------------------------------
//lookupTex4
//--------------------------------------------------------
float4 lookupTex4( float4 pos, Texture2D tex, float2 offset ){
	float4 n = tex.Load( int3( toTexPreSV( pos, offset ), 0 ) );
	return n;
}

//--------------------------------------------------------
// vsPre
//--------------------------------------------------------
PSPre_In vsPre( VS_In input ){
	PSPre_In ret;
	ret.Pos = mul( float4( input.localPos.xyz, 1.0f ), gWorldViewProjection );
	ret.Pos.z += 0.01f;
	return ret;
}

//--------------------------------------------------------
// psPre
//--------------------------------------------------------
float4 psPre( PSPre_In input ): SV_TARGET{
	float4 ret;
	ret = 0.0f;
	return ret;
}

//--------------------------------------------------------
// vs0
//--------------------------------------------------------
GS0_In vs0( VS_In input ){
	GS0_In ret;
	ret.localPos = float4( input.localPos, 1.0f );
	ret.Pos = mul( float4( input.localPos.xyz, 1.0f ), gWorldViewProjection );

	int2 sc = toTexPreSV( ret.Pos, float2( 0.0f, 0.0f ) );
	float2 p = float2( (float)sc.x + 0.5f, (float)sc.y + 0.5f );
	p.x -= 0.5f / gViewWidth;
	p.y += 0.5f / gViewHeight;
	p.x /= gViewWidth;
	p.y /= gViewHeight;
	p -= 0.5f;
	p *= 2.0f;
	p.y = -p.y;
	p *= ret.Pos.w;
	ret.Pos.x = p.x;
	ret.Pos.y = p.y;
	
	ret.wvPos = mul( float4( input.localPos.xyz, 1.0f ), gWorldView );
	ret.wPos = mul( float4( input.localPos.xyz, 1.0f ), gWorld );
	ret.normal = mul( float4( input.normal.xyz, 0.0f ), gWorld );
	return ret;
}

//--------------------------------------------------------
// gs0
//--------------------------------------------------------
[maxvertexcount(3)]
void gs0( triangle GS0_In inputStream[3], inout PointStream< PS0_In > outputStream ){

	PS0_In output;
	float area = length( cross( inputStream[1].normal.xyz - inputStream[0].normal.xyz, inputStream[2].normal.xyz - inputStream[0].normal.xyz ) ) * 0.5f;

	for( int i = 0; i < 3; ++i ){
		output.Pos = inputStream[i].Pos;
		output.wvPos = inputStream[i].wvPos;
		output.localPos = inputStream[i].localPos;

		int2 indices = { ( i + 1 ) % 3, ( i + 2 ) % 3 };

		float k = 0.0f;
		for( int j = 0; j < 2; ++j ){
			float3 ev = inputStream[indices[j]].wPos.xyz - inputStream[i].wPos.xyz;
			float h = dot( inputStream[i].normal.xyz, ev );
			float3 evPlane = ev - inputStream[i].normal.xyz * h;
			float t = max( length( evPlane ), 0.0000001f );
			k -= 1.0f / ( length( ev ) / atan( h / t ) );
		}

		output.curvature = float4( k, k, 1.0f, 1.0f );
		outputStream.Append( output );
	}

	outputStream.RestartStrip();

}

//--------------------------------------------------------
// ps0
//--------------------------------------------------------
PS0_Out ps0( PS0_In input ){
	PS0_Out ret;
	ret.curvature = input.curvature;
	return ret;
}

//--------------------------------------------------------
// vs1
//--------------------------------------------------------
PS1_In vs1( VS_In input ){
	PS1_In ret;
	ret.localPos = float4( input.localPos.xyz, 1.0f );
	ret.Pos = mul( float4( input.localPos.xyz, 1.0f ), gWorldViewProjection );
	ret.wvPos = mul( float4( input.localPos.xyz, 1.0f ), gWorldView );
	ret.wPos = mul( float4( input.localPos.xyz, 1.0f ), gWorld );
	ret.normal = mul( float4( input.normal.xyz, 0.0f ), gWorld );
	ret.uv = input.uv.xy;
	
	ret.curvature = lookupTex4( ret.Pos, gCurvatureTexture, float2( 0.5f, 0.5f ) );

	static int2 c[] = {	int2( -1.0f, -1.0f ),
						int2( -1.0f, 0.0f ),
						int2( -1.0f, 1.0f ),
						int2( 1.0f, -1.0f ),
						int2( 1.0f, 0.0f ),
						int2( 1.0f, 1.0f ),
						int2( 0.0f, -1.0f ),
						int2( 0.0f, 1.0f ) };

	if( ret.curvature.z < 0.1f ){
		for( int i = 0; i < 8; ++i ){
			ret.curvature = lookupTex4( ret.Pos, gCurvatureTexture, c[i] );
			if( ret.curvature.z > 0.1f ){
				break;
			}
		}
	}
	ret.curvature.xy /= ret.curvature.z;
	return ret;
}

//--------------------------------------------------------
// ps1
//--------------------------------------------------------
PS1_Out ps1( PS1_In input ){
	PS1_Out ret;
	
	float4 result = gColMid;

	float val = input.curvature.x * gValMult;

	if( val > 0.0f ){
		val = pow( val, gValPower );
	}else{
		val = -pow( -val, gValPower );
	}

	result = lerp( result, gColPos, clamp( val, 0.0f, 1.0f ) );
	result = lerp( result, gColNeg, clamp( -val, 0.0f, 1.0f ) );
	
	ret.color = result;
	ret.color *= max( gAmbient, input.normal.y );

	int xgd = clamp( abs( fmod( input.wPos.x + gGridOffset.x, gGridDist.x ) ) / gGridWidth.x - 1.0f, 0.0f, 1.0f );
	int ygd = clamp( abs( fmod( input.wPos.y + gGridOffset.y, gGridDist.y ) ) / gGridWidth.y - 1.0f, 0.0f, 1.0f );
	int zgd = clamp( abs( fmod( input.wPos.z + gGridOffset.z, gGridDist.z ) ) / gGridWidth.z - 1.0f, 0.0f, 1.0f );
	ret.color *= clamp( (float)xgd, gGridAlpha, 1.0f );
	ret.color *= clamp( (float)ygd, gGridAlpha, 1.0f );
	ret.color *= clamp( (float)zgd, gGridAlpha, 1.0f );

	static float checkerRepeat = gCheckerRepeat * 2.0f;
	int chx = (int)( input.uv.x * checkerRepeat ) % 2;
	int chy = (int)( input.uv.y * checkerRepeat ) % 2;
	if( input.uv.x < 0.0f ){
		chx = !chx;
	}
	if( input.uv.y < 0.0f ){
		chx = !chy;
	}
	int chOn = chx ^ chy;
	ret.color *= clamp( (float)chOn, gCheckerAlpha, 1.0f );
	return ret;
}

