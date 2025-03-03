import logging

import tweepy
from scrapy import Spider, Request, Selector
import json
import re
import requests

from tweepy import OAuth1UserHandler, API


class TwitterspiderSpider(Spider):
    name = 'twitter'
    allowed_domains = ["twitter.com"]
    start_urls = ["https://twitter.com"]

    def __init__(self):
        super(TwitterspiderSpider, self).__init__()

        consumer_key = 'V9mNpb9U1dOOYSwWow8Cdw9vL'
        consumer_secret = "J3OVZxdtJCrjaQwrg8hHfLA0EF4Z82jsQKVcK17khvHEigIpLZ"
        access_token = "2225339942-a8hxc6R3h4yZY5yZyYk2eU1nxq52kkImQhDl6Ya"
        access_token_secret = "xjxk9WPbWOjetq8cqrd2XbqctMEHEG1Pys18Bxbr8ux7k"
        CONSUMER_KEY = 'V9mNpb9U1dOOYSwWow8Cdw9vL'
        CONSUMER_SECRET = "J3OVZxdtJCrjaQwrg8hHfLA0EF4Z82jsQKVcK17khvHEigIpLZ"
        ACCESS_TOKEN = "2225339942-a8hxc6R3h4yZY5yZyYk2eU1nxq52kkImQhDl6Ya"
        ACCESS_TOKEN_SECRET = "xjxk9WPbWOjetq8cqrd2XbqctMEHEG1Pys18Bxbr8ux7k"

        # client = tweepy.Client(
        #     consumer_key="API / V9mNpb9U1dOOYSwWow8Cdw9vL",
        #     consumer_secret="API / J3OVZxdtJCrjaQwrg8hHfLA0EF4Z82jsQKVcK17khvHEigIpLZ",
        #     access_token="2225339942-a8hxc6R3h4yZY5yZyYk2eU1nxq52kkImQhDl6Ya",
        #     access_token_secret="xjxk9WPbWOjetq8cqrd2XbqctMEHEG1Pys18Bxbr8ux7k"
        # )
        auth = tweepy.OAuth1UserHandler(
            consumer_key, consumer_secret,
            access_token, access_token_secret
        )
        # Set up the API client
        # auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        # auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        # auth = tweepy.OAuth1UserHandler(
        #     "API / V9mNpb9U1dOOYSwWow8Cdw9vL", "API / J3OVZxdtJCrjaQwrg8hHfLA0EF4Z82jsQKVcK17khvHEigIpLZ",
        #     "2225339942-a8hxc6R3h4yZY5yZyYk2eU1nxq52kkImQhDl6Ya", "xjxk9WPbWOjetq8cqrd2XbqctMEHEG1Pys18Bxbr8ux7k"
        # )
        # Create the API object
        self.api = tweepy.API(auth, wait_on_rate_limit=True)

        logger = logging.getLogger("tweepy")
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename="tweepy.log")
        logger.addHandler(handler)

    def fetch_tweets(self, keyword, num_tweets):
        tweets = []

        # Use the API to fetch tweets
        for tweet in tweepy.Cursor(self.api.search_tweets, q=keyword, tweet_mode='extended').items(num_tweets):
            tweets.append(tweet.full_text)

        return tweets

    def start_requests(self):
        # Specify the keyword and number of tweets to fetch
        search_query = 'cricket'
        num_tweets = 10

        # Use the Twitter API to fetch tweets
        # tweets = self.fetch_tweets(keyword, num_tweets)
        tweets = self.api.search_tweets(q=search_query, lang="en", count=num_tweets, tweet_mode='extended')
        a=1

        # Process the fetched tweets
        for i, tweet in enumerate(tweets, start=1):
            yield {
                'tweet_number': i,
                'tweet_text': tweet
            }

    def parse(self, response, **kwargs):
        api = tweepy.API(self.auth)

        public_tweets = api.home_timeline()
        for tweet in public_tweets:
            print(tweet.text)
