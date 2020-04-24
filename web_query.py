#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from pyquery import PyQuery as pq
import webbrowser
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtCore import QUrl, QEventLoop
from PyQt5 import QtWebEngineWidgets
import urllib.parse


mac_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/605.1.15"
ios_user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"

# -------------------------------- Collins --------------------------------

collins_url = u"https://www.collinsdictionary.com/dictionary/english/%s"

collins_post_js = """
let selectors = ['iframe', '.topslot_container', '.cB-hook', '#videos', '.socialButtons', '.tabsNavigation',
                 '.res_cell_right', '.btmslot_a-container', '.exercise', '.mpuslot_b-container',
                 '._hj-f5b2a1eb-9b07_feedback_minimized_label', '.share-button', '.ac_leftslot_a',
                 '.new-from-collins'];
selectors.forEach(selector => document.querySelectorAll(selector).forEach(el => el.remove()));
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


def get_word_from_collins_url(url: str):
    if url.startswith(collins_url[:-2]):
        ret = url[len(collins_url[:-2]):]
        if ret.find("?") != -1:
            ret = ret[:ret.find("?")]
        return ret
    else:
        return None


# -------------------------------- Google Images --------------------------------

google_image_url = u"https://www.google.com/search?tbm=isch&q=%s"


def open_google_image_website(word):
    webbrowser.open(google_image_url + urllib.parse.quote(word))


# -------------------------------- Google Translate --------------------------------

google_translate_url = u"https://translate.google.com/?sl=en&tl=zh-CN&text=%s"

# -------------------------------- Google --------------------------------

google_url = u"https://www.google.com/search?q=%s"
