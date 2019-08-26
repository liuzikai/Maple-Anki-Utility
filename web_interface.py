import typing

import requests
from pyquery import PyQuery as pq
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

collins_url = "https://www.collinsdictionary.com/dictionary/english/"


def query_collins_word_frequency(word):
    try:
        url = collins_url + word
        doc = pq(requests.get(url).text.encode('utf-8'))
        freq_obj = doc(".word-frequency-img")
        if freq_obj is None:
            return 0, "Fail to find the word"
        else:
            return int(freq_obj.attr("data-band")), freq_obj.attr("title")
    except Exception as err:
        return 0, str(err)


class WebWorker(QThread):

    finished = pyqtSignal(int, int, str)

    def __init__(self):
        QThread.__init__(self)

        self.idx = None
        self.word = None

    def __del__(self):
        self.wait()

    def query(self, idx, word):
        self.idx = idx
        self.word = word
        self.start()

    def run(self):
        (freq, tips) = query_collins_word_frequency(self.word)
        self.finished.emit(self.idx, freq, tips)


if __name__ == '__main__':
    word = input("Please input a word: ")
    print("Word frequency of %s is %d" % (word, query_collins_word_frequency(word)))
