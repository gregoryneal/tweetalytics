from datetime import datetime
import string
import urllib

#Gets the tweet time.
def get_time(tweet):
    return datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S %z %Y')

#Gets all hashtags.
def get_hashtags(tweet):
    return [tag['text'] for tag in tweet['entities']['hashtags']]

#Gets the screen names of any user mentions.
def get_user_mentions(tweet):
    return [m['screen_name'] for m in tweet['entities']['user_mentions']]

#Gets the unwound media links
def get_media(tweet):
    if 'media' in tweet['entities']:
        r = []
        for media in tweet['entities']['media']:
            resp = urllib.urlopen(media['expanded_url'])
            if resp.getcode() == 200:
                r.append(resp.url)
        return r

    return []

#Gets the unwound urls
def get_urls(tweet):
    if 'urls' in tweet['entities']:
        r = []
        for url in tweet['entities']['urls']:
            resp = urllib.urlopen(url['expanded_url'])
            if resp.getcode() == 200:
                r.append(resp.url)
        return r
    return []

def unwound(url):
    resp = urllib.request.urlopen(url)
    if resp.getcode() == 200:
        return resp.url
    return url

#Gets the text, sans links, hashtags, mentions, media, and symbols.
#returns a tuple of (clean_text, unwound links, hashtags, mentions, symbols)
def get_text_cleaned(tweet):
    '''Gets the text, sans links, hashtags, mentions, media, and symbols.
       returns a list of [clean_text, unwound links, hashtags, mentions, symbols]
        
       TODO: add return value for unicode emoji's used and sentiment timeline
    '''
    text = tweet['text']
    
    slices = []
    #Strip out the urls.
    #urls = []
    if 'urls' in tweet['entities']:
        for url in tweet['entities']['urls']:
            slices += [{'start': url['indices'][0], 'stop': url['indices'][1]}]
    #        u = unwound(url['expanded_url'])
    #        if u != url['expanded_url']:
    #            urls.append(u)
    
    #Strip out the hashtags.
    hs = []
    if 'hashtags' in tweet['entities']:
        for tag in tweet['entities']['hashtags']:
            slices += [{'start': tag['indices'][0], 'stop': tag['indices'][1]}]
            hs.append(tag['text'].lower())
    
    #Strip out the user mentions.
    me = []
    if 'user_mentions' in tweet['entities']:
        for men in tweet['entities']['user_mentions']:
            slices += [{'start': men['indices'][0], 'stop': men['indices'][1]}]
            me.append(men['screen_name'].lower())
    
    #Strip out the media.
    if 'media' in tweet['entities']:
        for med in tweet['entities']['media']:
            slices += [{'start': med['indices'][0], 'stop': med['indices'][1]}]
    
    #Strip out the symbols.
    sy = []
    if 'symbols' in tweet['entities']:
        for sym in tweet['entities']['symbols']:
            slices += [{'start': sym['indices'][0], 'stop': sym['indices'][1]}]
            sy.append(sym['text'].lower())
    
    # Sort the slices from highest start to lowest.
    slices = sorted(slices, key=lambda x: -x['start'])
    
    #No offsets, since we're sorted from highest to lowest.
    for s in slices:
        text = text[:s['start']] + text[s['stop']:]
        
    return [text.lower(), ['this is saved for emojis'], hs, me, sy]

def get_all_tweet_data(tweet, stripPuncutation=False):
    ''' Gets all point data in a tuple:
        (cleaned_text, urls, hashtags, mentions, symbols)
    '''
    all = get_text_cleaned(tweet)

    translator = str.maketrans('','',string.punctuation + '—–‒―') #remove the rest of the punctuation, including some crazy horizontal bar characters
    all[0] = str.translate(all[0], translator)
    return all

#Sanitizes the text by removing front and end punctuation, 
#making words lower case, and removing any empty strings.
def get_text_sanitized(tweet):
    clean_text = get_text_cleaned(tweet)
    return ' '.join([w.lower().strip().rstrip(string.punctuation).lstrip(string.punctuation).strip() for w in clean_text[0].split() if w.strip().rstrip(string.punctuation).strip()])

#Gets the text, clean it, make it lower case, remove stop words.
def get_text_normalized(tweet):
    #Sanitize the text first.
    text = get_text_sanitized(tweet).split()
    return text