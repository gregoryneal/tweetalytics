"""
This script runs the application using a development server.
"""

import bottle
import os
import sys
import tweepy
import json
import string
import emoji
import psycopg2
import logging
import threading

# routes contains the HTTP handlers for our server and must be imported.
import routes
import db_utils
import re
import tweet_utils
import textblob
import pickle

from collections import defaultdict
from pprint import pprint
from tweepy import TweepError
from datetime import datetime
from collections import Counter

if '--debug' in sys.argv[1:] or 'SERVER_DEBUG' in os.environ:
    # Debug mode will enable more verbose output in the console window.
    # It must be set at the beginning of the script.
    bottle.debug(True)

def rollingAverage(newDataPoint, oldAvg, oldN):
    '''
        Calculates the rolling average of a series using the following formula:
        (newDataPoint + (oldN + oldAvg)) / (oldN + 1)
    '''
    return (newDataPoint + (oldN * oldAvg)) / (oldN + 1)

def get_user(user_input, input_type='@'):
    '''Given input from the user form, get the user object from the twitter api'''
    if input_type == '@':
        name = user_input.strip()
    else:
        name = user_input
    
    try:
        user = TAPI.get_user(name)
        return user
    except TweepError as e:
        print(str(e))
        raise

def handler(obj):
    ''' Extracts the iso format for datetime objects so they can be encoded by the JSON parser.
        Holy shit I sound like a real programmer now fml
    '''
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    raise TypeError

def get_parsed_tweet_data(id, since_id=-1):
    ''' Uses the Tweepy api to get as many tweets as possible from the user denoted by id (more recent than since_id if specified).
        Strips the tweet data into a smaller dictionary form.
        
        Processes up to 200 tweets at a time, up to a maximum of 3200
    '''
    print("Downloading timeline tweets from the Twitter API for user: " + str(id))
    print()
    word_frequency = Counter()
    hashtag_frequency = Counter()
    mentioned_user_frequency = Counter()
    sentiment_timeline = dict() #a day by day sentiment measurement
    tweet_times = []
    rnn = dict() #a nn trained to reproduce this motherfucker's speech patterns after enough training data
    last_tweet_id = 0 #the larger this is, the later it was posted

    def getRange(arr):
        return list(range(arr[0], arr[1]+1))

    def processTweet(tweet):
        nonlocal last_tweet_id  

        #tweet = (cleaned_text, urls, hashtags, mentions, symbols)
        data = tweet_utils.get_all_tweet_data(tweet)
        word_frequency.update(data[0].split())
        hashtag_frequency.update(data[2])
        mentioned_user_frequency.update(data[3])

        d = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S %z %Y')
        tweet_times.append(d)
        #build sentiment timeline
        #take the average sentiment of each tweet throughout the day
        st = textblob.TextBlob(data[0])
        sdata = [st.polarity, st.subjectivity, d]
        update_sentiment_timeline_datapoint(sdata, sentiment_timeline)

        if tweet['id'] > last_tweet_id:
            last_tweet_id = tweet['id']

    def processPage(page):
        print("Processing page: " + str(len(page)) + " tweets!")

        for status in page:
            j = status._json
            try:                
                processTweet(j)
            except TweepError as e:
                print("Error:")
                logging.exception(e)
                print("status:")
                pprint(status._json)
            except AttributeError as e:
                logging.exception("Attribute error: ")
            except Exception as e:
                logging.exception("Some other error")
                print(e)
            finally:
                pass
                #raise StopIteration

    def preparedData():
        #print("word freq: " + str(word_frequency))
        #print("hashtag freq: " + str(hashtag_frequency))
        #print("mention freq: " + str(mentioned_user_frequency))
        #print("tweet times: " + str(tweet_times))
        #print("latest tweet id: " + str(last_tweet_id))
        a = len(tweet_times)
        print("downloaded " + str(a) + " tweets.")

        if a == 0:
            r = {
                "latest_tweet_id": -1,
                "word_frequency": {},
                "hashtag_frequency": {},
                "mentioned_user_frequency": {},
                "tweet_times": [],
                "sentiment_timeline":{}
            }
        else:
            r = {
                "latest_tweet_id": last_tweet_id,
                "word_frequency": word_frequency,
                "hashtag_frequency": hashtag_frequency,
                "mentioned_user_frequency": mentioned_user_frequency,
                "tweet_times": tweet_times,
                "sentiment_timeline": sentiment_timeline
            }
        return r

    if since_id != -1:
        print("Since_id is " + str(since_id))
        try:
            for page in tweepy.Cursor(TAPI.user_timeline, id=id, since_id=since_id, count=200).pages(16):
                processPage(page)
        except TweepError as e:
            print(e)
    else:
        print("Since_id is -1.")
        try:
            for page in tweepy.Cursor(TAPI.user_timeline, id=id, count=200).pages(16):
                processPage(page)
        except TweepError as e:
            print(e)

    return preparedData()

def update_sentiment_timeline_dict(newSentimentDict, timelineToUpdate):
    ''' Update a sentiment timeline using another sentiment timeline '''
    for date, sentiments in newSentimentDict.items():
        avgP = sentiments[0] / sentiments[2]
        avgS = sentiments[1] / sentiments[2]
        for i in range(sentiments[2]):
            update_sentiment_timeline_datapoint([avgP, avgS, date], timelineToUpdate)

def update_sentiment_timeline_datapoint(newData, timelineToUpdate):
    ''' Updates a sentiment timeline with newData = [newPolarity, newSubjectivity, datetime.datetime] '''
    newPol = newData[0]
    newSub = newData[1]

    #if they are both zero, assume there wasn't any text or it was bad data
    #if newPol == 0 and newSub == 0:
    #    return

    d = newData[2]
    if isinstance(d, datetime):
        d = d.isoformat(' ').split()[0] # split the YYYY-MM-DDTHH:MM:SS into YYYY-MM-DD to give day granularity

    if d in timelineToUpdate:
        n = timelineToUpdate[d][2]
        #print("updating index to " + str(n + 1))
        pol = timelineToUpdate[d][0]
        sen = timelineToUpdate[d][1]

        timelineToUpdate[d] = [rollingAverage(newPol, pol, n), rollingAverage(newSub, pol, n), n + 1]
    else:
        xvv = [newPol, newSub, 1]
        #print(xvv)
        timelineToUpdate[d] = xvv

def rreplace(s, old, new, occurrence=1):
    ''' Replaces all occurrances of old with new in string s, limited by the occurrence parameter. 
        The replacement goes from right to left.
    '''
    li = s.rsplit(old, occurrence)
    return new.join(li)

def wsgi_app():
    """Returns the application to make available through wfastcgi. This is used
    when the site is published to Microsoft Azure."""
    return bottle.default_app()

def clearRateLimit(ratelimits, timer_seconds=60.0):
    '''
    Repeatedly clears the rate limit array
    '''
    t = threading.Timer(timer_seconds, clearRateLimit, [ratelimits, timer_seconds])
    t.daemon = True #daemon processes are killed when their creating process is killed
    t.start()

    print("Clearing rate limit cache: " + ','.join(ratelimits))
    ratelimits.clear()

if __name__ == '__main__':
    global AUTH
    global TAPI
    global DB
    global ratelimits

    ratelimits = []
    #1 request per minute, clear the ratelimits list every 1 minute
    clearRateLimit(ratelimits)

    #app meta-data
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
    STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static').replace('\\', '/')
    HOST = os.environ.get('SERVER_HOST', 'localhost')

    #set up the database
    DB = db_utils.DBContext()

    #create api auth references
    consumerkey = os.environ['tweetalytics_consumer_key']
    consumersecret = os.environ['tweetalytics_consumer_secret']
    print(consumerkey)
    print(consumersecret)
    print()

    AUTH = tweepy.AppAuthHandler(consumerkey, consumersecret)
    TAPI = tweepy.API(AUTH, wait_on_rate_limit=True)

    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555

    @bottle.route('/static/<filepath:path>')
    def server_static(filepath):
        """Handler for static files, used with the development server.
        When running under a production server such as IIS or Apache,
        the server should be configured to serve the static files."""
        return bottle.static_file(filepath, root=STATIC_ROOT)    

    #this is here to prevent having to import get_user() from app
    #which would cause a circular reference collision between routes and app.
    #call from ajax, returns json data
    @bottle.post('/stats')
    def stats():
        ''' Consolidate database data with new tweet data to present updated stats to the user. '''

        result = {
                    "result":"FAIL",
                    "message":"figure out how to write more descriptive error messages, asshole."
                 }

        ip = bottle.request.environ.get('HTTP_X_FORWARDED_FOR') or bottle.request.remote_addr
        print("Connection attempt: " + ip)

        if ip in ratelimits:
            result['message'] = 'request limit'
            print("Connection rejected: " + ip)
            return json.dumps(result)

        ratelimits.append(ip)

        user = bottle.request.forms.get('id-input')
        pprint(vars(bottle.request.forms))        

        try:
            #get user id, any database info, then any new tweet data, if everything is successful and there is new data, it is pushed back to the database.
            user_c = get_user(user)
            id = user_c.id_str

            print(str(user_c.screen_name))
            print(str(id))

            since_id = -1 #the most recent since_id, pulled from the database and the web api

            consolidated_stats = {
                "stats": {
                    "twitter_id": id,
                    "word_frequency": Counter(),
                    "hashtag_frequency": Counter(),
                    "mentioned_user_frequency": Counter(),
                    "tweet_times": [],
                    "sentiment_timeline": dict()
                },
                "metadata": {
                        "profile_url": rreplace(user_c.profile_image_url_https, '_normal', ''), #get the hidef version by removing the _normal at the end
                        "profile_banner": rreplace(user_c.profile_banner_url, '_normal', ''),
                        "statuses_count": user_c.statuses_count,
                        "screen_name": user_c.screen_name,
                        "bg_color": user_c.profile_background_color
                }
            }

            rnn = {}
            db_user_data = DB.getuserdata(id)
            # 0     1           2               3               4                           5                   6           7                   8              9
            #(id, twitter_id, latest_tweet_id, word_frequency, mentioned_user_frequency, hashtag_frequency, tweet_times, sentiment_timeline, emoji_frequency, rnn)
            if db_user_data != False:
                print("User exists in database!")
                print(db_user_data[0])

                consolidated_stats['stats']['word_frequency'].update(db_user_data[3])
                consolidated_stats['stats']['hashtag_frequency'].update(db_user_data[5])
                consolidated_stats['stats']['mentioned_user_frequency'].update(db_user_data[4])
                consolidated_stats['stats']['tweet_times'].extend(db_user_data[6])

                update_sentiment_timeline_dict(db_user_data[7], consolidated_stats['stats']['sentiment_timeline'])
                since_id = db_user_data[2] # passed to the twitter api for downloading tweets

                #if db_user_data[9]:
                ##rnn is a dict with non string keys so we gotta pickle it and store it as a byte array instead
                #    rnn = pickle.loads(db_user_data[9])
                #else:
                #    print("no usable rnn data")

                print("(database)New since_id: " + str(since_id))
            else:
                print("No user found in database")
            
            #if rnn == {}:
            #    pass

            new_user_data = get_parsed_tweet_data(user_c.id, since_id=since_id) #new tweet data
            
            if new_user_data['latest_tweet_id'] != -1:
                print("Found new tweets on their timeline!")
                wf = new_user_data['word_frequency']
                hf = new_user_data['hashtag_frequency']
                mf = new_user_data['mentioned_user_frequency']
                tt = new_user_data['tweet_times']

                update_sentiment_timeline_dict(new_user_data['sentiment_timeline'], consolidated_stats['stats']['sentiment_timeline'])

                print("Consolidating tweets!")
                consolidated_stats['stats']['word_frequency'].update(wf)
                consolidated_stats['stats']['hashtag_frequency'].update(hf)
                consolidated_stats['stats']['mentioned_user_frequency'].update(mf)
                consolidated_stats['stats']['tweet_times'].extend(tt)                
                since_id = max(new_user_data['latest_tweet_id'], since_id)
                print("(tweepy)New since_id: " + str(since_id))
            else:
                print("No tweets online!")

            consolidated_stats['stats']['latest_tweet_id'] = since_id

            #create a copy to update the database with
            try:
                zzz = dict(consolidated_stats['stats'])
                zzz['word_frequency'] = json.dumps(zzz['word_frequency'])
                zzz['hashtag_frequency'] = json.dumps(zzz['hashtag_frequency'])
                zzz['mentioned_user_frequency'] = json.dumps(zzz['mentioned_user_frequency'])
                zzz['sentiment_timeline'] = json.dumps(zzz['sentiment_timeline'])
                #zzz['rnn'] = pickle.dumps(rnn)
                DB.upsertuserdata(zzz)
            except Exception as e:
                print("Exception entering user data:" + str(e))

            #transform the counters from a dic{str:int} to a list[[str,int]] in descending order
            consolidated_stats['stats']['word_frequency'] = [list(a) for a in consolidated_stats['stats']['word_frequency'].most_common()]
            consolidated_stats['stats']['hashtag_frequency'] = [list(a) for a in consolidated_stats['stats']['hashtag_frequency'].most_common()]
            consolidated_stats['stats']['mentioned_user_frequency'] = [list(a) for a in consolidated_stats['stats']['mentioned_user_frequency'].most_common()]
            consolidated_stats['stats']['sentiment_timeline'] = [list(a) for a in consolidated_stats['stats']['sentiment_timeline'].items()]

            print(consolidated_stats['stats']['sentiment_timeline'][0:2])
            
            #print(consolidated_stats['tweet_times'])
            result = consolidated_stats

        except TweepError as ex:
            result['type'] = type(ex).__name__
            result['message'] = str(ex)
        except psycopg2.Error as ex:
            result['type'] = type(ex).__name__
            result['message'] = str(ex)
        except Exception as ext:
            result['type'] = type(ex).__name__
            result['message'] = str(ex)
        finally:
            return json.dumps(result, default=handler)

    # Starts a local test server.
    try:
        bottle.run(server='wsgiref', host=HOST, port=PORT)
    except (bottle.BottleException, psycopg2.Error):
        pass
    finally:
        DB.close()
