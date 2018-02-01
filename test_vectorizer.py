#!/usr/bin/env python2.7
# test vectorizer(s) to make sure they are getting the right features
# write features list to stdout
import sys
import argparse
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.datasets import load_files
#-----------------------
def parseCmdLine():
    parser = argparse.ArgumentParser( \
    description='test out vectorizer options')

    parser.add_argument('-d', '--dataDir', dest='dataDir', action='store',
	default=None,
	help='top level directory of sample data files. Reads stdin if not specified')

    parser.add_argument('--maxNgram', dest='maxNgram', action='store',
	type=int, default=1, help='max for ngram_range=(1,??). Default=1')

    parser.add_argument('--max_df', dest='max_df', action='store',
	type=float, default=0.8, help='Default=0.8')

    parser.add_argument('--min_df', dest='min_df', action='store',
	type=float, default=0.1, help='Default=0.1')

    parser.add_argument('-q', '--quiet', dest='verbose', action='store_false',
        required=False, help="skip helpful messages to stderr")

    args = parser.parse_args()

    return args
#-----------------------
def process():
    args = parseCmdLine()

    v = TfidfVectorizer(
			strip_accents=None,
			decode_error='strict',
			lowercase=False,
			stop_words="english",
			#token_pattern=u'(?i)\\b([a-z_]\w+)\\b',
			ngram_range=(1,args.maxNgram),
			min_df=args.min_df,
			max_df=args.max_df,
			)
    if args.dataDir:
	dataSet = load_files( args.dataDir )
	v.fit(dataSet.data)
	print "data Dir: %s" % args.dataDir
    else:		# just use inline text
	testdocs = [ \
	    " Here..here are some! here are things before URL.",
	    "http://foo.com.",
	    "in between URLs! http://xyz yuck?",
	    "...and..some..Stemmed stemming stem",
	    "Some stop words: almost became because become becomes being",
	    ]
	testdocs = [ sys.stdin.read() ]
	v.fit(testdocs)
	print "data from stdin"

    print v
    print "Features: %d" % len(v.get_feature_names())
    for f in sorted(v.get_feature_names()):
	print "'%s'" % str(f)
    return

if __name__ == "__main__":
    process()
