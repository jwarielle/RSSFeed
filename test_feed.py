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

PUBLISH_ADD = ('localhost', 50500)
PUBLISH = 'publish'
BUF_SZ = 4096

class TestFeed(object):
    """
    Sends news to publisher to publish

    Attributes:
        publisher: UDP socket
            socket to send news on
    """

    def send_news(self, source, headline):
        """
        Send some news to the publisher
        """

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(PUBLISH_ADD)
                s.sendall(pickle.dumps((PUBLISH, source, headline)))
            except Exception as e:
                return None


if __name__ == '__main__':
    """
    Test feed driver takes news as argument
    """

    if len(sys.argv) < 2:
        print("Usage: python3 test_feed.py NEWS")
        exit()

    source = sys.argv[1]
    headline = sys.argv[2:]
    headline_string = " ".join(headline)

    test_feed = TestFeed()
    test_feed.send_news(source, headline_string)
