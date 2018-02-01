import sys, ConfigParser
cp = ConfigParser.ConfigParser()
cp.read([ d+'/config.cfg' for d in ['.', '..', '../..', '../../..'] ])
TOOLSDIR = cp.get('DEFAULT', 'MLTEXTTOOLSDIR')
sys.path = [ sys.path[0], '..', '../..', '../../..', TOOLSDIR ] + sys.path[1:]
import textTuningLib as tl
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.preprocessing import StandardScaler, MaxAbsScaler
from sklearn.linear_model import SGDClassifier
#-----------------------
args = tl.parseCmdLine()
randomSeeds = tl.getRandomSeeds( { 	# None means generate a random seed
		'randForSplit'      : args.randForSplit,
		'randForClassifier' : args.randForClassifier,
		} )
pipeline = Pipeline( [
#('vectorizer', CountVectorizer(
('vectorizer', TfidfVectorizer(
		strip_accents=None,	# done in preprocessing
		decode_error='strict',	# should have been handled in preproc
		lowercase=False,	# done in preprocessing
		stop_words='english',
		# token_pattern=r'\b([a-z_]\w+)\b', # use default for now
		),),
#('scaler'    ,StandardScaler(copy=True,with_mean=False,with_std=True)),
('scaler'    , MaxAbsScaler(copy=True)),
('classifier', SGDClassifier(verbose=0, class_weight='balanced',
		random_state=randomSeeds['randForClassifier']) ),
] )
parameters={'vectorizer__ngram_range':[(1,2)],
	'vectorizer__min_df':[0.1],
	'vectorizer__max_df':[.8],
	'classifier__alpha':[1],
	'classifier__learning_rate':['invscaling'],
	'classifier__eta0':[ .01],
	'classifier__loss':[ 'hinge' ],
	'classifier__penalty':['l2'],
	}
p = tl.TextPipelineTuningHelper( pipeline, parameters, beta=4, cv=5,
			randomSeeds=randomSeeds,).fit()
print p.getReports()
