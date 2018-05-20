#
# -*- coding: utf-8 -*-

import sys

_DEBUG = False

def Debug_init(flag):
	global _DEBUG

	_DEBUG = flag
	return _DEBUG

def Debug_print( *strings ):
	global _DEBUG
	if _DEBUG:
		print( 'Debug:', *strings, file=sys.stderr )

def Debug_var_print( variable_str, variable ):
	global _DEBUG
	if _DEBUG:
		Debug_print( variable_str, '=', variable )

if __name__ == '__main__':
	print( '_DEBUG =', _DEBUG )
	Debug_var_print( '_DEBUG', _DEBUG )

	_DEBUG = True
	print( 'init()' )
	Debug_init()
	Debug_var_print( '_DEBUG', _DEBUG )
