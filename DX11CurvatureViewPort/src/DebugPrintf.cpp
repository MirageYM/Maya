/*
  DebugPrintf
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/

#include "DebugPrintf.hpp"

#define MAX_CHAR_LENGTH 4096

void DebugPrintf( const char* str, ... ){
	va_list	argp;
	char buf[ MAX_CHAR_LENGTH ];
	va_start( argp, str );
	vsprintf_s( buf, MAX_CHAR_LENGTH, str, argp);
	va_end( argp );
	OutputDebugStringA( buf );
}
