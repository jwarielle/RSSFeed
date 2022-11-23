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
    Publishes news messages to subscribers

    Attributes:
         subscriptions: map {subscriber: datetime}
         registration_socket: UDP socket
         publication_socket: TCP socket
    """
    def __init__(self):
        self.subscriptions = {}
        self.registration_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.publication_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start_register_server(self):
        """
        Starts UDP register listener and registers subscribers that connect
        """

        self.registration_socket.bind(REGISTER_ADD)

        while True:
            msg, client = self.registration_socket.recvfrom(BUF_SZ)
            th = threading.Thread(target=self.register_subscription, args=(client, msg))
            th.start()

    def start_publication_server(self):
        """
        Starts TCP publication server, which listens for RPCs
        from the host
        :return:
        """

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
        method, arg1 = pickle.loads(rpc)
        result = self.dispatch_rpc(method, arg1)
        client.sendall(pickle.dumps(result))

    def dispatch_rpc(self, method, arg1):
        """
        Dispatches rpc according to method name
        :param method: str
            rpc to call
        :param arg1: any
            rpc argument
        :return:
        """

        if method == 'publish':
            return self.publish(arg1) # arg1 is xml string

    def register_subscription(self, subscriber, msg):
        """
        Registers subscriber
        :param subscriber: client socket
            Client wanting publications
        :param msg: tuple (host, port)
            subscriber address
        """

        subscriber = pickle.loads(msg)

        print('registering subscription for {}'.format(subscriber))
        self.subscriptions[subscriber] = datetime.utcnow()

    def publish(self, xml_str):
        """
        Publishes news to subscribers
        :param xml_str: byte str
            news as xml string
        :return:
        """

        for subscriber in self.subscriptions:
            print('publishing news to {}'.format(subscriber))
            self.registration_socket.sendto(pickle.dumps(xml_str), subscriber)


if __name__ == '__main__':
    """
    Publisher driver
    """

    dnp = DailyNewsPublisher()

    threading.Thread(target=dnp.start_register_server, args=()).start()
    threading.Thread(target=dnp.start_publication_server, args=()).start()

