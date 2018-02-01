#!/usr/bin/env python2.7
# split the RECORDSEP delimited samples in a file into lines
import sys
import argparse
import string
#-----------------------
def parseCmdLine():
    parser = argparse.ArgumentParser( \
    description='look at features extracted for loaded sample files.\nstdin to stdout')

    parser.add_argument('-d', '--delim',  dest='delim', action='store',
	default=';;', help='record delimiter')

    parser.add_argument('-t', '--truncate', dest='truncate', action='store',
	default=0, type=int, help='truncate sample records to specified length')

    args = parser.parse_args()

    return args
#-----------------------
def process():
    args = parseCmdLine()

    input = sys.stdin.read()
    for line in input.split(args.delim):
	if args.truncate == 0:
	    print line
	else:
	    print line[:args.truncate]

if __name__ == "__main__":
    process()
