"""
CPSC 5520, Seattle University
This is free and unencumbered software released into the public domain.
:Author: Arielle Wilson (and Aacer Daken)
:Version: 1.0
Description: Sends news test
"""

import pickle
import socket
import sys

SERVER_ADDRESS = ('localhost', 50411)
NEWS = 'NEWS'

class TestFeed(object):
    """
    Sends news to publisher to publish

    Attributes:
        publisher: UDP socket
            socket to send news on
    """

    def __init__(self):
        self.publisher = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_news(self, news):
        """
        Send some news to the publisher
        """

        self.publisher.sendto(pickle.dumps((NEWS, news)), SERVER_ADDRESS)

if __name__ == '__main__':
    """
    Test feed driver takes news as argument
    """

    if len(sys.argv) < 2:
        print("Usage: python3 test_feed.py NEWS")
        exit()

    news = sys.argv[1:]
    news_string = " ".join(news)

    test_feed = TestFeed()
    test_feed.send_news(news_string)
