#!/usr/bin/env python2.7

#-----------------------------------
'''
  Purpose:
	   run sql to get GXD lit triage training set
	   Data transformations include:
	    replacing non-ascii chars with ' '
	    replacing FIELDSEP and RECORDSEP chars in the doc text w/ ' '

  Outputs:     to stdout
'''
OutputColumns = [
    'yes_no', 	# relevant to GXD. =yes for these samples
    'pubmed',
    'isDiscard',# MGI-discard value. =0 for these samples
    'status',	# GXD lit triage status
    'journal',
    'text',	# '|\n\t\r' replaced by space & convert Unicode to space
    ]	# this order is assumed in sampleDataLib.py

#-----------------------------------
# Try to keep this script easy to run from various servers,
# Try to keep import dependencies down to standard Python libaries
import sys
import os
import string
import time
import argparse
import ConfigParser
import db
#-----------------------------------
cp = ConfigParser.ConfigParser()
cp.optionxform = str # make keys case sensitive
cl = ['.']+['/'.join(l)+'/config.cfg' for l in [['..']*i for i in range(1,4)]]
cp.read(cl)
#
FIELDSEP = eval(cp.get("DEFAULT", "FIELDSEP"))
RECORDSEP = eval(cp.get("DEFAULT", "RECORDSEP"))
#-----------------------------------

def getArgs():
    parser = argparse.ArgumentParser( \
	description='Get GXD lit triage training samples, write to stdout')

    parser.add_argument('-s', '--server', dest='server', action='store',
        required=False, default='dev',
        help='db server. Shortcuts:  adhoc, prod, or dev (default)')

    parser.add_argument('-d', '--database', dest='database', action='store',
        required=False, default='mgd',
        help='Which database. Example: mgd (default)')

    parser.add_argument('--query', dest='query', action='store',
        required=False, default='all', choices=['all', 'pos', 'neg1', 'neg2'],
        help='which subset of the training data to get')

    parser.add_argument('-l', '--limit', dest='nResults',
	type=int, default=0, 		# 0 means ALL
        help="limit SQL to n results. Default is no limit")

    parser.add_argument('-q', '--quiet', dest='verbose', action='store_false',
        required=False, help="skip helpful messages to stderr")

    args =  parser.parse_args()

    if args.server == 'adhoc':
	args.host = 'mgi-adhoc.jax.org'
	args.db = 'mgd'
    if args.server == 'prod':
	args.host = 'bhmgidb01'
	args.db = 'prod'
    if args.server == 'dev':
	args.host = 'bhmgidevdb01'
	args.db = 'prod'

    return args
#-----------------------------------

SQLSEPARATOR = '||'

# get Positive samples created 1/1/2016 - 1/1/2018
PosQuery1 =  \
'''
select 'yes' as yes_no, a.accid pubmed, r.isDiscard, bs.gxd_status as status
    , r.journal
    , translate(bd.extractedtext, E'\r', ' ') as "text" -- remove ^M's
from bib_refs r join bib_workflow_data bd on (r._refs_key = bd._refs_key)
    join acc_accession a on
     (a._object_key = r._refs_key and a._logicaldb_key=29 -- pubmed
      and a._mgitype_key=1 )
    join bib_status_view bs on (bs._refs_key = r._refs_key)
where
    r.creation_date > '1/01/2016'
and r.creation_date < '1/01/2018'
and bd.haspdf=1
and r.isdiscard = 0
and bs.gxd_status in ('Chosen', 'Indexed', 'Full-coded')
-- and r._referencetype_key=31576687 -- peer reviewed article
-- and bd._supplemental_key =34026997  -- "supplemental attached"
''' 

# get Negative samples with MGI-discard = 0, created after 10/1/2017
NegQuery1 =  \
'''
select 'no' as yes_no, a.accid pubmed, r.isDiscard, bs.gxd_status as status
    , r.journal
    , translate(bd.extractedtext, E'\r', ' ') as "text" -- remove ^M's
from bib_refs r join bib_workflow_data bd on (r._refs_key = bd._refs_key)
    join acc_accession a on
     (a._object_key = r._refs_key and a._logicaldb_key=29 -- pubmed
      and a._mgitype_key=1 )
    join bib_status_view bs on (bs._refs_key = r._refs_key)
where
    r.creation_date > '10/01/2017'
and r.creation_date < '1/01/2018'
and bd.haspdf=1
and r.isdiscard = 0
and bs.gxd_status = 'Rejected'
-- and r._referencetype_key=31576687 -- peer reviewed article
-- and bd._supplemental_key =34026997  -- "supplemental attached"
''' 

# get Negative samples with MGI-discard = 1, created after 10/1/2017
NegQuery2=  \
'''
select  'no' as yes_no, a.accid pubmed, r.isDiscard, bs.gxd_status as status
    , r.journal
    , translate(bd.extractedtext, E'\r', ' ') as "text" -- remove ^M's
from bib_refs r join bib_workflow_data bd on (r._refs_key = bd._refs_key)
    join acc_accession a on
     (a._object_key = r._refs_key and a._logicaldb_key=29 -- pubmed
      and a._mgitype_key=1 )
    join bib_status_view bs on (bs._refs_key = r._refs_key)
where
    r.creation_date > '10/01/2017'
and r.creation_date < '1/01/2018'
and bd.haspdf=1
and r.isdiscard = 1
-- and bs.gxd_status = 'Rejected'
-- and r._referencetype_key=31576687 -- peer reviewed article
-- and bd._supplemental_key =34026997  -- "supplemental attached"
''' 

#-----------------------------------

def getQueries(args):

    if args.query == 'pos':
	queries = [PosQuery1]
    elif args.query == 'neg1':
	queries = [NegQuery1]
    elif args.query == 'neg2':
	queries = [NegQuery2]
    else:
	queries = [PosQuery1, NegQuery1, NegQuery2]

    if args.nResults > 0:
	limitText = "\nlimit %d\n" % args.nResults
	final = []
	for q in queries:
	    final.append( q + limitText )
    else: final = queries

    return final
#-----------------------------------

def process():

    args = getArgs()

    db.set_sqlServer  ( args.host)
    db.set_sqlDatabase( args.db)
    db.set_sqlUser    ("mgd_public")
    db.set_sqlPassword("mgdpub")

    if args.verbose:
	sys.stderr.write( "Hitting database %s %s as mgd_public\n\n" % \
							(args.host, args.db))
    startTime = time.time()

    sys.stdout.write( FIELDSEP.join(OutputColumns) + RECORDSEP )

    for i, q in enumerate(getQueries(args)):
	qStartTime = time.time()

	results = db.sql( string.split(q, SQLSEPARATOR), 'auto')

	if args.verbose:
	    sys.stderr.write( "Query %d SQL time: %8.3f seconds\n\n" % \
						(i, time.time()-qStartTime))
	nResults = writeResults(results[-1]) # db.sql returns list of rslt lists

	if args.verbose:
	    sys.stderr.write( "%d references processed\n\n" % (nResults) )

    if args.verbose:
	sys.stderr.write( "Total time: %8.3f seconds\n\n" % \
						    (time.time()-startTime))
#-----------------------------------

def writeResults( results	# list of records (dicts)
    ):
    # write records to stdout
    # return count of records written
    for r in results:
	sys.stdout.write( FIELDSEP.join( [
	    r['yes_no'],
	    r['pubmed'],
	    str(r['isDiscard']),
	    r['status'],
	    r['journal'],
	    removeNonAscii(r['text']).replace(RECORDSEP,' ').replace(FIELDSEP,' '),
	    ] )
	    + RECORDSEP
	)
    return len(results)
#-----------------------------------

def removeNonAscii(text):
    return ''.join([i if ord(i) < 128 else ' ' for i in text])
#-----------------------------------

if __name__ == "__main__": process()
