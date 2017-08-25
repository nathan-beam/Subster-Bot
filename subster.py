import praw
import json
import nltk
import string
from nltk.corpus import stopwords
from nltk.stem.porter import *
from sklearn.feature_extraction.text import TfidfVectorizer
import operator

stemmer = PorterStemmer()

subreddit_dict = {}
already_done = []
subreddits = []
reddit = None
vectorizer = None

def init():
	global subreddits
	global reddit
	global vectorizer
	with open('subster.json') as settings_file:    
		settings = json.load(settings_file)
		subreddits = settings["subreddits"]
	vectorizer = TfidfVectorizer(tokenizer=tokenize, stop_words='english')
	reddit = praw.Reddit(client_id=settings["client_id"],
						 client_secret=settings["secret"],
						 password=settings["password"],
						 user_agent='Script by /u/morpen',
						 username=settings["username"])
					 
def prep_subs():
	global subreddit_dict
	for sub in subreddits:
		print(sub)
		comment_string = ""
		for comment in reddit.subreddit(sub).comments(limit=100):
			comment_string += comment.body
		lower = comment_string.lower()
		translator = str.maketrans('', '', string.punctuation)
		no_punc = lower.translate(translator)
		subreddit_dict[sub] = no_punc
		
def tokenize(text):
	tokens = nltk.word_tokenize(text)
	stemmed = stem_tokens(tokens, stemmer)
	return stemmed

def stem_tokens(tokens, stemmer):
	stemmed = []
	for item in tokens:
		stemmed.append(stemmer.stem(item))
	return stemmed

def analyze(username):
	user_comments = get_user_comments(username)
	dictionary = {}
	for key, value in subreddit_dict.items():
		tfidf = vectorizer.fit_transform([user_comments, value])
		score = ((tfidf * tfidf.T).A)[0,1]
		dictionary[key]=score
	return sorted(dictionary.items(), key=operator.itemgetter(1),reverse=True)[:10]

def get_user_comments(username):
	comment_string = ""
	for comment in reddit.redditor(username).comments.new(limit=None):
		comment_string += comment.body
	return comment_string
	
def get_reply(dictionary):
	reply = "Hello! I have analysed your comments, and here's how you stack up!  \n\n"
	for key, value in dictionary:
		reply+= key + ": " + str(value)+"  \n"
	reply+="\n\n  ***** \n\n ^I ^am ^a ^bot ^and ^this ^action ^was ^performed ^automatically.  \n\n ^Made ^by ^/u/morpen"
	return reply
	
init()
print("Initializing...")
prep_subs()
print("Initialized")
subreddit = reddit.subreddit("all")
for comment in subreddit.stream.comments():
	if("!subster" in comment.body):
		if(comment.id not in already_done):
			try:
				print("Analyzing: "+comment.author.name)
				dictionary = analyze(comment.author.name)
				reply = get_reply(dictionary)
				comment.reply(reply)
				print("Done")
				already_done.append(comment.id)
			except:
				print("Whoops: " + comment.id)