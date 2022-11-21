import pickle
import socket
import sys

SERVER_ADDRESS = ('localhost', 50411)
BASE_PORT = 50420


class DailyNewsSubscriber(object):
    def __init__(self, node_id):
        self.publisher = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = ('localhost', BASE_PORT + node_id)

    def run(self):
        """
        Bind to UDP publisher socket and listen for published news
        """

        self.publisher.bind(self.address)
        self.publisher.sendto(pickle.dumps(self.address), SERVER_ADDRESS)

        while True:
            data = self.publisher.recv(4096)
            unpickled_data = pickle.loads(data)
            print('DATA: {}'.format(unpickled_data))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 daily_news_subscriber.py NODE_ID")
        exit()

    node_id = int(sys.argv[1])

    subscriber = DailyNewsSubscriber(node_id)
    subscriber.run()

