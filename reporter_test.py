"""
CPSC 5520, Seattle University
This is free and unencumbered software released into the public domain.
:Author: Aacer Daken and Arielle Wilson
:Filename: reporter_test.py
:Version: 1.0
Description: Test driver for news_reporter
"""
import random
import threading
import time

import news_reporter

LOOPS = 10
NUM_CLIENTS = 20
HOST_NAME = 'localhost'
HOST_PORT = 50100
EVENTS = [
    'Shooting',
    'Hurricane',
    'War',
    'Celebrations',
    'Heavy rain',
    'Flooding',
    'Elections'
]
PLACES = [
    'America',
    'Zimbabwe',
    'Tha Bahamas',
    'Cambodia',
    'New Zealand',
    'The Netherlands',
    'Egypt',
    'South Africa',
    'Papua New Guinea'
]
SOURCES = [
    'CNN',
    'BBC',
    'FOX',
    'EuroNews',
    'SkyNews',
    'AlJazeera',
    'Reuters',
    'France24',
    'DW',
    'AssociatedPress'
]


def run():
    # Create a Reporter object
    reporter = news_reporter.Reporter(HOST_NAME, HOST_PORT)
    # For specified number of loops, create a news post, and start a thread to post the new news
    for i in range(0, LOOPS):
        source = SOURCES[random.randint(0, len(SOURCES) - 1)]
        headline = EVENTS[random.randint(0, len(EVENTS) - 1)] + ' in ' + PLACES[random.randint(0, len(PLACES) - 1)]
        threading.Thread(target=reporter.add_post, args=(source, headline,)).start()
        time.sleep(random.randint(0,2))


if __name__ == '__main__':

    for i in range(0, NUM_CLIENTS):
        threading.Thread(target=run, args=()).start()

