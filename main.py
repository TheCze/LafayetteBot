'''
Created on 27.05.2018

@author: Cze
'''
import tweepy
import secrets
import re
from tweepy.error import TweepError
import time
import pickle
import os
from setuptools.sandbox import save_argv

lafayetteLines = ["I’m takin this horse by the reins makin’ Redcoats redder with bloodstains",
       "And I’m never gonna stop until I make ‘em Drop and burn ‘em up and scatter their remains, I’m",
       "Watch me engagin’ em! Escapin’ em! Enragin’ em! I’m—",
       "I go to France for more funds",
       "I come back with more Guns - And ships - And so the balance shifts",
       "Sir, he knows what to do in a trench Ingenuitive and fluent in French, I mean—",
       "Sir, you’re gonna have to use him eventually What’s he gonna do on the bench? I mean—",
       "No one has more resilience Or matches my practical tactical brilliance—",
       "You wanna fight for your land back?"]

lafayettemiddle = "We can end this war in Yorktown, cut them off at sea but \nFor this to succeed there is someone else we need!"
lafayettefinale = "Ah! Get ya right hand man back \nYou know you gotta get ya right hand man back\n\
I mean you gotta put some thought into the letter \nbut the sooner the better To get your right hand man back!"
washingtonlines = ["We rendezvous with Rochambeau, consolidate their gifts",
                   "I know",
                   "I need my right hand man back!",
                   "Alexander Hamilton \nTroops are waiting in the field for you \nIf you join us right now, \ntogether we can turn the tide",
                   "Oh, Alexander Hamilton \nI have soldiers that will yield for you \nIf we manage to get this right \n\
They’ll surrender by early light \nThe world will never be the same, Alexander…"]
users = {}
apis = {}
lafayetteusername = "@BotLafayette"
washingtonfollowmsg = "You've got Washington on your side!"
lafayettefollowmsg = "Oui oui, mon ami"

#Initiate all three twitter bots (the third bot is just for testing features)
lauth = tweepy.OAuthHandler(secrets.lafayette_consumer_token, secrets.lafayette_consumer_secret)
lauth.set_access_token(secrets.lafayette_access_token, secrets.lafayette_access_secret)
lafayetteAPI = tweepy.API(lauth)

wauth = tweepy.OAuthHandler(secrets.washington_consumer_token, secrets.washington_consumer_secret)
wauth.set_access_token(secrets.washington_access_token, secrets.washington_access_secret)
washingtonAPI = tweepy.API(wauth)

halauth = tweepy.OAuthHandler(secrets.hal_consumer_token, secrets.hal_consumer_secret)
halauth.set_access_token(secrets.hal_access_token, secrets.hal_access_secret)
halAPI = tweepy.API(halauth)

apis = {lafayetteAPI: 'Lafayette', washingtonAPI: 'Washington', halAPI: 'HAL'}

timeOfLastFollowCheck=0
timeBetweenFollowChecks=3000

def answer(status, saidHamilton):
    """selects which answer to tweet to a user, afterwards saves users{}
    """
    user = status.user.screen_name
    if user not in users:
        users[user] = 0
    if(users[user] <= 4 and not saidHamilton)or(users[user] >= 5 and saidHamilton):
        messageMe("Replying to {} for the {} time, Original tweetReply: {}".format(user, users[user], status.text))
        if(users[user] < 9):
            statustext = lafayetteLines[users[user]]
            tweetReply(lafayetteAPI, statustext, status)
        else:
            doFinale(status)
        if users[user] == 4:
            doMiddle(status)
        if users[user] == 9:
            doFinale(status)
        if(users[user]>=9):
            users[user]=0
        else:
            users[user] = users[user] + 1

    else:
        print("User {} did not match criteria, listindex {}, saidHamilton: {}".format(user, users[user], saidHamilton))

    saveUsers()
        
def doMiddle(reply):
    """Tweets the bridge part of the song
    """
    tweetReply(washingtonAPI, washingtonlines[0], reply)
    tweetReply(lafayetteAPI, lafayettemiddle, reply)
    tweetReply(washingtonAPI, washingtonlines[1], reply)


def doFinale(reply):
    """Tweets the finale
    """
    tweetReply(washingtonAPI, washingtonlines[2], reply)
    tweetReply(lafayetteAPI, lafayettefinale, reply)
    tweetReply(washingtonAPI, washingtonlines[3], reply)
    tweetReply(washingtonAPI, washingtonlines[4], reply)


def tweetReply(thisAPI, statustext, reply):
    """Tweets the statustext to the user who send 'reply' in reply format
    """
    statustext = "@{} ".format(reply.user.screen_name) + statustext
    try:
        thisAPI.update_status(statustext, in_reply_to_status_id=reply.id, auto_populate_reply_metadata=True)
        print("Tweeted reply to {}, message: {}".format(reply.user.screen_name, statustext))
    except tweepy.TweepError as err:
        errormessage = "{} Encountered a TweepError while replying: {}".format(apis[thisAPI], err.response.text)
        if re.search(r"187", errormessage):
            tryToDeleteDuplicate(statustext, thisAPI)
            try:
                thisAPI.update_status(statustext, in_reply_to_status_id=reply.id, auto_populate_reply_metadata=True)
            except tweepy.TweepError as err:
                errormessage = "{} Encountered a TweepError on second tweetReply try: {}".format(apis[thisAPI], err.response.text)
                messageMe(errormessage)
        else:
            messageMe(errormessage)


def tweet(thisAPI, statustext, user):
    """Tweets the statustext to the "user"
    """
    statustext = "@{} ".format(user) + statustext
    try:
        thisAPI.update_status(statustext)
        print("Tweeted to {}, message: {}".format(user, statustext))
    except tweepy.TweepError as err:
        errormessage = "{} Encountered a TweepError while replying: {}".format(apis[thisAPI], err.response.text)
        if re.search(r"187", errormessage):
            tryToDeleteDuplicate(statustext, thisAPI)
            try:
                thisAPI.update_status(statustext)
            except tweepy.TweepError as err:
                errormessage = "{} Encountered a TweepError on second tweetReply try: {}".format(apis[thisAPI], err.response.text)
                messageMe(errormessage)
        else:
            messageMe(errormessage)


def checkTweet(status):
    """Checks if a Tweet should be responded to, afterwards checks if it's time to check the followers
    """
    global timeOfLastFollowCheck
    global timeBetweenFollowChecks
    user = status.user.screen_name
    if re.search(r"Lafayette!+$", status.text, re.IGNORECASE):
        print("WINNER FROM {},saidHamilton False, TWEET: {}".format(user, status.text))
        answer(status, False)
    elif re.search(r"Hamilton!+$", status.text, re.IGNORECASE):
        print("WINNER FROM {},saidHamilton True, TWEET: {}".format(user, status.text))
        answer(status, True)
    elif re.search(r"@BotLafayette", status.text, re.IGNORECASE):
        messageMe("Message to the bot: {}".format(status.text))
    passedtime=time.time()-timeOfLastFollowCheck
    if passedtime>timeBetweenFollowChecks:
        checkFollowers(lafayetteAPI)
        checkFollowers(washingtonAPI)
        timeOfLastFollowCheck=time.time()


def saveUsers():
    """Locally saves all previously interacted users
    """
    print("Saving users")
    if(os.path.exists("obj")):
        pass
    else:
        os.mkdir("obj")
    with open('obj/'+ "users" + '.pkl', 'wb') as f:
        pickle.dump(users, f, pickle.HIGHEST_PROTOCOL)


def loadUsers():
    """Loads knows users from local file
    """
    print("Loading users")
    try:
        with open('obj/' + "users" + '.pkl', 'rb') as f:
            thisusers= pickle.load(f)
            print("Loaded users, length {}".format(len(users)))
            return thisusers
    except FileNotFoundError:
        thisusers={}
        print("Users did not exist, creating blank users{}")
        return thisusers
        
def messageMe(text):
    """Sends a text message to the bot owner
    """
    print("Sending message: {}".format(text))
    lafayetteAPI.send_direct_message(secrets.botowner, text=text)


def tryToDeleteDuplicate(text, thisAPI):
    """Looks through previous tweets and tries to delete the matching tweet
    """
    idlst = []
    for status in thisAPI.user_timeline():
        if(status.text == text):
            idlst.append(status.id)
    
    if(len(idlst) > 0):
        for tweetid in idlst:
            try:
                thisAPI.destroy_status(tweetid)
                print("Succesfully destroyed Tweet: {}".format(text))     
            except tweepy.TweepError as err:
                errormessage = "{} Encountered a TweepError while destroying tweetID {}, Text: {}: {}".format(apis[thisAPI], tweetid, text, err.response.text)
                messageMe(errormessage)      
    else:
        print("Could not find Tweet: {}".format(text))


def deleteAllTweets(thisAPI):
    """Deletes all tweets in a given users timeline
    """
    print("==DELETING ALL TWEETS FOR USER {}==".format(apis[thisAPI]))
    for status in thisAPI.user_timeline():
        try:
            thisAPI.destroy_status(status.id)
        except tweepy.TweepError as err:
            errormessage = "{} Encountered a TweepError while destroying all Tweets: {}".format(apis[thisAPI], err.response.text)
            messageMe(errormessage)  

           
def checkFollowers(thisAPI):
    """Checks all followers, follows new followers and sends welcome message
    """
    try:
        for follower in thisAPI.followers_ids(lafayetteusername):
            if follower in thisAPI.friends_ids(lafayetteusername):
                print("Ein echter Freund!")
            else:
                user = thisAPI.get_user(follower).screen_name
                text = ""
                thisAPI.create_friendship(follower)
                if(apis[thisAPI] == "Lafayette"):
                    text = lafayettefollowmsg
                else:
                    text = washingtonfollowmsg
                text = "@{} {}".format(user, text)
    except tweepy.TweepError as err:            
            errormessage = "{} Encountered a TweepError while ckecking Followers: {}".format(apis[thisAPI], err.response.text)
            messageMe(errormessage)
            

class BotStreamer(tweepy.StreamListener):
    # Called when a new status arrives which is passed down from the on_data method of the StreamListener
    def on_status(self, status):
        checkTweet(status)
        

messageMe("Booting up Bot! Current Time: {}".format(time.time()))
'''deleteAllTweets(washingtonAPI)
deleteAllTweets(lafayetteAPI)
deleteAllTweets(halAPI)'''
users=loadUsers()
print(users)

myStreamListener = BotStreamer()
stream = tweepy.Stream(lauth, myStreamListener)
stream.filter(track=["hamilton","Lafayette", lafayetteusername])

