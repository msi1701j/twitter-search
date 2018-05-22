#!/opt/python/twitter-search/bin/python3
# -*- coding: utf-8 -*-

import shelve
import argparse

def print_shelve( shelvefile ):
	if shelvefile is not None:
		print( 'Shelve File:', shelvefile)
		dbase = shelve.open(shelvefile, flag='r')
		for k in dbase.keys():
			print( '{}: {}'.format(k, dbase[k]) )
		dbase.close()


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('shelvefile', default='shelvefile', help=u'shelveファイル名')
	shelvefile = parser.parse_args().shelvefile
	print_shelve( shelvefile )
