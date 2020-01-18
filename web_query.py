#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from pyquery import PyQuery as pq
import webbrowser
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtCore import QUrl, QEventLoop
from PyQt5 import QtWebEngineWidgets
import urllib.parse


mac_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8"
ios_user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"

# -------------------------------- Collins --------------------------------

collins_url = u"https://www.collinsdictionary.com/dictionary/english/%s"

collins_post_js = """
$('iframe').remove()
$('.topslot_container').remove()
$('.cB-hook').remove()
$('#videos').remove()
$('.socialButtons').remove()
$('.tabsNavigation').remove()
$('.res_cell_right').remove()
$('.btmslot_a-container').remove()
$('.exercise').remove()
$('.mpuslot_b-container').remove()
$('._hj-f5b2a1eb-9b07_feedback_minimized_label').remove()
$('.share-button').remove()
"""


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


# -------------------------------- Google Images --------------------------------

google_image_url = u"https://www.google.com/search?tbm=isch&q=%s"


def open_google_image_website(word):
    webbrowser.open(google_image_url + urllib.parse.quote(word))


# -------------------------------- Google Translate --------------------------------

google_translate_url = u"https://translate.google.com/?sl=en&tl=zh-CN&text=%s"

# -------------------------------- Google --------------------------------

google_url = u"https://www.google.com/search?q=%s"
