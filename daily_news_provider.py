"""
CPSC 5520, Seattle University
This is free and unencumbered software released into the public domain.
:Author: Arielle Wilson and Aacer Daken
:Version: 1.0
Description: publishes daily news from RSS feed to subscribers
"""
import sys
import pickle
import socket
import selectors
import threading
from datetime import datetime, timedelta

REGISTER_ADD = ('localhost', 50414)
PUBLISH_ADD = ('localhost', 50500)
REQUEST_SIZE = 12
REGISTER = 'register'
PUBLISH = 'publish'
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
    def __init__(self, reg_port, pub_port):
        self.subscriptions = {}
        self.registration_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.publication_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.registration_address = ('localhost', reg_port)
        self.publication_address = ('localhost', pub_port)

    def start_register_server(self):
        """
        Starts UDP register listener and registers subscribers that connect
        """

        self.registration_socket.bind(self.registration_address)

        while True:
            msg, client = self.registration_socket.recvfrom(BUF_SZ)
            th = threading.Thread(target=self.handle_rpc_from_subscriber, args=(client, msg))
            th.start()

    def start_publication_server(self):
        """
        Starts TCP publication server, which listens for RPCs
        from the host
        """

        self.publication_socket.bind(self.publication_address)
        self.publication_socket.listen(BACKLOG)

        while True:
            client, client_addr = self.publication_socket.accept()
            th = threading.Thread(target=self.handle_rpc_from_host, args=(client,))
            th.start()

    def handle_rpc_from_host(self, client):
        """
        Handles incoming rpc for tcp connection from host
        :param client: connecting client
        """

        rpc = client.recv(BUF_SZ)
        method, arg1 = pickle.loads(rpc)
        result = self.dispatch_rpc(method, arg1)
        client.sendall(pickle.dumps(result))

    def handle_rpc_from_subscriber(self, client, msg):
        """
        Handles incoming rpc for UDP connection from subscriber
        :param client: connecting client
        :param: msg: any
            argument for rpc
        """

        args = pickle.loads(msg)
        method, result, sub_addr = self.dispatch_rpc(args[0], args[1])
        self.registration_socket.sendto(pickle.dumps((method, result)), sub_addr)

    def dispatch_rpc(self, method, arg1):
        """
        Dispatches rpc according to method name
        :param method: str
            rpc to call
        :param arg1: any
            rpc argument
        :return: any
            result of dispatched method
        """

        if method == PUBLISH:
            return self.publish(arg1)
        elif method == REGISTER:
            return self.register(arg1)

    def register(self, sub_address):
        """
        Registers subscriber
        :param sub_address: client address
            Client wanting publications
        :return: (method, result str, address of subscriber)
        """

        print('registering subscription for {}'.format(sub_address))
        self.subscriptions[sub_address] = datetime.utcnow()
        return REGISTER, 'Registered', sub_address

    def publish(self, xml_str):
        """
        Publishes news to subscribers
        :param xml_str: byte str
            news as xml string
        :return: boolean
        """

        if len(self.subscriptions) == 0:
            return False

        for subscriber in self.subscriptions:
            print('publishing news to {}'.format(subscriber))
            self.registration_socket.sendto(pickle.dumps((PUBLISH, xml_str)), subscriber)

        return True


if __name__ == '__main__':
    """
    Publisher driver
    """

    if len(sys.argv) < 3:
        print('Please enter the registration and publication ports for this node.')
        print("Usage: python3 daily_news_provider.py <registration port> <publication port>")
        print("For example: python3 daily_news_provider.py 50414 50500")
        exit()

    reg_port = int(sys.argv[1])
    pub_port = int(sys.argv[2])

    dnp = DailyNewsPublisher(reg_port, pub_port)

    threading.Thread(target=dnp.start_register_server, args=()).start()
    threading.Thread(target=dnp.start_publication_server, args=()).start()

