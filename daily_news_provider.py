"""
Forex Provider
(c) all rights reserved

This module implements a staging version the Forex Provider price feed on localhost.
"""
import pickle
import socket
import selectors
from datetime import datetime, timedelta

REQUEST_ADDRESS = ('localhost', 50411)
REQUEST_SIZE = 12


class TestPublisher(object):
    """
    Publishes news messages
    """
    def __init__(self):
        self.subscriptions = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def register_subscription(self, subscriber):
        print('registering subscription for {}'.format(subscriber))
        self.subscriptions[subscriber] = datetime.utcnow()

    def publish(self):
        if len(self.subscriptions) == 0:
            print('no subscriptions')
            return 1000.0  # nothing to do until we get a subscription, so we can wait a long time

        print('publishing')

        for subscriber in self.subscriptions:
            print('publishing {} to {}'.format('Hello', subscriber))
            self.socket.sendto(b'Hello', subscriber)


class DailyNewsProvider(object):
    """
    Accept subscriptions for a new instance of a given publisher class.
    """

    def __init__(self, request_address, publisher_class):
        """
        :param request_address:
        :param publisher_class: publisher class must support publish and register_
        """
        self.selector = selectors.DefaultSelector()
        self.subscription_requests = self.start_a_server(request_address)
        self.selector.register(self.subscription_requests, selectors.EVENT_READ)
        self.publisher = publisher_class()

    def run_forever(self):
        print('waiting for subscribers on {}  - v2'.format(self.subscription_requests))
        next_timeout = 0.2
        while True:
            events = self.selector.select(next_timeout)
            for key, mask in events:
                self.register_subscription()
            next_timeout = self.publisher.publish()

    def register_subscription(self):
        data, _address = self.subscription_requests.recvfrom(REQUEST_SIZE)
        subscriber = pickle.loads(data)
        self.publisher.register_subscription(subscriber)

    @staticmethod
    def start_a_server(address):
        """
        Start a socket bound to given address.

        :returns: listening socket
        """
        listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listener.bind(address)
        listener.settimeout(0.2)
        return listener


if __name__ == '__main__':
    if REQUEST_ADDRESS[1] == 50403:
        print('Pick your own port for testing!')
        print('Modify REQUEST_ADDRESS above to use localhost and some random port')
        exit(1)
    fxp = DailyNewsProvider(REQUEST_ADDRESS, TestPublisher)
    fxp.run_forever()
