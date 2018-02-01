# AutomatedTagging
Using machine learning to automate MGI literature triage tagging for different
curation groups

# General things I've learned

    In sklearn, during vectorizing, stop word removal happens before ngram
    selection (as you'd expect).
    BUT term removal due to min_df or max_df happens AFTER ngram selection.
    (i.e., the ngrams frequencies are analysed and the ngrams are removed)

# Repo organization thoughts...

lit triage text tools repo/product
    refsection removal
    maybe all the automated tagging stuff

Text ML repo
    comparepipelines
    ...

# Abbreviations
refsectR	-- reference section removal
aftOct		-- after Oct 1, 2017, papers entered after this use the new
			lit triage system
suppdata	-- supplemental data
MGIrel		-- MGI relevant = MGI-discard = 0
non-MGIrel	-- MGI-discard = 1

# GXD tagging
Training data:
    what's available:
    AftOct:
	~500	Positive: status = chosen, indexed, or full-coded
	~3500	Negative: status = rejected and MGIrel
	~9000	Negative: non-MGIrel

    1/1/2016 - 10/1/2017
	~1500	Positive: status = chosen, indexed, or full-coded
    (plus lots more from older papers)

    Initial plan:
	* Positive samples
	(511) papers chosen, indexed, or full coded for GXD created aftOct
	    few have supplemental data attached
	(15??) papers chosen, indexed, or full coded for GXD
	    created 1/1/2016 .. 10/1/2017
	    most have suppdata attached

	* Negative samples (few should have suppdata attached)
	(random 1000) MGIrel & Rejected from GXD created aftOct
			(could go before Oct to get some w/ suppdata)
	(random 1000) non-MGIrel created aftOct

	Could try to pick random sets w/ same distribution of papers across
	journals, but won't bother for now. Maybe random sample will come close.

	Could try several training epochs using different random negatives.

	* Article Preprocessing
	Will use refsectR on these.
	Remove papers w/ no "mice" after refsectR?  YES
	(assuming we will do these steps with new papers in the future)
	Should pick the random negative samples AFTER removing the
	    no "mice" papers

	Think about when to apply other preprocessing: 
	    -/-  -->  mut_mut
	    stemming
	    ...

	* Gives a balanced set.
	Have lots of other positive and negative examples to add to training
	    or do additional testing on (lots more negatives after 10/1/2017,
	    more positives before 2016)

	* Concerns
	Some concern over existence of suppdata in the PDF/extracted text as
	    1) most of new papers coming in that we would apply this model
		to will NOT have supp data attached
	    2) it affects how well the refsection removal works

	    BUT will just try this for now and see.
    Jan 18, 2017:
	pulled positive and negative training samples out
	Split into
	    # used getTrainingData.py
		trainY.txt,
		trainNall.txt  
	    # used grep '|0|' and grep '|1|' to split (no)discard
		trainNdiscard.txt
		trainNnodis.txt
	    # used getRandomSubset.py -n 1000 to split discards, nodiscard
		trainNdiscardRandom.txt trainNdiscardLeftov.txt
		trainNnodisRandom.txt   trainNnodisLeftov.txt
	    # used preprocessor.py trainY.txt trainN*Random.txt >
		trainingSet.txt
	    # used preprocessor.py -p removeRefSection -p removeIfNoMice
	    #                     trainingSet.txt > trainingPreproc.txt

		147 skipped for "Mice not found"
		4071 kept

		So this is training set, but no lower(), stemming,
		punctuation removal, tokenizing yet.
    Jan 25:
	Automated all the above steps in buildTrainingSet

Preprocessing thoughts:
  Goals:
    preprocess all docs ahead of time, before vectorizing during tuning,
    so tuning experiments are faster. (same for training during the
    building of the final predictor, i.e., trainModel.py will use the
    same preprocessed samples) 
	- so vectorizer has to do minimal preprocessing work

    able to try different preprocessing ideas via command line params to
    preprocessSamples.py
	- storing differently preprocessed samples/doc files in different
	    locations.

    able to have a standard, default, set of preprocessing steps defined in
    config file
	- predict.py will need to run these steps on new/unseen docs
	- Does predict.py need preprocessor command line options?

    Smarts for how to do preprocessing (options) needs to be encapsulated 
    in sampleDataLib

    Preprocessing needs to support sample rejection and rejection reasons

  Implications

    1) If you want to compare models on diff preprocessing (e.g., stemming vs.
	not), you'd create two different document dirs preprocessed differently.

    2) rejecting a sample means:
	during tuning:		it is omitted from training/test set
	during final training:	it is omitted
	during predict.py:	Should be predicted as a 'no' - or tagged
				special somehow.
	SO preprocessSamples.py, trainModel.py, and predict.py need to detect
	and handle rejects.
	UNLESS preprocessSamples.py always runs first and handles rejects.
	- yes, like that idea
	- preprocessSamples.py should be a module that defines a preprocess()
	    function called by predict??

    5) who is responsible for reading config file and applying default
	preprocessing steps?
	preprocesssSamples.py or sampleDataLib?

