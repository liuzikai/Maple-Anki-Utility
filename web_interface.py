#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from pyquery import PyQuery as pq
import webbrowser
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtCore import QUrl, QEventLoop
from PyQt5 import QtWebEngineWidgets
import urllib.parse

collins_url = u"https://www.collinsdictionary.com/dictionary/english/"


def query_collins_word_frequency(word):
    try:
        url = collins_url + urllib.parse.quote(word)
        headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"}
        return parse_collins_word_frequency(requests.get(url, headers=headers).text.encode('utf-8'))
    except Exception as err:
        return 0, str(err)


def parse_collins_word_frequency(html):
    try:
        doc = pq(html)
        freq_obj = doc(".word-frequency-img")
        if freq_obj is None:
            return 0, "Fail to find the word"
        freq_attr = freq_obj.attr("data-band")
        if freq_attr is None:
            return 0, "Fail to find the word"
        return int(freq_attr), freq_obj.attr("title")
    except Exception as err:
        return 0, str(err)


def open_collins_website(word):
    webbrowser.open(collins_url + urllib.parse.quote(word))


class CollinsWorker(QThread):

    finished = pyqtSignal(int, int, str)

    toHtmlFinished = pyqtSignal()

    def __init__(self, web_view):
        QThread.__init__(self)

        self.web_view = web_view

        self.idx = None
        self.word = None
        self.html = ""

    def __del__(self):
        self.wait()

    def query(self, idx, word):
        self.idx = idx
        self.word = word
        self.start()

    def run(self):
        (freq, tips) = query_collins_word_frequency(self.word)
        self.finished.emit(self.idx, freq, tips)


google_image_url = u"https://www.google.com/search?tbm=isch&q="


def open_google_image_website(word):
    webbrowser.open(google_image_url + urllib.parse.quote(word))


mac_dict_url = u"dict://"


def open_mac_dict(word):
    webbrowser.open(mac_dict_url + urllib.parse.quote(word), autoraise=False)


class MacDictWorker(QThread):

    finished = pyqtSignal(str)

    def __init__(self):
        QThread.__init__(self)
        self.word = None

    def __del__(self):
        self.wait()

    def search(self, word):
        self.word = word
        self.start()

    def run(self):
        open_collins_website(self.word)
        self.finished.emit(self.word)


if __name__ == '__main__':
    word = input("Please input a word: ")
    (freq, tips) = query_collins_word_frequency(word)
    print("Word frequency of %s is %d (%s)" % (word, freq, tips))
