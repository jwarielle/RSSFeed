"""
CPSC 5520, Seattle University
This is free and unencumbered software released into the public domain.
:Author: Arielle Wilson (and Aacer Daken)
:Version: 1.0
Description: Sends news test
"""

import pickle
import socket
from xml.etree.ElementTree import Element, SubElement, tostring

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

    def send_news(self, news):
        """
        Send some news to the publisher
        """

        tree_str = tostring(news)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(PUBLISH_ADD)
                s.sendall(pickle.dumps((PUBLISH, tree_str)))
            except Exception as e:
                return None


if __name__ == '__main__':
    """
    Test feed driver
    """

    root = Element('root')
    first_child = SubElement(root, "source")
    first_child.text = "BBC"
    sec_child = SubElement(root, "headline")
    sec_child.text = "Some News"

    test_feed = TestFeed()
    test_feed.send_news(root)
