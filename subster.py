import praw
import json
import nltk
import string
from nltk.corpus import stopwords
from nltk.stem.porter import *
from sklearn.feature_extraction.text import TfidfVectorizer
import operator
import sys
import threading

stemmer = PorterStemmer()

subreddits_main_dict = {}
subreddits_large_dict = {}
subreddits_political_dict = {}
subreddits_meta_dict = {}
already_done = []
subreddits_large = []
subreddits_political = []
subreddits_meta = []
reddit = None

def init():
	global subreddits_large
	global subreddits_political
	global subreddits_meta
	global reddit
	with open('subster.json') as settings_file:    
		settings = json.load(settings_file)
		subreddits_large = settings["subreddits_large"]
		subreddits_political = settings["subreddits_political"]
		subreddits_meta = settings["subreddits_meta"]

	reddit = praw.Reddit(client_id=settings["client_id"],
						 client_secret=settings["secret"],
						 password=settings["password"],
						 user_agent='Script by /u/morpen',
						 username=settings["username"])
					 
def prep_subs():
	threads = []

	for sub in subreddits_large:
		t = threading.Thread(target=scrape_subreddit, args=(sub,subreddits_large_dict))
		threads.append(t)
		t.start()

	for sub in subreddits_large[:10]:
		t = threading.Thread(target=scrape_subreddit, args=(sub,subreddits_main_dict))
		threads.append(t)
		t.start()

	for sub in subreddits_political:
		t = threading.Thread(target=scrape_subreddit, args=(sub,subreddits_political_dict))
		threads.append(t)
		t.start()
	for sub in subreddits_meta:
		t = threading.Thread(target=scrape_subreddit, args=(sub,subreddits_meta_dict))
		threads.append(t)
		t.start()

	for thread in threads:
		thread.join();
		
def tokenize(text):
	tokens = nltk.word_tokenize(text)
	stemmed = stem_tokens(tokens, stemmer)
	return stemmed

def stem_tokens(tokens, stemmer):
	stemmed = []
	for item in tokens:
		stemmed.append(stemmer.stem(item))
	return stemmed

def analyze(username,subreddit_dictionary):
	user_comments = get_user_comments(username)
	score_dictionary = {}
	threads = []
	for key, value in subreddit_dictionary.items():
		t = threading.Thread(target=vectorize, args=(score_dictionary,user_comments,value,key))
		threads.append(t)
		t.start()

	for thread in threads:
		thread.join();
		
	return sorted(score_dictionary.items(), key=operator.itemgetter(1),reverse=True)[:10]

def get_user_comments(username):
	comment_string = ""
	for comment in reddit.redditor(username).comments.new(limit=None):
		comment_string += comment.body
	return comment_string
	
def get_reply(username,dictionary,size):
	reply = "Hello /u/"+username+"! I have analysed your vocabulary and compared it to over "+str(size)+" subreddits, and here's how you stack up!  \n\n"
	for key, value in dictionary:
		reply+= key + ": " + str(value)+"  \n"
	reply+="\n\n  ***** \n\n ^I ^am ^a ^bot ^and ^this ^action ^was ^performed ^automatically.  \n\n ^Made ^by ^[morpen](http://www.reddit.com/user/morpen)"
	return reply

def scrape_subreddit(sub,dictionary):
	try:
		comment_string = ""
		for comment in reddit.subreddit(sub).comments(limit=100):
			comment_string += comment.body
		lower = comment_string.lower()
		translator = str.maketrans('', '', string.punctuation)
		no_punc = lower.translate(translator)
		dictionary[sub] = no_punc
		print(sub + " initialized")
	except:
		print(sub + " filed")

def analyze_user(comment,dictionary):
	print("Analyzing: "+comment.author.name)
	scores = analyze(comment.author.name,dictionary)
	reply = get_reply(comment.author.name, scores, len(dictionary))
	comment.reply(reply)
	print("Done")
	already_done.append(comment.id)	

def vectorize(dictionary, user_comments, subreddit_comments, key):
	vectorizer = TfidfVectorizer(tokenizer=tokenize, stop_words='english')
	tfidf = vectorizer.fit_transform([user_comments, subreddit_comments])
	score = ((tfidf * tfidf.T).A)[0,1]
	dictionary[key]=score

sub_name = "all" 
if len(sys.argv) > 1:
	sub_name = sys.argv[1]
init()
print("Initializing...")
prep_subs()	
print("Initialized")
subreddit = reddit.subreddit(sub_name)
print("Listening on /r/"+sub_name)
print()
for comment in subreddit.stream.comments():
	if("!subster" in comment.body):
		if(comment.id not in already_done):
			if("!p" in comment.body):
				print("political requested")
				dictionary = subreddits_political_dict
			elif("!m" in comment.body):
				print("meta requested")
				dictionary = subreddits_meta_dict
			elif("!l") in comment.body:
				print("large requested")
				dictionary = subreddits_large_dict
			else:
				dictionary = subreddits_main_dict
			try:
				t = threading.Thread(target=analyze_user,args=(comment,dictionary))
				t.start()
			except:
				print("Whoops: " + sys.exc_info()[0])