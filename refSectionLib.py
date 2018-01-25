#!/usr/bin/env python2.7

import string
import re

refKeyTerms = [ "References",
		"Reference",
		"Literature Cited",
		"Acknowledgements",
		"Acknowledgments",
		"Conflicts of Interest",
		"Conflict of Interest",
		]

class RefSectionRemover (object):
    '''
    Class to predict/remove Reference sections from (extracted) text strings
    '''

    def __init__(self,
		 keyTerms=refKeyTerms,	# terms that can begin a ref section
		 maxFraction=0.4	# max fraction of whole doc that the
		 			#  ref section is allowed to be
		):
	self.keyTerms = keyTerms
	self.maxFraction = maxFraction
	self.regexString = self.buildRegex()
	self.refRegex = re.compile(self.regexString)
    # -----------------------

    def removeRefSection(self, text):

	kw, refStart = self.predictRefSection(text)
	return text[:refStart]

    def getBody(self, text): return self.removeRefSection(text)
    # ----------------------------------

    def getRefSection(self, text):

	kw, refStart = self.predictRefSection(text)
	return text[refStart:]
    # ----------------------------------

    def predictRefSection(self, text):
	# predict ref section.
	# Return the key term matched and the position of the predicted
	#  refs section in text.

	textLength = len(text)
	matches = [ x for x in self.refRegex.finditer(text)]

	if len(matches) == 0:
	    lastKeyWord = "No match"
	    refStart = textLength
	else:
	    m = matches[-1]
	    lastKeyWord = m.group(0)	# last matched term
	    refStart = m.start(0)	# position at end of that term
	    refLength = textLength - refStart

	    if float(refLength)/textLength > self.maxFraction:
		lastKeyWord = "Ref Prediction > %4.2f" % self.maxFraction
		refStart = textLength

	return lastKeyWord, refStart
    # ----------------------------------

    def buildRegex(self):
	# for given list of words, return regex pattern string that matches
	# \b(word1|word2|word3)\b - with each word "almostCaseInsensitive"

	regexStr = r'\b('
	insensitive = map(almostCaseInsensitiveRegex, self.keyTerms)
	regexStr += '|'.join(insensitive)
	regexStr += r')\b'
	return regexStr
    # ----------------------------------

#------------------ end Class RefSectionRemover

def almostCaseInsensitiveRegex(s):
    # for given string, return regex pattern string that matches the 1st
    #  char and then all subsequent chars in either case
    reg = s[0]
    for c in s[1:]:
	if c.isalpha():
	    reg += '[%s%s]' % (c.upper(), c.lower())
	else:
	    reg += '[%s]' % c
    return reg
# -----------------------

if __name__ == "__main__":
    rm = RefSectionRemover(maxFraction=0.5, keyTerms=['Refs'])
    shortDoc = "this is the body ........... REFS literature section"
    print "doc: %s" % shortDoc
    print "body: %s" % rm.getBody(shortDoc)
    print "refs: %s" % rm.getRefSection(shortDoc)
