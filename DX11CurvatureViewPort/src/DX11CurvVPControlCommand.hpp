/*
  DX11CurvVPControlCommand
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/

#pragma once

#if !defined( DX11CURVVPCONTROLCOMMAND_HPP_INCLUDED__ )
#define DX11CURVVPCONTROLCOMMAND_HPP_INCLUDED__

#include <maya/MIOStream.h>
//C
#include <stdio.h>
#include <stdlib.h>

//Maya
#include <maya/MString.h>

#include <maya/MPxCommand.h>
#include <maya/MSyntax.h>
#include <maya/MArgDatabase.h>
#include <maya/MArgList.h>
#include <maya/M3dView.h>

//project


//--------------------------------------------------------
//! C_DX11CurvVPControlCommand
//! 
//
//--------------------------------------------------------
class C_DX11CurvVPControlCommand: public MPxCommand{
 public:
	//Creators
	inline C_DX11CurvVPControlCommand(){};
	inline virtual ~C_DX11CurvVPControlCommand(){};

 public:
	//Manipulators
	MStatus	doIt					( const MArgList& args );
	static MSyntax		newSyntax	( void );
	static void*		creator		( void );

 private:
	MStatus				parseArgsAndSet( const MArgList& args );
	
};


#endif