/*
  maya_utility
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/

#include "maya_utility.hpp"

namespace MayaUtility{

	void DebugPrintf( const char* str, ... ){
		va_list	argp;
		char buf[2048];
		va_start( argp, str );
		vsprintf_s( buf, 2048, str, argp);
		va_end( argp );
		OutputDebugString( buf );
	}

}