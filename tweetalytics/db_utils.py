from contextlib import contextmanager
import psycopg2
import psycopg2.pool
import psycopg2.extras
import logging
import json
import os

class DBContext(object):

    @contextmanager
    def getcursor(self):
        con = self.connection_pool.getconn()
        try:
            yield con.cursor(cursor_factory=psycopg2.extras.DictCursor) #ensure we can use query results like a dict
            con.commit()
        finally:
            self.connection_pool.putconn(con)

    def reconnect(self):
        logging.debug("Establishing connection pool of size: " + str(self.minconnections))

        try:
            if self.connection_pool.closed: #if our current pool is closed, we need another one
                self.connection_pool = psycopg2.pool.SimpleConnectionPool(self.minconnections, self.maxconnections, database=self.dbname, host=self.host, port=self.port, user=self.user, password=self.password)
                logging.debug("Connection pool established.")
        except AttributeError: #we don't have a connection pool, create one
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(self.minconnections, self.maxconnections, database=self.dbname, host=self.host, port=self.port, user=self.user, password=self.password)
            logging.debug("Connection pool established.")

    def close(self):
        self.connection_pool.closeall()
        logging.debug("Database connection pool closed.")

    def getuserdata(self, id):
        '''gets the user's data from the stats table, returns False if none exists'''
        with self.getcursor() as cursor:
            logging.debug("Searching for user: " + str(id) + " in database.")
            cursor.execute("SELECT * FROM stats WHERE twitter_id = %s;", (str(id),))           
            try:
                user_stats = cursor.fetchone()
                if user_stats == None: #no data
                    logging.debug("No data found in database")
                    return False

                logging.debug("User found in database!")
                print()
                return user_stats #()
            except psycopg2.Error as e:
                print("Error retrieving user data:")
                print(e)
                return False

    def upsertuserdata(self, data):
        ''' Inserts or updates the users stats in the database 
            TODO: Add the rnn data to be uploaded
        '''
        with self.getcursor() as cursor:
            print("Updating user stats in database for user: " + data['twitter_id'])
            #upsert the stats row
            #m = cursor.mogrify(statement, d)
            #print(m)
            try:
                cursor.execute("INSERT INTO stats (word_frequency, hashtag_frequency, mentioned_user_frequency, tweet_times, latest_tweet_id, twitter_id, sentiment_timeline) VALUES (%(word_frequency)s, %(hashtag_frequency)s, %(mentioned_user_frequency)s, %(tweet_times)s, %(latest_tweet_id)s, %(twitter_id)s, %(sentiment_timeline)s) ON CONFLICT (twitter_id) DO UPDATE SET word_frequency = excluded.word_frequency, hashtag_frequency = excluded.hashtag_frequency, mentioned_user_frequency = excluded.mentioned_user_frequency, tweet_times = excluded.tweet_times, sentiment_timeline=excluded.sentiment_timeline, latest_tweet_id = excluded.latest_tweet_id;", data)
                print("Updated user stats: " + data['twitter_id'])
            except psycopg2.Error as e:
                print("Error:")
                print(e)

    def __init__(self, **kwargs):
        #logging.basicConfig(level=logging.DEBUG)

        self.dbname = 'tweetalytics'
        self.host = 'localhost'
        self.port = '5432'
        self.user = 'postgres'
        self.password = os.environ['dbpass']
        self.minconnections = 1
        self.maxconnections = 20
        self.reconnect()
            