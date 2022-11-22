"""
CPSC 5520, Seattle University
This is free and unencumbered software released into the public domain.
:Author: Arielle Wilson (and Aacer Daken)
:Version: 1.0
Description: publishes daily news from RSS feed to subscribers
"""
import pickle
import socket
import selectors
from datetime import datetime, timedelta

REQUEST_ADDRESS = ('localhost', 50411)
REQUEST_SIZE = 12
REGISTER = 'REGISTER'
NEWS = 'NEWS'


class TestPublisher(object):
    """
    Publishes news messages

    Attributes:
         subscriptions: map {subscriber: datetime}
         socket: UDP socket
            publishing socket
    """
    def __init__(self):
        self.subscriptions = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def register_subscription(self, subscriber):
        """
        Registers subscriber
        :param subscriber: tuple
            Address of subscriber
        """

        print('registering subscription for {}'.format(subscriber))
        self.subscriptions[subscriber] = datetime.utcnow()

    def publish(self):
        """
        Publishes daily news to subscribers
        """

        if len(self.subscriptions) == 0:
            print('no subscriptions')
            return 1000.0  # nothing to do until we get a subscription, so we can wait a long time

        for subscriber in self.subscriptions:
            print('publishing {} to {}'.format('Hello', subscriber))
            self.socket.sendto(pickle.dumps('Hello'), subscriber)

    def publish_news(self, data):
        if len(self.subscriptions) == 0:
            print('no subscriptions')
            return 1000.0  # nothing to do until we get a subscription, so we can wait a long time

        for subscriber in self.subscriptions:
            print('publishing news to {}'.format(subscriber))
            self.socket.sendto(pickle.dumps(data), subscriber)


class DailyNewsProvider(object):
    """
    Accepts subscriptions for a new instance of a given publisher class.
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
        """
        Listens for new subscribers and gets them registered
        """

        print('waiting for subscribers on {}'.format(self.subscription_requests))
        next_timeout = 0.2
        while True:
            events = self.selector.select(next_timeout)
            for key, mask in events:
                self.register_subscription()
            next_timeout = self.publisher.publish()

    def register_subscription(self):
        """
        Registers subscriber
        """

        data, _address = self.subscription_requests.recvfrom(4096)
        subscriber_data = pickle.loads(data)

        if subscriber_data[0] == REGISTER:
            self.publisher.register_subscription(subscriber_data[1])
        elif subscriber_data[0] == NEWS:
            self.publisher.publish_news(subscriber_data[1])

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
    """
    Driver for provider
    """

    dnp = DailyNewsProvider(REQUEST_ADDRESS, TestPublisher)
    dnp.run_forever()
