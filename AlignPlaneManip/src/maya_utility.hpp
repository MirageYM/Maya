/*
  maya_utility
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/

#pragma once
#if !defined( MAYA_UTILITY_HPP_INCLUDED__ )
#define MAYA_UTILITY_HPP_INCLUDED__

#include <maya/MIOStream.h>
//C
#include <stdio.h>
#include <stdlib.h>

//Maya
#include <maya/MGlobal.h>
#include <maya/MPlug.h>
#include <maya/MVector.h>
#include <maya/MString.h>

//Windows
#include <windows.h>


namespace MayaUtility{

	//--------------------------------------------------------
	void DebugPrintf( const char* str, ... );

	//--------------------------------------------------------
	template< typename T>
	inline T plug2MVector( const MPlug& plug ){
		if( plug.numChildren() == 3 ){

			double x,y,z;
			MPlug rx = plug.child( 0 );
			MPlug ry = plug.child( 1 );
			MPlug rz = plug.child( 2 );
			rx.getValue( x );
			ry.getValue( y );
			rz.getValue( z );
			T result( x, y, z );

			return result;
		}else{
			MGlobal::displayError( "Expected 3 children for plug "+ MString(plug.name()) );
			T result( 0.0, 0.0, 0.0 );
			return result;
		}
	}
	
	//--------------------------------------------------------
	template< typename T >
	inline void vector2Plug( const T& v,  const MPlug& plug ){
		if( plug.numChildren() == 3 ){

			double x,y,z;
			MPlug rx = plug.child( 0 );
			MPlug ry = plug.child( 1 );
			MPlug rz = plug.child( 2 );
			rx.setValue( v.x );
			ry.setValue( v.y );
			rz.setValue( v.z );

		}
	}

}

#endif //MAYA_UTILITY_HPP_INCLUDED__