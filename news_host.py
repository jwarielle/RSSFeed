"""
CPSC 5520, Seattle University
This is free and unencumbered software released into the public domain.
:Author: Aacer Daken and Arielle Wilson
:Filename: news_host.py
:Version: 1.0

Description: Host server application for submitting news posts for publishing. This application interacts with the
persistent database, to store news posts, and retrieve any unpublished posts in case of failures

Usage:
    python3 news_host.py <publisher hostname> <publisher port>
    e.g: python3 news_host.py localhost 50123
"""
import datetime
import pickle
import socket
import sqlite3
import threading
import time
import sys
import xml.etree.ElementTree

DB_MUTEX = threading.Lock()     #Mutex for protecting the database, and treating it as a critical section
QUEUE_MUTEX = threading.Lock()  #Mutex for protecting the send queue, and treating it as a critical section
BUF_SZ = 4096                   #Buffer size for receiving messages
DB_NAME = 'lab6.db'             #Database name/path
TABLE_NAME = 'news'             #Name of table in database hosting the news posts

class NewsHost(object):
    """
    NewsHost object listens to reporters, stores the news posts into a SQLite DB, and publishes the news to the
    publisher
    """

    ADD_POST = 'add_post'       #RPC name for adding posts
    PUBLISH = 'publish'         #RPC name for publishing posts
    SOURCE_TAG = 'source'       #XML tag for source identification
    Headline_TAG = 'headline'   #XML tag for headline identification
    ROOT_TAG = 'news'           #XML tag for the root of the XML file/string


    def __init__(self, pub_addr = 'localhost', pub_port = 50500, listener_port = 0):
        """
        Constructor for the news_host
        Args:
            pub_addr: Hostname of publisher to be contacted for sending data
            pub_port: Port number for the publisher to be contacted for sending data
        """
        self.listener, self.listener_addr = NewsHost.start_listener(port = int(listener_port))
        self.database = self.SqlDb(DB_NAME, TABLE_NAME)
        self.send_queue = {}
        self.publisher_addr = pub_addr
        self.publisher_port = int(pub_port)

    def handle_rpc(self, client) -> None:
        """
        Handles incoming RPC calls from other nodes
        Args:
            client: client: Client socket connection

        Returns: None

        """

        # Receive the message from client, and marshal it
        rpc = client.recv(BUF_SZ)
        method, arg1 = pickle.loads(rpc)
        self._print_recv_rpc(client.getpeername(),(method, arg1))

        # Invoke the method for the given RPC request and send response to client
        result = self.dispatch_rpc(method, arg1)
        client.sendall(pickle.dumps(result))
        self._print_sent_rpc(client.getpeername(), result)

    def dispatch_rpc(self, method, arg1):
        """
        Invokes the method requested by RPC, and returns response
        Args:
            method: method to be invoked
            arg1: arg1 for the method

        Returns: The return value from the method, can be None

        """

        #If RPC requesting to add a new news post ('add_post')
        if method == NewsHost.ADD_POST:
            #Extract information from XML string (news source, news headline)
            news_src = xml.etree.ElementTree.fromstring(arg1).find(NewsHost.SOURCE_TAG).text
            news_headline = xml.etree.ElementTree.fromstring(arg1).find(NewsHost.Headline_TAG).text

            #Invoke the add_post method, with provided information to commit data to Database
            result = self.add_post(news_src, news_headline)

            #Add news post to send queue, to send to publisher
            QUEUE_MUTEX.acquire()
            self.send_queue[result[1]] = arg1
            QUEUE_MUTEX.release()

            #return the result to caller
            return result

    def add_post(self, source, news) -> (bool, int):
        """
        Adds a new news topic to the database
        :param source: The source agency of the news (e.g. 'CNN', 'BBC', ...)
        :param news: The actual news header to be added (e.g. 'Midterm elections are underway in U.S.A.')
        :return: True, if topic is added successfully, along with ID of entry in database
        """
        #Lock database using mutex from any modification
        DB_MUTEX.acquire()
        # print('DEBUG: add to file {}: {}'.format(source, news))

        #Add post to database, then release DB lock
        id = self.database.add_entry(source, news)
        DB_MUTEX.release()

        #return entry id in DB
        return True, id

    def send_news(self) -> None:
        """
        Sends news in send_queue to publisher.

        Send queue is appended everytime a news post is added, or on boot if there are any entries in DB that haven't
        been published. Once published, item is removed from the queue
        Returns: None

        """

        #Get list of unpublished entries from the database
        unpublished_list = self.database.get_unpublished()

        #For each item in tha unpublished list, add to the send_queue in XML format
        for item in unpublished_list:
            self.send_queue[item[0]] = '<{}><{}>{}</{}><{}>{}</{}></{}>'.format(NewsHost.ROOT_TAG,
                                                                                NewsHost.SOURCE_TAG,
                                                                                item[1],
                                                                                NewsHost.SOURCE_TAG,
                                                                                NewsHost.Headline_TAG,
                                                                                item[2],
                                                                                NewsHost.Headline_TAG,
                                                                                NewsHost.ROOT_TAG)

        #Infinite loop that checks if new items have been added to the queue, and sends them to publisher
        while True:
            try:

                #For each item in the send_queue, publish the news item to publisher
                QUEUE_MUTEX.acquire()
                send_queue_snapshot = self.send_queue.copy()
                QUEUE_MUTEX.release()
                for id, item in send_queue_snapshot.items():
                    send_msg = (NewsHost.PUBLISH, item)

                    #Create socket, then send message, and receive response
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                        client.connect((self.publisher_addr, self.publisher_port))
                        client.sendall(pickle.dumps(send_msg))
                        self._print_sent_rpc(client.getpeername(), send_msg)
                        recv_msg = pickle.loads(client.recv(BUF_SZ))
                        self._print_recv_rpc(client.getpeername(), recv_msg)
                        client.close()

                        #If publisher's response is not success, then exit the loop and try again later
                        if recv_msg is not True:
                            break

                        #If publisher's response is success, then mark the data as published in database
                        else:
                            DB_MUTEX.acquire()
                            self.database.update_entry_publishing_state(id, True)
                            DB_MUTEX.release()

                            #Remove data for send_queue, so that it is not sent again in next iteration
                            QUEUE_MUTEX.acquire()
                            self.send_queue.pop(id)
                            QUEUE_MUTEX.release()

            except OSError as excpt:
                print('Failed to send queue to publisher. {}'.format(excpt))
            time.sleep(1)

    def listen(self) -> None:
        """
        Dispatch loop to listen to incoming RPCs. Each RPC is forked into its own thread for processing the RPC

        Returns:None

        """

        #infinite loop listening to incoming connection requests, and forking a thread to handle incoming RPC
        while True:
            client, client_addr = self.listener.accept()
            handle_thread = threading.Thread(target=self.handle_rpc, args=(client,))
            handle_thread.start()

    @staticmethod
    def start_listener(host = 'localhost', port = 0):
        """

        Starts a listener for incoming connections

        Args:
            host: Host address/name for the listening server
            port: Port number for the listening server

        Returns:Tuple containing socket object and address (socket, (host, port))

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
        """
        SQLite Database object
        """
        def __init__(self, db_name, table_name):
            """
            Constructor
            Args:
                db_name: Name of DB to be created/accessed
                table_name: Name of table to be created/accessed
            """
            self.db_name = db_name
            self.table_name = table_name

        def create_table(self, cursor: sqlite3.Cursor):
            """
            Creates a table, if it doesn't exist, using the table name provided to constructor
            Args:
                cursor: Cursor object to be used in executing the SQL command

            Returns: None

            """
            db_cursor = cursor
            command = """ CREATE TABLE IF NOT EXISTS {} (
                                            id int PRIMARY KEY NOT NULL,
                                            news_source text NOT NULL,
                                            news_header text NOT NULL,
                                            event_time datetime NOT NULL,
                                            is_published int NOT NULL
                                        );""".format(self.table_name)
            db_cursor.execute(command)

        def add_entry(self, news_src, news_header) -> int:
            """
            Adds an entry to the database
            Args:
                news_src: information to be added to the news source column
                news_header: information to be added to the news headline column

            Returns: ID of the new entry created

            """

            #Create connection and cursor for the database
            db_connection = self.start_db_connection()
            db_cursor = db_connection.cursor()

            #Create the table to be used
            self.create_table(db_cursor)

            #Query database to get the last ID used. If none, then next ID is 1, otherwise next ID is current ID + 1
            command = ' SELECT id FROM {} WHERE id >= (SELECT MAX(id) FROM {})'.format(self.table_name, self.table_name)
            id_list = db_cursor.execute(command).fetchall()
            # print(id_list, len(id_list))
            if len(id_list) == 0:
                id = 1
            else:
                id = int(id_list[0][0]) + 1


            #Insert data into the database
            command = 'INSERT INTO {} VALUES(?, ?, ?, ?, ?)'.format(self.table_name)
            data = (id, news_src, news_header, datetime.datetime.now(), False)
            db_cursor.execute(command, data)
            # print(db_cursor.execute('SELECT * FROM news').fetchall())

            #Commit DB changes and close connection
            db_connection.commit()
            db_cursor.close()
            db_connection.close()

            #Return the id of the newly created entry
            return id

        def update_entry_publishing_state(self, id: int, state: bool) -> None:
            """
            Updates the state of 'is_published' of an entry in the DB table
            Args:
                id: ID of entry to be modified
                state: The requested state of the entry

            Returns: None

            """

            #Create connection and cursor for the db file
            db_connection = self.start_db_connection()
            db_cursor = db_connection.cursor()

            #Execute update command for the given item
            command = 'UPDATE {} SET is_published = ? WHERE id = ?'.format(self.table_name)
            data = (state, id)
            db_cursor.execute(command, data)
            # print(db_cursor.execute('SELECT * FROM news').fetchall())

            #Commit changes and close connection
            db_connection.commit()
            db_cursor.close()
            db_connection.close()

        def get_unpublished(self) -> list:
            """
            Queries for all unpublished items stored in the database

            Returns: List containing all unpublished items

            """
            #Create connection and cursor for DB
            db_connection = self.start_db_connection()
            db_cursor = db_connection.cursor()

            #if table doesn't exist, create it, and query for unpublished items
            self.create_table(db_cursor)
            command = 'SELECT id, news_source, news_header FROM news WHERE is_published = FALSE'

            #Return the list of unpublished items
            return db_cursor.execute(command).fetchall()

        def start_db_connection(self):
            """
            Returns a connection for a given DB
            :return: Connection to the database
            """
            # Connect to Database and create cursor object
            con = sqlite3.connect(self.db_name)
            return con

def print_welcome_message():
    """Prints a welcome message on console"""
    print()
    print('***************************************************')
    print('* Welcome to CPSC5520 Lab6 RSS FEED NEWS HOST APP *')
    print('***************************************************')
    print()


def print_goodbye_message():
    """Prints a goodbye message on console"""
    print()
    print('***************************************************')
    print('* Thank you for using Lab6 RSS FEED NEWS HOST APP *')
    print('***************************************************')
    print()


if __name__ == '__main__':
    #print welcome banner
    print_welcome_message()

    #if insufficient command line arguments provided, print error and exit program gracefully
    if len(sys.argv) != 3:
        print('ERROR: Incorrect input arguments. Expecting daily_news_provider ADDRESS and PORT as input argument.')
        print('Expected format:')
        print('python3 news_host.py <Provider address> <Provider Port>')
        print('E.g.: python3 news_host.py localhost 50200')
        print_goodbye_message()
        exit(1)

    #Get host address and port number from command line arguments
    try:
        listening_port = str(sys.argv[1])
        pub_port = int(sys.argv[2])
    except OSError as excpt:
        print('Invalid port number provided')
        print_goodbye_message()
        exit(1)

    #Create news reporter object
    host_srv = NewsHost(listener_port=listening_port, pub_port=pub_port)

    #Create a thread for the listener and a thread for the news sender
    threading.Thread(target=host_srv.listen, args=()).start()
    threading.Thread(target=host_srv.send_news, args=()).start()

