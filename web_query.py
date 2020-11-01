#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import deque

from PyQt5 import QtCore
from PyQt5 import QtWebEngineWidgets
from pyquery import PyQuery as pq


class QueryManager(QtCore.QObject):
    """
    Web Query manager module.

    The main purpose of introducing such an individual module is to achieve properly-scheduled pre-queries. When the
    user has a list of word and works on one of them, MapleVocabUtility may initiate web queries of later words.
    When the user switches to the later words, queried web pages can be presented immediately. The number of pre-loaded
    web pages are limited so that the memory and internet usage is bounded.

    Each web page is loaded in a QWebEngineView object, which is called a 'worker' in current module. MainWindow is
    responsible for creating QWebEngineView objects, while this module controls them through signals.

    Interface of this module is designed to hide scheduling details from MainWindow. MainWindow supplies a list of
    words, and ask for web sites at the time they are needed. This module will notify the MainWindow to make a specific
    worker visible while hiding the others. Ideally, the web site would has been loaded in the QWebEngineView. If not,
    then it must be loading...
    """

    # ================================ Signals ================================

    # Signals to control QWebEngineView
    start_worker = QtCore.pyqtSignal(int, str)  # worker, url
    interrupt_worker = QtCore.pyqtSignal(int)  # worker

    # Signals for MainWindow to update UI
    worker_progress = QtCore.pyqtSignal(int, int)  # worker, progress
    worker_usage = QtCore.pyqtSignal(int, int, int, str)  # finished, working, free, tooltip
    worker_activated = QtCore.pyqtSignal(int, bool)  # worker, finished
    active_worker_progress = QtCore.pyqtSignal(int, int)  # active_worker, process

    # Signals for MainWindow to update data or perform actions
    delay_request_activated = QtCore.pyqtSignal(str, int)  # subject, query
    collins_suggestion_retrieved = QtCore.pyqtSignal(str, str)  # original_subject, suggestion
    collins_freq_retrieved = QtCore.pyqtSignal(str, int, str)  # original_subject, freq, tip

    COLLINS = 0
    GOOGLE_IMAGE = 1
    GOOGLE_TRANSLATE = 2
    GOOGLE = 3

    # ================================ Internal Constants ================================

    _URLS = [
        u"https://www.collinsdictionary.com/dictionary/english/%s",
        u"https://www.google.com/search?tbm=isch&q=%s",
        u"https://translate.google.com/?sl=en&tl=zh-CN&text=%s",
        u"https://www.google.com/search?q=%s"
    ]

    _MAC_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/605.1.15"
    _IOS_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"

    _COLLINS_POST_JS = """
    let selectors = ['iframe', '.topslot_container', '.cB-hook', '#videos', '.socialButtons', '.tabsNavigation',
                     '.res_cell_right', '.btmslot_a-container', '.exercise', '.mpuslot_b-container',
                     '._hj-f5b2a1eb-9b07_feedback_minimized_label', '.share-button', '.ac_leftslot_a',
                     '.new-from-collins'];
    selectors.forEach(selector => document.querySelectorAll(selector).forEach(el => el.remove()));
    """

    _DELAY_REQUEST_TIME = 3000  # [ms]
    _QUERY_INTERVAL = 10000  # [ms]
    _QUERY_INTERRUPT_TIME = 20000  # [ms]

    def __init__(self, worker_count: int):
        super().__init__()

        self._worker_count = worker_count

        self._worker = []
        # Notice: do not use [{...}] * worker_count, since dict is mutable
        for i in range(worker_count):
            self._worker.append({
                "subject": "",
                "query": -1,
                "progress": 0,
                "forced_stopped": False
            })

        self._active_worker = -1  # index of the active worker, which is also the visible one in MainWindow

        # Worker index lists
        self._finished_workers = deque()
        self._working_workers = deque()
        self._free_workers = deque()
        for i in range(self._worker_count):
            self._free_workers.append(i)

        # Timers to monitor each worker and timeout them
        self._worker_timer = []
        for i in range(self._worker_count):
            timer = QtCore.QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda idx=i: self._worker_timeout(idx))
            self._worker_timer.append(timer)

        # Lists of query requests
        self._query_count = {}  # (subject, query) -> int
        self._pending_queries = deque()  # (subject, query)
        self._started_queries = deque()  # [subject, query, worker]

        # Timer to initiate queries in period
        self._query_timer = QtCore.QTimer()
        self._query_timer.setSingleShot(False)
        self._query_timer.timeout.connect(self._query_timer_timeout)
        self._query_timer.start(self._QUERY_INTERVAL)

        # Timer to handle delayed queries
        self._delay_request = None
        self._delay_request_timer = QtCore.QTimer()
        self._delay_request_timer.setSingleShot(True)
        self._delay_request_timer.timeout.connect(self._delay_request_timeout)

    def reset(self):
        # Reset all workers
        for worker in self._working_workers:
            self._force_stop_worker(worker)
            # It won't take place immediately since it involves signal. But when it happens, the slot
            # load_finished won't try to remove it from _working_workers
        self._finished_workers.clear()
        self._working_workers.clear()
        self._free_workers = deque()
        for i in range(self._worker_count):
            self._free_workers.append(i)
        self.report_worker_usage()

        if self._active_worker != -1:
            self._active_worker = -1
            self.worker_activated.emit(-1, True)

        # Reset all timer, except _query_timer
        for timer in self._worker_timer:
            timer.stop()
        self._delay_request_timer.stop()

        # Clear all queries
        self._query_count.clear()
        self._pending_queries.clear()
        self._started_queries.clear()
        self._delay_request = None

    @QtCore.pyqtSlot(int)
    def load_started(self, idx: int):
        self._handle_progress(idx, 0)
        # Moving current worker to self._working_worker is completed before this

    @QtCore.pyqtSlot(int, int)
    def load_progress(self, idx: int, progress: int):
        self._handle_progress(idx, progress)

    @QtCore.pyqtSlot(int, bool)
    def load_finished(self, idx: int, ok: bool):

        if self._worker[idx]["forced_stopped"]:
            # When forced stopped, worker position in lists (_working_workers, etc.) must already be handled externally
            # Also, there is nothing to do with the result
            self._worker[idx]["forced_stopped"] = False
            # But this must be set here, rather than at the time calling start_worker.emit, or it may not work since
            # signals are asynchronous.
            return
        if idx not in self._working_workers:
            # Cause by accessing new url within webView itself
            return

        self._handle_progress(idx, 100)
        self._working_workers.remove(idx)
        self._finished_workers.append(idx)
        self.report_worker_usage()

        sender: QtWebEngineWidgets.QWebEngineView = self.sender()
        if self._worker[idx]["query"] == self.COLLINS:
            # Parse suggestion
            suggestion = self._get_word_from_collins_url(sender.page().url().url())
            subject = self._worker[idx]["subject"]
            # Space will be replace by '-' in url, but there are cases that subject itself contains '-'
            if suggestion is not None and suggestion != subject.replace(' ', '-'):
                self.collins_suggestion_retrieved.emit(subject, suggestion)

            # Retrieve freq and tip
            sender.page().runJavaScript("document.documentElement.outerHTML",
                                        # Pass subject string instead of idx in this async case
                                        lambda html, s=subject: self._collins_web_to_html_callback(s, html))
            QtCore.QCoreApplication.processEvents()
            # Clean up page
            sender.page().runJavaScript(self._COLLINS_POST_JS)

    def apply_suggestion(self, subject: str, suggestion: str):
        # Update query info to avoid the worker from losing track
        for i in range(len(self._started_queries)):
            if self._started_queries[i][0] == subject and self._started_queries[i][1] == self.COLLINS:
                self._started_queries[i][0] = suggestion
                self._query_count[(subject, self.COLLINS)] -= 1
                c = self._query_count.get((suggestion, self.COLLINS))
                if c is None:
                    self._query_count[(suggestion, self.COLLINS)] = 1
                else:
                    self._query_count[(suggestion, self.COLLINS)] = c + 1
                self._worker[self._started_queries[i][2]]["subject"] = suggestion

    def queue(self, subject: str, query: int, front: bool = False):
        c = self._query_count.get((subject, query))
        if c is not None and c > 0:  # have queued
            self._query_count[(subject, query)] = c + 1  # only increment counter
        else:
            self._query_count[(subject, query)] = 1
            if front:
                self._pending_queries.appendleft((subject, query))
            else:
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
            self._query_timer.start(self._QUERY_INTERVAL)  # reset the timer

            worker = self._free_workers.popleft()
            self._working_workers.append(worker)
            self.report_worker_usage()

            self._active_worker = worker  # set before start_worker for proper progress update
            self.worker_activated.emit(worker, False)

            self._start_worker(worker, subject, query)

            return

        # If not, postpone the last started query and use its worker
        self._query_timer.start(self._QUERY_INTERVAL)  # reset the timer

        s, q, worker = tuple(self._started_queries.pop())
        self._pending_queries.appendleft((s, q))

        if worker in self._working_workers:
            self._force_stop_worker(worker)
            # It won't take place immediately since it involves signal. But when it happens, the slot load_finished
            # won't try to remove it from _working_workers

            # Leave it in _working_workers
        else:
            self._finished_workers.remove(worker)
            self._working_workers.append(worker)
        self.report_worker_usage()

        self._active_worker = worker  # set before start_worker for proper progress update
        self.worker_activated.emit(worker, False)

        self._start_worker(worker, subject, query)
        # It's safe even if the worker hasn't actually stopped yet, since signals are sent in the order they emitted

    def delay_request(self, subject: str, query: int):
        """
        If the query is already started, request immediately. If not, delay for _DELAY_REQUEST_TIME before actually
        request or cancel if discarded during the delay time
        :param subject:
        :param query:
        :return:
        """
        if self._find_in_started_queries(subject, query):
            self.request(subject, query)
            # Still start the _delay_request_timer for delay_request_activated signal

        self._delay_request = (subject, query)
        # If there is already a delay request, simply overwrite it and reset timer as follows
        self._delay_request_timer.start(self._DELAY_REQUEST_TIME)

    def discard_by_subject(self, subject):
        for query in range(4):
            c = self._query_count.get((subject, query))
            if c is not None and c > 0:
                c -= 1
                self._query_count[(subject, query)] = c

                if c == 0:  # only actually discard query when duplication count goes to 0

                    # Search in _started queries
                    to_remove = self._find_in_started_queries(subject, query)
                    if to_remove is not None:
                        worker = to_remove[2]
                        self._started_queries.remove(to_remove)
                        if worker in self._working_workers:
                            self._force_stop_worker(worker)
                            # It won't take place immediately since it involves signal. But when it happens, the slot
                            # load_finished won't try to remove it from _working_workers
                            self._working_workers.remove(worker)
                        else:
                            self._finished_workers.remove(worker)
                        self._free_workers.append(worker)
                        self.report_worker_usage()

                    # Search in started _pending_queries
                    try:
                        self._pending_queries.remove((subject, query))
                    except ValueError:
                        pass

            if self._delay_request == (subject, query):
                self._delay_request = None

    @QtCore.pyqtSlot()
    def force_stop_active_worker(self):
        self._worker_timeout(self._active_worker)

    # ================================ Helper Functions ================================

    def _force_stop_worker(self, idx: int) -> None:
        """
        Force a working worker to stop. When it stopped, slot load_finished will be triggered but do nothing. Worker's
        location in worker lists (_working_worker, etc.) must be managed manually (this function will do nothing about
        this.)
        :param idx:
        :return:
        """
        assert idx in self._working_workers, "Worker %d is not working" % idx
        self._worker[idx]["forced_stopped"] = True
        self.interrupt_worker.emit(idx)
        if idx == self._active_worker:
            self._active_worker = -1
            self.worker_activated.emit(-1, True)

    def _find_in_started_queries(self, subject: str, query: int) -> list:
        ret = None
        for q in self._started_queries:
            if q[0] == subject and q[1] == query:
                ret = q
                break
        return ret

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
        if url.startswith(self._URLS[self.COLLINS][:-2]):
            ret = url[len(self._URLS[self.COLLINS][:-2]):]
            if ret.find("?") != -1:
                ret = ret[:ret.find("?")]
            return ret
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
            self._start_worker(worker, subject, query)

    @QtCore.pyqtSlot(int)
    def _worker_timeout(self, idx: int):
        if idx in self._working_workers:  # if still working
            self.interrupt_worker.emit(idx)  # stop normally, not force stop

    def _start_worker(self, idx: int, subject: str, query: int) -> None:
        self._worker[idx]["subject"] = subject
        self._worker[idx]["query"] = query
        self._started_queries.append([subject, query, idx])
        self.start_worker.emit(idx, self._URLS[query] % subject)
        self._worker_timer[idx].start(self._QUERY_INTERRUPT_TIME)

    def report_worker_usage(self):
        tooltips = []
        for i in range(self._worker_count):
            tooltips.append("%d: %s %s" % (i, self._worker[i]["subject"], self._worker[i]["query"]))
        self.worker_usage.emit(len(self._finished_workers), len(self._working_workers), len(self._free_workers), "\n".join(tooltips))

    @QtCore.pyqtSlot()
    def _delay_request_timeout(self):
        if self._delay_request is not None:
            self.request(self._delay_request[0], self._delay_request[1])
            self.delay_request_activated.emit(self._delay_request[0], self._delay_request[1])
            self._delay_request = None
