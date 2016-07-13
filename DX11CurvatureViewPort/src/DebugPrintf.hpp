/*
  DebugPrintf
  Copyright (C) 2015 Yasutoshi Mori (Mirage)
  $Id:  $
*/

#pragma once
#if !defined( DEBUG_PRINTF_HPP_INCLUDED__ )
#define DEBUG_PRINTF_HPP_INCLUDED__

//C
#include <stdio.h>
#include <stdlib.h>

//Windows
#include <windows.h>

void DebugPrintf( const char* str, ... );


#endif //MAYA_UTILITY_HPP_INCLUDED__