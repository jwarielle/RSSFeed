import pickle
import socket


class Reporter(object):
    def __init__(self, serv_host_name, serv_port):
        self.server_host_name = serv_host_name
        self.server_port = int(serv_port)
        self._news = None
        self._news_source = None

    @property
    def news_source(self):
        return self._news_source
    @news_source.setter
    def news_source(self, value):
        self._news_source = value

    @property
    def news(self):
        return self._news

    @news.setter
    def news(self, value):
        self._news = value

    def add_topic(self, source, news) -> bool:
        """
        Adds a new news topic to the host
        :param source: The source agency of the news (e.g. 'CNN', 'BBC', ...)
        :param news: The actual news header to be added (e.g. 'Midterm elections are underway in U.S.A.')
        :return: True, if topic is added successfully
        """
        pass

    def call_rpc(self, method, arg1, arg2):
        """
        Performs an RPC call to the remote server
        :param method: name of method to be executed
        :param arg1: 1st argument of the method to be executed
        :param arg2: 2nd argument of the method to be executed
        :return: Any
        """

        # Create tuple object for the message to be sent to remote server
        msg_to_send = (method, arg1, arg2)

        # Create socket and send RPC
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serv_sock:
            serv_sock.connect((self.server_host_name, self.server_port))
            serv_sock.sendall(pickle.dumps(msg_to_send))

if __name__ == '__main__':
    rep = Reporter('localhost', 50200)

    rep.news_source = 'CNN'
    rep.news = 'Obama Won!!!'

    print('Source: {}'.format(rep.news_source))
    print('{}'.format(rep.news))