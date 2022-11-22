import datetime
import pickle
import socket
import threading


BUF_SZ = 4096
CONN_TIMEOUT = 10

class Reporter(object):
    ADD_POST = 'add_post'

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

    def add_post(self, source, news) -> bool:
        """
        Adds a new news topic to the host
        :param source: The source agency of the news (e.g. 'CNN', 'BBC', ...)
        :param news: The actual news header to be added (e.g. 'Midterm elections are underway in U.S.A.')
        :return: True, if topic is added successfully
        """
        result = self.call_rpc(Reporter.ADD_POST, source, news)
        if result is True:
            print('Added news post successfully')
            return True
        else:
            print('Failed to add news post')
            return False

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
        recv_msg = False

        try:
            # Create socket and send RPC
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serv_sock:
                serv_sock.connect((self.server_host_name, self.server_port))
                serv_sock.settimeout(CONN_TIMEOUT)
                #Debug print
                print('{} -> {} Sent RPC: {} [{}]'.format(serv_sock.getsockname(),
                                                          serv_sock.getpeername(),
                                                          msg_to_send,
                                                          Reporter._pr_now()))
                serv_sock.sendall(pickle.dumps(msg_to_send))
                recv_msg = pickle.loads(serv_sock.recv(BUF_SZ))
                print('{} -> {} Recv RPC: {} [{}]'.format(serv_sock.getpeername(),
                                                          serv_sock.getsockname(),
                                                          recv_msg,
                                                          Reporter._pr_now()))
                serv_sock.close()

            if recv_msg is True:
                print('News post added successfully. {}: {}'.format(self.news_source, self.news))
                return True
            else:
                print('Server failed to add news post.{}: {}'.format(self.news_source, self.news))
                return False

        except OSError as excpt:
            print('Submitting news post failed. {}'.format(excpt))
            return False

    @staticmethod
    def _pr_now():
        """Helper method to print the current timestamp"""
        return datetime.datetime.now().strftime('%H:%M:%S.%f')

if __name__ == '__main__':
    rep = Reporter('localhost', 50100)
    rep2 = Reporter('localhost', 50100)

    rep.news_source = 'CNN'
    rep.news = 'Obama Won!!!'
    rep2.news_source = 'BBC'
    rep2.news = 'Queen Died!!!'

    threading.Thread(target=rep.add_post, args=(rep.news_source, rep.news)).start()
    threading.Thread(target=rep2.add_post, args=(rep2.news_source, rep2.news)).start()