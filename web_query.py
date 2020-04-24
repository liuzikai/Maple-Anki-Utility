#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests

from pyquery import PyQuery as pq
from collections import deque

from PyQt5 import QtCore
from PyQt5 import QtWebEngineWidgets


class QueryManager(QtCore.QObject):

    start_worker = QtCore.pyqtSignal(int, str)  # worker, url
    worker_progress = QtCore.pyqtSignal(int, int)  # worker, progress
    worker_usage = QtCore.pyqtSignal(int, int, int)  # finished, working, free

    worker_activated = QtCore.pyqtSignal(int, bool)  # worker, finished
    active_worker_progress = QtCore.pyqtSignal(int, int)  # active_worker, process

    collins_suggestion_retrieved = QtCore.pyqtSignal(str, str)  # original_subject, suggestion
    collins_freq_retrieved = QtCore.pyqtSignal(str, int, str)  # original_subject, freq, tip

    COLLINS = 0
    GOOGLE_IMAGE = 1
    GOOGLE_TRANSLATE = 2
    GOOGLE = 3

    URLS = [
        u"https://www.collinsdictionary.com/dictionary/english/%s",
        u"https://www.google.com/search?tbm=isch&q=%s",
        u"https://translate.google.com/?sl=en&tl=zh-CN&text=%s",
        u"https://www.google.com/search?q=%s"
    ]

    MAC_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/605.1.15"
    IOS_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"

    COLLINS_POST_JS = """
    let selectors = ['iframe', '.topslot_container', '.cB-hook', '#videos', '.socialButtons', '.tabsNavigation',
                     '.res_cell_right', '.btmslot_a-container', '.exercise', '.mpuslot_b-container',
                     '._hj-f5b2a1eb-9b07_feedback_minimized_label', '.share-button', '.ac_leftslot_a',
                     '.new-from-collins'];
    selectors.forEach(selector => document.querySelectorAll(selector).forEach(el => el.remove()));
    """

    QUERY_INTERVAL = 5000  # [ms]

    def __init__(self, worker_count: int):
        super().__init__()

        self._worker_count = worker_count

        self._worker = [{
            "subject": "",
            "query": -1,
            "progress": 0
        }] * worker_count

        self._active_worker = -1

        self._finished_workers = deque()
        self._working_workers = deque()
        self._free_workers = deque()
        for i in range(self._worker_count):
            self._free_workers.append(i)
        self.report_worker_usage()

        self._query_count = {}
        self._pending_queries = deque()  # (subject, query, worker)
        self._started_queries = deque()  # (subject, query)

        self._query_timer = QtCore.QTimer()
        self._query_timer.setSingleShot(False)
        self._query_timer.timeout.connect(self._query_timer_timeout)
        self._query_timer.start(self.QUERY_INTERVAL)

    @QtCore.pyqtSlot(int)
    def load_start(self, idx: int):
        self._handle_progress(idx, 0)
        # Moving current worker to self._working_worker is completed before this

    @QtCore.pyqtSlot(int, int)
    def load_progress(self, idx: int, progress: int):
        self._handle_progress(idx, progress)

    @QtCore.pyqtSlot(int, bool)
    def load_finished(self, idx: int, ok: bool):
        self._handle_progress(idx, 100)
        self._working_workers.remove(idx)
        self._finished_workers.append(idx)

        sender: QtWebEngineWidgets.QWebEngineView = self.sender()
        if self._worker[idx]["query"] == self.COLLINS:
            # Parse suggestion
            suggestion = self._get_word_from_collins_url(sender.page().url().url())
            if suggestion is not None and suggestion != self._worker[idx]["subject"]:
                self.collins_suggestion_retrieved.emit(self._worker[idx]["subject"], suggestion)
            # Retrieve freq and tip
            sender.page().runJavaScript("document.documentElement.outerHTML",
                                        # Pass subject string instead of idx in this async case
                                        lambda html: self._collins_web_to_html_callback(self._worker[idx]["subject"],
                                                                                        html))
            # Clean up page
            sender.page().runJavaScript(self.COLLINS_POST_JS)

    def queue(self, subject: str, query: int):
        c = self._query_count.get((subject, query))
        if c is not None and c > 0:  # have queued
            self._query_count[(subject, query)] = c + 1  # only increment counter
        else:
            self._query_count[(subject, query)] = 1
            self._pending_queries.append((subject, query))

    def request(self, subject: str, query: int):
        # Search in _started_queries
        for q in self._started_queries:
            if q[0] == subject and q[1] == query:
                worker = q[2]
                self._active_worker = worker
                if worker in self._finished_workers:
                    self.worker_activated.emit(worker, True)
                else:
                    self.worker_activated.emit(worker, False)
                    self.active_worker_progress.emit(worker, self._worker[worker]["progress"])
                return

        if (subject, query) in self._pending_queries:  # if the query is in _pending_queries, remove it
            self._pending_queries.remove((subject, query))
        else:  # otherwise, the query is in neither _started_queries nor _pending_queries
            c = self._query_count.get((subject, query))
            assert (c is None or c == 0), "_query_count inconsistent"
            self._query_count[(subject, query)] = 1  # need to increment _query_count

        # If there is free worker, use it immediately
        if len(self._free_workers) > 0:
            self._query_timer.start(self.QUERY_INTERVAL)  # reset the timer

            worker = self._free_workers.popleft()
            self._working_workers.append(worker)
            self.report_worker_usage()

            self._active_worker = worker  # set before start_worker for proper progress update

            self.start_worker.emit(worker, self.URLS[query] % subject)

            self.worker_activated.emit(worker, False)

            return

        # If not, postpone the last started query and use its worker
        self._query_timer.start(self.QUERY_INTERVAL)  # reset the timer

        (s, q, worker) = self._started_queries.pop()
        self._pending_queries.appendleft((s, q))

        if worker in self._working_workers:
            self._working_workers.remove(worker)
        elif worker in self._finished_workers:
            self._finished_workers.remove(worker)
        self._working_workers.append(worker)
        self.report_worker_usage()

        self._active_worker = worker  # set before start_worker for proper progress update

        self.start_worker.emit(worker, self.URLS[query] % subject)

        self.worker_activated.emit(worker, False)

    def discard_by_subject(self, subject):
        for query in range(4):
            c = self._query_count.get((subject, query))
            if c is not None and c > 0:
                c -= 1
                self._query_count[(subject, query)] = c
                if c == 0:  # only actually discard query when duplication count goes to 0
                    for q in self._started_queries:
                        if q[0] == subject and q[1] == query:
                            self._started_queries.remove(q)
                    for q in self._pending_queries:
                        if q[0] == subject and q[1] == query:
                            self._pending_queries.remove(q)

    def _handle_progress(self, idx: int, progress: int):
        self._worker[idx]["progress"] = progress
        self.worker_progress.emit(idx, progress)
        if self._active_worker == idx:
            self.active_worker_progress.emit(self._active_worker, progress)
            if progress == 100:
                self.worker_activated.emit(self._active_worker, True)

    @staticmethod
    def _parse_collins_freq(html: str) -> (int, str):
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

    def _get_word_from_collins_url(self, url: str):
        if url.startswith(self.URLS[self.COLLINS][:-2]):
            ret = url[len(self.URLS[self.COLLINS][:-2]):]
            if ret.find("?") != -1:
                ret = ret[:ret.find("?")]
            return ret.replace("-", " ")
        else:
            return None

    def _collins_web_to_html_callback(self, subject: str, html: str):

        (freq, tips) = self._parse_collins_freq(html)
        self.collins_freq_retrieved.emit(subject, freq, tips)

    @QtCore.pyqtSlot()
    def _query_timer_timeout(self):
        if len(self._free_workers) > 0 and len(self._pending_queries) > 0:
            worker = self._free_workers.popleft()
            subject, query = self._pending_queries.popleft()
            self._working_workers.append(worker)
            self.report_worker_usage()
            self.start_worker.emit(worker, self.URLS[query] % subject)

    def report_worker_usage(self):
        self.worker_usage.emit(len(self._finished_workers), len(self._working_workers), len(self._free_workers))
