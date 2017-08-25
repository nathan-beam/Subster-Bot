import praw
import json

with open('subster.json') as settings_file:    
    settings = json.load(settings_file)

reddit = praw.Reddit(client_id=settings["client_id"],
                     client_secret=settings["secret"],
                     password=settings["password"],
                     user_agent='Script by /u/morpen',
                     username=settings["username"])
					 
print(reddit.user.me())
