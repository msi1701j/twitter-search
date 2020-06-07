#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import shelve
import argparse

def print_shelve( shelvefile ):
    if shelvefile is not None:
        print( 'Shelve File:', shelvefile)
        try:
            with shelve.open(shelvefile, flag='r') as dbase:
                for k in dbase.keys():
                    print( '{}: {}'.format(k, dbase[k]) )
        except Exception as e:
            print(e)
            sys.exit(1)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('shelvefile', default='shelvefile',
										help=u'shelveファイル名')
	shelvefile = parser.parse_args().shelvefile
	print_shelve( shelvefile )
