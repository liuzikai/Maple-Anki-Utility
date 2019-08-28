import requests
from pyquery import PyQuery as pq
import webbrowser
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


def open_collins_website(word):
    webbrowser.open(collins_url + word)


class CollinsWorker(QThread):

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


google_image_url = "https://www.google.com/search?tbm=isch&q="


def open_google_image_website(word):
    webbrowser.open(google_image_url + word)


mac_dict_url = "dict://"


def open_mac_dict(word):
    webbrowser.open(mac_dict_url + word, autoraise=False)


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
        open_mac_dict(self.word)
        self.finished.emit(self.word)


if __name__ == '__main__':
    word = input("Please input a word: ")
    (freq, tips) = query_collins_word_frequency(word)
    print("Word frequency of %s is %d (%s)" % (word, freq, tips))
