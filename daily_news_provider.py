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
import threading
from datetime import datetime, timedelta

REGISTER_ADD = ('localhost', 50414)
PUBLISH_ADD = ('localhost', 50500)
REQUEST_SIZE = 12
REGISTER = 'register'
BACKLOG = 100
BUF_SZ = 4096


class DailyNewsPublisher(object):
    """
    Publishes news messages

    Attributes:
         subscriptions: map {subscriber: datetime}
         socket: UDP socket
            publishing socket
    """
    def __init__(self):
        self.subscriptions = {}
        self.registration_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.publication_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start_register_server(self):
        self.registration_socket.bind(REGISTER_ADD)

        while True:
            msg, client = self.registration_socket.recvfrom(BUF_SZ)
            th = threading.Thread(target=self.register_subscription, args=(client, msg))
            th.start()

    def start_publication_server(self):
        self.publication_socket.bind(PUBLISH_ADD)
        self.publication_socket.listen(BACKLOG)

        while True:
            client, client_addr = self.publication_socket.accept()
            th = threading.Thread(target=self.handle_rpc, args=(client,))
            th.start()

    def handle_rpc(self, client):
        """
        Handles incoming rpc
        :param client: connecting client
        :return: any
            data returned from rpc
        """

        rpc = client.recv(BUF_SZ)
        method, arg1, arg2 = pickle.loads(rpc)
        print('method: {}'.format(method))
        result = self.dispatch_rpc(method, arg1, arg2)
        client.sendall(pickle.dumps(result))

    def dispatch_rpc(self, method, arg1, arg2):
        if method == 'publish':
            return self.publish(arg1, arg2) # arg1 is source and arg2 is headline

    def register_subscription(self, subscriber, msg):
        subscriber = pickle.loads(msg)

        print('registering subscription for {}'.format(subscriber))
        self.subscriptions[subscriber] = datetime.utcnow()

    def publish(self, source, headline):
        for subscriber in self.subscriptions:
            print('publishing news to {}'.format(subscriber))
            self.registration_socket.sendto(pickle.dumps((source, headline)), subscriber)


if __name__ == '__main__':
    """
    Driver for provider
    """

    dnp = DailyNewsPublisher()

    threading.Thread(target=dnp.start_register_server, args=()).start()
    threading.Thread(target=dnp.start_publication_server, args=()).start()

