from typing import Optional, Union, List, Deque, cast
from enum import Enum
from dataclasses import dataclass
from collections import deque

from PyQt6 import QtWidgets, QtCore, QtWebEngineWidgets
from pyquery import PyQuery


class QueryType(Enum):
    COLLINS = 0
    GOOGLE_IMAGE = 1
    GOOGLE_TRANSLATE = 2
    GOOGLE = 3


@dataclass
class Query:
    subject: str
    query_type: QueryType
    cid: int  # card id


QuerySettings = {
    "CollinsDirectory": "english",
    "TranslateFrom": "en",
    "TranslateTo": "zh-CN"
}


class QueryWorker(QtWidgets.QWidget):
    """
    A worker for queries.
    If get_query() returns None, the worker is free.
    If get_query() is not None and working_on_query() if false, the worker is working.
    Otherwise, the worker has finished.
    """

    # Signals
    progress_changed = QtCore.pyqtSignal(int)  # progress, -1 for completed

    collins_suggestion_retrieved = QtCore.pyqtSignal(Query, str)  # query, suggestion
    collins_freq_retrieved = QtCore.pyqtSignal(Query, int, str)  # query, freq, freq_note

    # Internal constants

    _MAC_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/605.1.15"
    _IOS_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"

    _COLLINS_POST_JS = """
        let selectors = ['iframe', '.topslot_container', '.cB-hook', '#videos', '.socialButtons', '.tabsNavigation',
                         '.res_cell_right', '.btmslot_a-container', '.exercise', '.mpuslot_b-container',
                         '._hj-f5b2a1eb-9b07_feedback_minimized_label', '.share-button', '.ac_leftslot_a',
                         '.new-from-collins'];
        selectors.forEach(selector => document.querySelectorAll(selector).forEach(el => el.remove()));
        """

    _TIMEOUT = 20000  # [ms]

    @staticmethod
    def _get_url(query_type: QueryType, subject: str = "") -> str:
        if query_type == QueryType.COLLINS:
            return u"https://www.collinsdictionary.com/dictionary/%s/%s" % (QuerySettings["CollinsDirectory"], subject)
        elif query_type == QueryType.GOOGLE_IMAGE:
            return u"https://www.google.com/search?tbm=isch&q=%s" % subject
        elif query_type == QueryType.GOOGLE_TRANSLATE:
            return u"https://translate.google.com/?sl=%s&tl=%s&text=%s" % (QuerySettings["TranslateFrom"],
                                                                           QuerySettings["TranslateTo"], subject)
        elif query_type == QueryType.GOOGLE:
            return u"https://www.google.com/search?q=%s" % subject

    def __init__(self, parent: Optional['QtWidgets.QWidget'] = None) -> None:
        super().__init__(parent)

        self._query: Optional[Query] = None
        self._progress: int = 0
        self._working_on_query: bool = False

        # Create a QWebEngineView centralized in a QHBoxLayout
        self._webview: QtWebEngineWidgets.QWebEngineView = QtWebEngineWidgets.QWebEngineView(self)
        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._webview)

        # Setup the QWebEngineView
        self._webview.page().profile().setHttpUserAgent(self._MAC_USER_AGENT)
        self._webview.page().profile().setProperty("X-Frame-Options", "Deny")  # this prevents some ads from loading

        # Prevent webView from grabbing focus when calling load() or stop()
        self._webview.settings().setAttribute(self._webview.settings().WebAttribute.FocusOnNavigationEnabled, False)

        # Signals
        self._webview.loadStarted.connect(lambda progress=0: self._handle_progress_change(progress))
        self._webview.loadProgress.connect(lambda progress: self._handle_progress_change(progress))
        self._webview.loadFinished.connect(self._handle_load_finished)

        # Create a timer to timeout the QWebEngineView
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._timer_timeout)

    def start(self, query: Query) -> None:
        """Start a query."""
        self._query = query
        self._webview.load(QtCore.QUrl(self._get_url(query.query_type, query.subject)))
        self._working_on_query = True
        self._timer.start(self._TIMEOUT)
        QtCore.QCoreApplication.processEvents()

    def stop(self) -> None:
        self._webview.stop()
        QtCore.QCoreApplication.processEvents()
        # self._working_on_query will be cleared by signal

    def free(self) -> None:
        self._working_on_query = False
        self._webview.stop()
        self._query = None

    def get_query(self) -> Query:
        return self._query

    def working_on_query(self) -> bool:
        return self._working_on_query

    def get_progress(self) -> int:
        return self._progress

    @QtCore.pyqtSlot(bool)
    def _handle_load_finished(self, ok: bool):
        self._timer.stop()

        if self._working_on_query:  # loadFinished can be triggered by manual browsing
            self._working_on_query = False  # set this before emitting any signal

            # self._query may be None due to async
            if self._query is not None and self._query.query_type == QueryType.COLLINS:

                sender: QtWebEngineWidgets.QWebEngineView = cast(QtWebEngineWidgets.QWebEngineView, self.sender())

                # Clean up page
                sender.page().runJavaScript(self._COLLINS_POST_JS)
                QtCore.QCoreApplication.processEvents()

                # Parse suggestion
                suggestion = self._get_word_from_collins_url(sender.page().url().url())
                subject = self._query.subject
                # Space will be replace by '-' in url, but there are cases that subject itself contains '-'
                if suggestion is not None and suggestion != subject.replace(' ', '-'):
                    self.collins_suggestion_retrieved.emit(self._query, suggestion)

                # Retrieve freq and note
                sender.page().runJavaScript("document.documentElement.outerHTML", self._collins_web_to_html_callback)

        self._handle_progress_change(-1)

    @QtCore.pyqtSlot(int)
    def _handle_progress_change(self, progress: int):
        self._progress = progress
        self.progress_changed.emit(progress)

    @QtCore.pyqtSlot()
    def _timer_timeout(self):
        self._webview.stop()  # will trigger self._handle_load_finished

    @staticmethod
    def _get_word_from_collins_url(url: str) -> Optional[str]:
        """
        Parse Collins URL and get queried word. Apply this function on final URL (possibly redirected) to get the word
        suggestion.
        :param url:
        :return:
        """
        if url.startswith(QueryWorker._get_url(QueryType.COLLINS)):
            ret = url[len(QueryWorker._get_url(QueryType.COLLINS)):]
            if ret.find("?") != -1:
                ret = ret[:ret.find("?")]
            return ret
        else:
            return None

    def _collins_web_to_html_callback(self, html: str):
        if self._query is None:  # this can happen due to async callback
            return
        (freq, note) = self._parse_collins_freq(html)
        self.collins_freq_retrieved.emit(self._query, freq, note)

    @staticmethod
    def _parse_collins_freq(html: str) -> (int, str):
        """
        Parse Collins webpage html and return frequency and note.
        :param html:
        :return: (freq, note)
        """
        try:
            doc = PyQuery(html)
            freq_obj = doc(".word-frequency-img")
            if freq_obj is None:
                return 0, "Fail to find the word"
            freq_attr = freq_obj.attr("data-band")
            if freq_attr is None:
                return 0, "Fail to find the word"
            return int(freq_attr), freq_obj.attr("title")
        except Exception as err:
            return 0, str(err)


class WebQueryView(QtWidgets.QWidget):
    """A container managing multiple QWebEngineViews."""

    usage_updated = QtCore.pyqtSignal(int, int, int)  # finished, working, free
    active_worker_progress = QtCore.pyqtSignal(int)  # progress (-1 for completed or no active worker)

    collins_suggestion_retrieved = QtCore.pyqtSignal(int, str)  # cid, suggestion
    collins_freq_retrieved = QtCore.pyqtSignal(int, int, str)  # cid, freq, freq_note

    _PREFETCH_LENGTH = 5
    _PREFETCH_ISSUE_INTERVAL = 5000  # [ms]
    _DELAY_REQUEST_TIME = 2000  # [ms]

    def __init__(self, parent: Optional['QtWidgets.QWidget'] = None) -> None:

        super().__init__(parent)

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        # List of workers
        self._workers: List[QueryWorker] = []
        self._active_worker: Optional[QueryWorker] = None

        # Create prefetch workers
        for i in range(self._PREFETCH_LENGTH):
            self._allocate_a_new_worker()

        # Create prefetch timer
        self._prefetch_timer = QtCore.QTimer()
        self._prefetch_timer.setSingleShot(False)  # repeatedly
        self._prefetch_timer.timeout.connect(self._issue_prefetch)
        self._prefetch_timer.start(self._PREFETCH_ISSUE_INTERVAL)

        # List of queries to prefetch
        self._queue: Deque[Query] = deque()

        # Timer to handle delayed queries
        self._delay_request: Optional[Query] = None
        self._delay_request_timer = QtCore.QTimer()
        self._delay_request_timer.setSingleShot(True)
        self._delay_request_timer.timeout.connect(self._delay_request_timeout)

    def prefetch_queued(self, subject: str, query_type: QueryType, cid: int) -> None:
        """Put a prefetch request to the end of the queue."""
        self._queue.append(Query(subject, query_type, cid))

    def prefetch_immediately(self, subject: str, query_type: QueryType, cid: int) -> None:
        """Prefetch a webpage immediately."""
        self._prefetch_immediately(subject, query_type, cid)

    def _prefetch_immediately(self, subject: str, query_type: QueryType, cid: int) -> QueryWorker:
        """Internal implementation of prefetch_immediately and return the worker for the query."""
        query = Query(subject, query_type, cid)

        # Check whether there is a worker working on the query
        worker = self._search_worker_working_on_query(query)
        if worker is not None:
            return worker

        # Issue prefetch
        worker = self._get_a_free_worker()
        if worker is None:
            worker = self._allocate_a_new_worker()
        worker.start(query)
        return worker

    def request(self, subject: str, query_type: QueryType, cid: int) -> None:
        """Show a webpage."""
        worker = self._prefetch_immediately(subject, query_type, cid)
        # If the query is already prefetched, return the worker that is loading or has loaded the query
        # Is not, the returned worker is assigned to fetch the query

        # Activate the worker
        self._set_active_worker(worker)

    def delay_request(self, subject: str, query_type: QueryType, cid: int) -> None:
        """Show a webpage after some time."""
        self._delay_request = Query(subject, query_type, cid)
        self._delay_request_timer.start(self._DELAY_REQUEST_TIME)

    def discard_by_cid(self, cid: int):
        # Search in workers
        for worker in self._workers:
            if worker.get_query() is not None and worker.get_query().cid == cid:
                worker.free()
        self._recycle_workers()
        self.report_worker_usage()

        # Search in queue
        for query in self._queue:
            if query.cid == cid:
                self._queue.remove(query)

    def force_stop_active_worker(self) -> None:
        if self._active_worker is not None:
            self._active_worker.stop()

    def reset(self) -> None:
        self._queue.clear()  # clear this first to avoid any new prefetch
        self._set_active_worker(None)
        for worker in self._workers:
            worker.free()
        self._recycle_workers()
        self.report_worker_usage()

    def report_worker_usage(self):
        finished_count = 0
        working_count = 0
        free_count = 0
        for w in self._workers:
            if w.get_query() is None:
                free_count += 1
            elif w.working_on_query():
                working_count += 1
            else:
                finished_count += 1
        self.usage_updated.emit(finished_count, working_count, free_count)

    def has_prefetched(self, subject: str, query_type: QueryType, cid: int) -> bool:
        return self._search_worker_working_on_query(Query(subject, query_type, cid)) is not None

    def _search_worker_working_on_query(self, query: Query) -> Optional[QueryWorker]:
        for worker in self._workers:
            if worker.get_query() == query:
                return worker
        return None

    def _set_active_worker(self, worker: Optional[QueryWorker]) -> None:
        """
        Hide the original active worker (if not None), set self._active_worker, make the new active worker visible
        (if not None) and emit active_worker_progress.
        """
        if self._active_worker is not None:
            self._active_worker.setVisible(False)
        self._active_worker = worker
        if worker is not None:
            worker.setVisible(True)
            self.active_worker_progress.emit(worker.get_progress())
        else:
            self.active_worker_progress.emit(-1)

    def _issue_prefetch(self):
        if len(self._queue) == 0:
            return  # nothing to prefetch

        worker = self._get_a_free_worker()
        if worker is None:
            return  # prefetch only if there is a free worker

        query = self._queue.popleft()

        # Check whether there is a worker working on the query
        if self._search_worker_working_on_query(query) is not None:
            return

        worker.start(query)

    def _get_a_free_worker(self) -> Optional[QueryWorker]:
        """Get a free QueryWorker (excluding the active worker). If all workers are busy, return None."""
        for worker in self._workers:
            if worker.get_query() is None:
                return worker
        return None

    def _allocate_a_new_worker(self) -> QueryWorker:
        """Create a new worker, add it to self._workers and return."""
        worker = QueryWorker(self)
        self._workers.append(worker)
        worker.setVisible(False)
        worker.progress_changed.connect(self._handle_worker_progress)
        worker.collins_freq_retrieved.connect(self._handle_collins_freq)
        worker.collins_suggestion_retrieved.connect(self._handle_collins_suggestion)
        self._layout.addWidget(worker)
        return worker

    def _recycle_workers(self) -> None:
        """Deallocate exceeded workers. Do not call this function inside an iteration of self._workers."""
        if len(self._workers) <= self._PREFETCH_LENGTH:
            return

        # Search in workers and gather workers to delete
        delete_list: List[QueryWorker] = []
        for worker in self._workers:
            if worker.get_query() is None:
                if len(self._workers) - len(delete_list) > self._PREFETCH_LENGTH:
                    delete_list.append(worker)
                else:
                    break

        # Delete workers
        if len(delete_list) > 0:
            for worker in delete_list:
                if worker is self._active_worker:
                    self._set_active_worker(None)
                self._workers.remove(worker)
                worker.deleteLater()
            delete_list.clear()
            QtCore.QCoreApplication.processEvents()

    @QtCore.pyqtSlot(int)
    def _handle_worker_progress(self, progress: int):
        worker: QueryWorker = cast(QueryWorker, self.sender())
        if worker is self._active_worker:
            self.active_worker_progress.emit(progress)
        self.report_worker_usage()

    @QtCore.pyqtSlot(Query, str)
    def _handle_collins_suggestion(self, query: Query, suggestion: str):
        self.collins_suggestion_retrieved.emit(query.cid, suggestion)

    @QtCore.pyqtSlot(Query, int, str)
    def _handle_collins_freq(self, query: Query, freq: int, freq_note: str):
        self.collins_freq_retrieved.emit(query.cid, freq, freq_note)

    @QtCore.pyqtSlot()
    def _delay_request_timeout(self):
        if self._delay_request is not None:
            self.request(self._delay_request.subject, self._delay_request.query_type, self._delay_request.cid)
            self._delay_request = None
