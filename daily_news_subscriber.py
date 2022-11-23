"""
CPSC 5520, Seattle University
This is free and unencumbered software released into the public domain.
:Author: Arielle Wilson (and Aacer Daken)
:Version: 1.0
Description: Subscribes to daily news from RSS feed
"""

import pickle
import socket
import sys
from xml.etree.ElementTree import Element, SubElement, tostring, fromstring

REGISTER_ADD = ('localhost', 50414)
BASE_PORT = 50420
REGISTER = 'register'
BUF_SZ = 4096


class DailyNewsSubscriber(object):
    """
    Subscribes to RSS Feed daily news

    Attributes:
        publisher: UDP socket
            publishers address that subscriber sends address to
        address: tuple (host, port)
            Listener address for publications
    """

    def __init__(self, node_id):
        """
        :param node_id: Id of subscriber node
        """

        self.publisher = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = ('localhost', BASE_PORT + node_id)

    def run(self):
        """
        Bind to UDP publisher socket and listen for published news
        """

        self.publisher.bind(self.address)
        self.publisher.sendto(pickle.dumps(self.address), REGISTER_ADD)

        while True:
            data = pickle.loads(self.publisher.recv(BUF_SZ))
            self.parse_xml(data)

    def parse_xml(self, data):
        """
        Parases xml string from publisher
        :param data: xml byte string
        """

        root = fromstring(data)
        source = root[0].text
        headline = root[1].text
        print('{}: {}'.format(source, headline))

if __name__ == '__main__':
    """
    Subscriber driver that takes subscriber node id
    """

    if len(sys.argv) < 2:
        print("Usage: python3 daily_news_subscriber.py NODE_ID")
        exit()

    node_id = int(sys.argv[1])

    subscriber = DailyNewsSubscriber(node_id)
    subscriber.run()

