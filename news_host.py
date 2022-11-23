import datetime
import random
import socket
import threading
import pickle
import sqlite3
import time
import hashlib

MUTEX = threading.Lock()
BUF_SZ = 4096
DB_NAME = 'lab6.db'
TABLE_NAME = 'news'

class NewsHost(object):
    ADD_POST = 'add_post'

    def __init__(self):
        self.listener, self.listener_addr = NewsHost.start_listener()
        self.database = self.SqlDb(DB_NAME, TABLE_NAME)

    def handle_rpc(self, client):
        """
        Handles incoming RPC calls from other nodes
        :param client: Client socket connection
        :return: Any, the response of the RPC method invocation
        """
        # Get address and port of the client invoking the RPC call
        client_addr, client_port = client.getpeername()

        # Receive the message from client, and marshal it
        rpc = client.recv(BUF_SZ)
        method, arg1, arg2 = pickle.loads(rpc)
        self._print_recv_rpc(client.getpeername(),(method, arg1, arg2))

        # Invoke the method for the given RPC request and send response to client
        result = self.dispatch_rpc(method, arg1, arg2)
        client.sendall(pickle.dumps(result))
        self._print_sent_rpc(client_port, result)

    def dispatch_rpc(self, method, arg1, arg2):
        """
        Invokes the method requested by RPC, and returns response
        :param method: method name
        :param arg1: arg1 for the method
        :param arg2: arg2 for the method
        :return: the return value from the method, can be None
        """
        if method == NewsHost.ADD_POST:
            return self.add_post(arg1, arg2)

    def add_post(self, source, news) -> bool:
        """
        Adds a new news topic to the database
        :param source: The source agency of the news (e.g. 'CNN', 'BBC', ...)
        :param news: The actual news header to be added (e.g. 'Midterm elections are underway in U.S.A.')
        :return: True, if topic is added successfully
        """
        time.sleep(random.randint(1, 3))
        MUTEX.acquire()
        print('DEBUG: add to file {}: {}'.format(source, news))
        self.database.add_entry(source, news)
        MUTEX.release()
        return True


    def listen(self):
        """
        Dispatch loop to listen to incoming RPCs. Each RPC is forked into its own thread for processing the RPC
        :return: None
        """
        while True:
            client, client_addr = self.listener.accept()
            handle_thread = None
            handle_thread = threading.Thread(target=self.handle_rpc, args=(client,))
            handle_thread.start()

    @staticmethod
    def start_listener(host = 'localhost', port = 50100):
        """
        Starts a listener for incoming connections
        :return Tuple containing socket object and address (socket, (host, port))
        """

        #Create TCP/IP socket, bind socket to host and port, then start listening
        srv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv_socket.bind((host, port))
        srv_socket.listen()

        #Debug print
        print('Started listener at {}'.format(srv_socket.getsockname()))

        # return socket and the address (host, port)
        return srv_socket, srv_socket.getsockname()

    def _print_sent_rpc(self, client_addr, rpc) -> None:
        """
        Helper function to print the details of a sent RPC
        :param client_addr: Address of node contacted
        :param rpc: The RPC sent
        :return: None
        """
        print('{} -> {}: Sent RPC: {} [{}]'.format(self.listener_addr,
                                                   client_addr,
                                                   rpc,
                                                   NewsHost._pr_now()))

    def _print_recv_rpc(self, client_addr, rpc) -> None:
        """
        Helper function to print the details of a received RPC
        :param client_addr: Address for the connection
        :param rpc: RPC received
        :return: None
        """
        print('{} -> {}: Received RPC: {} [{}]'.format(client_addr,
                                                       self.listener_addr,
                                                       rpc,
                                                       NewsHost._pr_now()))

    @staticmethod
    def _pr_now():
        """Helper method to print the current timestamp"""
        return datetime.datetime.now().strftime('%H:%M:%S.%f')

    class SqlDb(object):
        def __init__(self, db_name, table_name):
            self.db_name = db_name
            self.table_name = table_name

        def create_table(self, cursor):
            db_cursor = cursor
            command = """ CREATE TABLE IF NOT EXISTS {} (
                                            id NOT NULL,
                                            news_source NOT NULL,
                                            news_header NOT NULL,
                                            event_time NOT NULL
                                        );""".format(self.table_name)
            db_cursor.execute(command)


        def add_entry(self, news_src, news_header):
            db_connection = self.start_db_connection()
            db_cursor = db_connection.cursor()
            self.create_table(db_cursor)
            command = ' SELECT id FROM {} WHERE id >= (SELECT MAX(id) FROM {})'.format(self.table_name, self.table_name)
            # db_cursor = db_connection.cursor()
            id_list = db_cursor.execute(command).fetchall()
            print(id_list, len(id_list))
            if len(id_list) == 0:
                id = 1
            else:
                id = int(id_list[0][0]) + 1

            command = 'INSERT INTO {} VALUES(?, ?, ?, ?)'.format(self.table_name)
            data = (id, news_src, news_header, datetime.datetime.now())
            db_cursor.execute(command, data)
            print(db_cursor.execute('SELECT * FROM news').fetchall())
            db_connection.commit()
            db_cursor.close()
            db_connection.close()

            print(id)

        def start_db_connection(self):
            """
            Returns a cursor for a given DB
            :param db_name: Database name
            :return: Cursor to the database
            """
            # Connect to Database and create cursor object
            con = sqlite3.connect(self.db_name)
            return con

if __name__ == '__main__':
    host_srv = NewsHost()
    host_srv.listen()

