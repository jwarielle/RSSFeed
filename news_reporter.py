"""
CPSC 5520, Seattle University
This is free and unencumbered software released into the public domain.
:Author: Aacer Daken and Arielle Wilson
:Filename: news_reporter.py
:Version: 1.0
Description: Client application for users to post news to RSS Feed
"""
import datetime
import pickle
import socket
import sys


BUF_SZ = 4096
CONN_TIMEOUT = 10

class Reporter(object):
    """
    Reporter class collects news from user, reports it to the news host server
    """

    #Global "constants" to be used in creation of XML and sending RPCs
    ADD_POST = 'add_post'
    SOURCE_TAG = 'source'
    HEADLINE_TAG = 'headline'

    def __init__(self, serv_host_name, serv_port):
        """
        Constructor
        Args:
            serv_host_name: Host name or IP address of host server
            serv_port: Port on host server to be contacted
        """
        self.server_host_name = serv_host_name
        self.server_port = int(serv_port)

    def add_post(self, source, headline) -> bool:
        """
        Adds a new news topic to the host
        Args:
            source: The source agency of the news (e.g. 'CNN', 'BBC', ...)
            headline: The actual news header to be added (e.g. 'Midterm elections are underway in U.S.A.')

        Returns: True, if topic is added successfully, else False

        """
        #Initialize XML helper object, and add news source and headline to XML file
        xml_file = Reporter.XmlHelper()
        xml_file.add_data(Reporter.SOURCE_TAG, source)
        xml_file.add_data(Reporter.HEADLINE_TAG, headline)

        #Make RPC call to server
        result = self.call_rpc(Reporter.ADD_POST, xml_file.get_xml())
        if result is True:
            print('Added news post successfully')
            return True
        else:
            print('Failed to add news post')
            return False

    def call_rpc(self, method, arg1):
        """
        Performs an RPC call to the remote server
        Args:
            method: name of method to be executed
            arg1: 1st argument of the method to be executed

        Returns: Any

        """
        # Create tuple object for the message to be sent to remote server
        msg_to_send = (method, arg1)
        recv_msg = False

        try:
            # Create socket connection with host server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serv_sock:
                serv_sock.connect((self.server_host_name, self.server_port))
                serv_sock.settimeout(CONN_TIMEOUT)

                #Send RPC
                serv_sock.sendall(pickle.dumps(msg_to_send))
                #Debug print
                Reporter._pr_sent_rpc(serv_sock, msg_to_send)

                #Block on response
                recv_msg = pickle.loads(serv_sock.recv(BUF_SZ))
                Reporter._pr_recv_rpc(serv_sock, recv_msg)

                #Close socket
                serv_sock.close()
            return recv_msg

        except OSError as excpt:
            print('Submitting news post failed. {}'.format(excpt))
            return False

    def run_ui(self) -> None:
        """
        UI for reporter, provide prompts to the user

        Returns: None

        """
        #Loop until user elects to exit program
        repeat = True
        while repeat:
            #Prompt user to enter news source and headline
            print('Enter news source:', end=' ')
            news_source = input().strip()
            print('Enter news headline:', end=' ')
            news_headline = input().strip()

            #Check that user entered actual values
            if len(news_source) == 0 or len(news_headline) == 0:
                print('Invalid input. Input must not be blank.')
            else:
                #Add post
                if self.add_post(news_source, news_headline):
                    print('News sent successfully')
                else:
                    print('Failed to send news. Try again')

            #Ask user if additional news need to be posted
            print('Enter \'y\' if you would like to post again, or other key to exit:', end=' ')
            user_input = input().lower().strip()

            #If user elects to exit, set loop condition to False
            if user_input != 'y':
                repeat = False

    @staticmethod
    def _pr_sent_rpc(sock: socket.socket, rpc) -> None:
        """
        Helper function to print sent RPCs
        Args:
            sock: Socket connection used for sending the RPC
            rpc: The content of the RPC message

        Returns: None

        """
        print('{} -> {}: Sent RPC: {} [{}]'.format(sock.getsockname(),
                                                   sock.getpeername(),
                                                   rpc,
                                                   Reporter._pr_now()))

    @staticmethod
    def _pr_recv_rpc(sock: socket.socket, rpc) -> None:
        """
        Helper function to print received RPC responses
        Args:
            sock: Socket connection used for sending the RPC
            rpc: The content of the RPC message

        Returns: None

        """
        print('{} -> {}: Received RPC: {} [{}]'.format(sock.getpeername(),
                                                   sock.getsockname(),
                                                   rpc,
                                                   Reporter._pr_now()))
    @staticmethod
    def _pr_now():
        """Helper method to print the current timestamp"""
        return datetime.datetime.now().strftime('%H:%M:%S.%f')

    class XmlHelper(object):
        """Helper class to create XML strings"""
        def __init__(self):
            self.xml_string = '<news>'  #init the XML string

        def add_data(self, tag, data) -> None:
            """
            Adds data to XML string
            :param
            tag: XML tag for the data to be added
                data: data to be added to XML string

            Returns:None

            """
            #Append new information to XML string
            self.xml_string = self.xml_string + '<{}>{}</{}>'.format(tag, data, tag)

        def get_xml(self) -> str:
            """
            Finalize XML file and returns string representation
            Returns: String representation of XML file

            """
            return self.xml_string + '</news>'

def print_welcome_message():
    """Prints a welcome message on console"""
    print()
    print('*******************************************************')
    print('* Welcome to CPSC5520 Lab6 RSS FEED NEWS REPORTER APP *')
    print('*******************************************************')
    print()


def print_goodbye_message():
    """Prints a goodbye message on console"""
    print()
    print('*******************************************************')
    print('* Thank you for using Lab6 RSS FEED NEWS REPORTER APP *')
    print('*******************************************************')
    print()


if __name__ == '__main__':
    #print welcome banner
    print_welcome_message()

    #if insufficient command line arguments provided, print error and exit program gracefully
    if len(sys.argv) != 3 and len(sys.argv) not in range(5, sys.maxsize):
        print('ERROR: Incorrect input arguments. Expecting news_host ADDRESS and PORT as input argument.')
        print('Expected format:')
        print('python3 news_reporter.py <Node address> <Node Address> <Node Port> [optional: <news source e.g. CNN> '
              '<news header>]')
        print('E.g.: python3 news_reporter.py localhost 50100')
        print_goodbye_message()
        exit(1)

    #Get host address and port number from command line arguments
    try:
        host_name = str(sys.argv[1])
        host_port = int(sys.argv[2])
    except OSError as excpt:
        print('Invalid port number provided')
        print_goodbye_message()
        exit(1)

    #Create news reporter object
    news_reporter = Reporter(host_name, host_port)

    #if only host address and port provided, run the UI to prompt the user for the news
    if len(sys.argv) < 5:
        news_reporter.run_ui()
        print_goodbye_message()
        exit(0)

    #if news provided in command line, add the post
    else:
        #Get the news source and headline from the command line arguments
        news_source = sys.argv[3]
        news_headline_list = sys.argv[4:]
        news_headline = ''
        for i in range(0, len(news_headline_list)):
            news_headline = news_headline + ' ' + news_headline_list[i]
        news_headline = news_headline.strip()

        #Add news received
        news_reporter.add_post(news_source, news_headline)
        print_goodbye_message()
        exit(0)

