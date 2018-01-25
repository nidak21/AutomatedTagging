#!/usr/bin/env python2.7 
#
# Library to support handling of lit triage text documents
#
import sys
sys.path.append('..')
sys.path.append('../..')
import string
import re
import ConfigParser
import nltk.stem.snowball as nltk
from refSectionLib import RefSectionRemover
#-----------------------------------
cp = ConfigParser.ConfigParser()
cp.optionxform = str # make keys case sensitive
cp.read(["config.cfg","../config.cfg","../../config.cfg","../../../config.cfg"])

FIELDSEP  = eval( cp.get("DEFAULT", "FIELDSEP") )

# As is the sklearn convention we use
#  y_true to be the index of the known class of a sample (from training set)
#  y_pred is the index of the predicted class of a sample/record
# CLASS_NAMES maps indexes to class names. CLASS_NAME[0] is 0th class name,etc.
CLASS_NAMES      = eval( cp.get("DEFAULT", "CLASS_NAMES") )
#-----------------------------------

class SampleRecord (object):
    """
    Represents a training sample or a sample to predict.
    A training sample has a known class that it belongs to,
    A sample to predict may or may not have a known class (sometimes we
	do predictions on samples for which we know what class they belong to)
    Knows how to take a text representation of a record (typically a
	text string with delimitted fields) and parse into its fields
    Provides various methods to preprocess a sample record (if any)
    Knows how to format a record output line for various types of prediction
	reports (when passed a predicted value for this sample).

    A SampleRecord can be marked as "reject". Has rejectReason, ...
    """
    def __init__(self, s,):

	self.rejected  = False
	self.rejectReason = None
	self.parseInput(s)
    #----------------------

    def parseInput(self, s):
	fields = s.split(FIELDSEP)

	if len(fields) == 6:	# have known class name as 1st field
	    self.knownClassName = fields[0]
	    fields = fields[1:]
	else:
	    self.knownClassName = None

	self.ID        = str(fields[0])
	self.isDiscard = str(fields[1])
	self.status    = fields[2]
	self.journal   = fields[3]
	self.doc       = self.constructDoc(fields[4])
    #----------------------

    def constructDoc(self, text):
	# Do what needs to be done to construct the text portion
	return text
    #----------------------

    def getSampleAsText(self):
	# return this record as a text string

	if self.rejected: return None

	if self.knownClassName:
	    fields = [self.knownClassName]
	else:
	    fields = []
	fields += [ self.ID,
		    self.isDiscard,
		    self.status,
		    self.journal,
		    self.doc,
		    ]
	return FIELDSEP.join( fields)
    #----------------------

    def getSampleName(self):
	return self.ID

    def getDiscard(self):
	return self.isDiscard

    def getStatus(self):
	return self.status

    def getJournal(self):
	return self.journal

    def getDocument(self):
	return self.doc

    def getKnownClassName(self):
	return self.knownClassName

    def setReject(self, trueOrFalse):
	self.rejected = trueOrFalse

    def isReject(self):
	return self.rejected

    def getRejectReason(self):
	return self.rejectReason

    #----------------------
    # "Preprocessor" functions.
    #  Each should modify this sample and return itself
    #----------------------
    refRemover = RefSectionRemover(maxFraction=0.4) # finds ref sections

    def removeRefSection(self):
	self.doc = SampleRecord.refRemover.getBody(self.doc)
	return self

    miceRegex = re.compile( r'\bmice\b', flags=re.IGNORECASE)

    def rejectIfNoMice(self):
	if not SampleRecord.miceRegex.search(self.doc):
	    self.rejected = True
	    self.rejectReason = "Mice not found"
	return self

    def truncateText(self):
	# so you can see a sample record easily
	self.doc = self.doc[:25]
	return self

    urls_re = re.compile(r'\bhttps?://\S*',re.IGNORECASE) # match URLs
    token_re = re.compile(r'\b([a-z_]\w+)\b')	# match lower case words
    stemmer = nltk.EnglishStemmer()

    def removeURLsCleanStem(self):
	'''
	remove URLs and punct, lower case everything,
	convert '-/-',
	keep tokens that start w/ letter or _ and are 2 or more chars.
	stem
	'''
	output = ''

	for s in SampleRecord.urls_re.split(self.doc): # split and remove URLs
	    s.replace('-/-', 'mut_mut')
	    s.lower()
	    for m in SampleRecord.token_re.finditer(s):
		output += " " + SampleRecord.stemmer.stem(m.group())
	self.doc = output
	return self
    # ---------------------------

    def removeURLs(self):
	'''
	remove URLs, lower case everything
	convert '-/-',
	'''
	output = ''

	for s in SampleRecord.urls_re.split(self.doc):
	    s.replace('-/-', 'mut_mut')
	    output += ' ' + s.lower()
	self.doc = output
	return self

    #----------------------
    # formatting prediction reports, Regular (short) and Long
    #----------------------
    def getPredOutputHeader(self, hasConfidence=False):
	# return formatted header line for prediction report
	cols = [ "ID" ]
	if self.knownClassName != None: cols.append("True Class")
	cols.append("Pred Class")
	if self.hasConfidence:
	    cols.append("Confidence")
	    cols.append("Abs Value")
	return '\t'.join(cols) + '\n'

    def getPredOutput(self, y_pred, confidence=None):
	# return formatted line for the prediction report for this sample
	# y_pred is the predicted class index, not the class name
	cols = [ self.ID ]
	if self.knownClassName != None:  cols.append(self.knownClassName)
	cols.append(CLASS_NAMES[y_pred])
	if confidence != None:
	    cols.append("%6.3f" % confidence)
	    cols.append("%6.3f" % abs(confidence))
	return '\t'.join(cols) + '\n'

    def getPredLongOutputHeader(self, hasConfidence=False):
	# return formatted header line for Long prediction report
	cols = [ "ID" ]
	if self.knownClassName != None: cols.append("True Class")
	cols.append("Pred Class")
	if hasConfidence:
	    cols.append("Confidence")
	    cols.append("Abs Value")
	cols.append("isDiscard")
	cols.append("status")
	cols.append("journal")
	cols.append("Processed text")
	return '\t'.join(cols) + '\n'

    def getPredLongOutput(self, y_pred, confidence=None):
	# return formatted line for the Long prediction report for this sample
	# include confidence value if not None
	cols = [ self.ID ]
	if self.knownClassName != None:  cols.append(self.knownClassName)
	cols.append(CLASS_NAMES[y_pred])
	if self.confidence != None:
	    cols.append("%6.3f" % confidence)
	    cols.append("%6.3f" % abs(confidence))
	cols.append(self.isDiscard)
	cols.append(self.status)
	cols.append(str(self.journal))
	cols.append(str(self.doc))
	return '\t'.join(cols) + '\n'

# end class SampleRecord ------------------------

if __name__ == "__main__":
    r = SampleRecord(\
    'yes|pmID1|noDiscard|Indexed|my Journal|text text text text text Reference r1\n'
    )
    print r.getKnownClassName()
    print r.getSampleName()
    print r.getJournal()
    print r.isReject()
    print r.getDocument()
    print r.getSampleAsText(),
    r.removeRefSection()
    print r.getDocument()
    r.rejectIfNoMice()
    print r.isReject()
    print r.getRejectReason()
