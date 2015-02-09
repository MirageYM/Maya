#include <windows.h>
#include <stdio.h>

#include "maya_utility.hpp"


namespace MayaUtility{

	void DebugPrintf( const char* str, ... ){
		va_list	argp;
		char buf[256];
		va_start( argp, str );
		vsprintf( buf, str, argp);
		va_end( argp );
		OutputDebugString( buf );
	}

}