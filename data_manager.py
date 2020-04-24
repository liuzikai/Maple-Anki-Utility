#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from pyquery import PyQuery
from data_source import *
from data_export import *
from PyQt5 import QtCore

UNVIEWED = 0  # not viewed yet
TOPROCESS = 1  # already viewed at least one (has been pronounced)
CONFIRMED = 2
DISCARDED = 3


def html_extract(h: str) -> str:
    if len(h.strip()) == 0:
        return ""
    pq = PyQuery(h)
    if pq:
        p = pq("p")
        if p:
            return p.html().strip()
    return h


class DataManager(QtCore.QObject):

    # Signals
    record_status_changed = QtCore.pyqtSignal(int, int, int)  # index, old_status, new_status
    record_cleared = QtCore.pyqtSignal()
    record_inserted = QtCore.pyqtSignal(int, bool)  # index, batch_loading(True)/add_single(False)
    record_count_changed = QtCore.pyqtSignal()
    save_progress = QtCore.pyqtSignal(int)  # index to highlight

    def __init__(self):

        super().__init__()

        self._db = None
        self.has_changed = False

        self._records = []
        self._counts = [0] * 4

    def __del__(self):
        del self._db

    def get(self, idx: int) -> dict:
        return self._records[idx]

    def count(self, status=None) -> int:
        if status is None:
            return len(self._records)
        else:
            return self._counts[status]

    def clear(self) -> None:
        """
        Helper function to clear all _records.
        :return: None
        """

        self._records = []
        self._counts = [0] * 4

        # Signals
        self.record_cleared.emit()
        self.record_count_changed.emit()

    def reload_kindle_data(self, db_file: str) -> bool:
        """
        Clear _records and load _records from Kindle.
        :return: True if file exists, False otherwise
        """
        if not os.path.isfile(db_file):
            return False

        # Set up database to KindleDB
        if self._db is not None:
            del self._db
            self._db = None
        self._db = KindleDB(db_file)

        self._reload_from_db()

        return True

    def reload_csv_data(self, csv_file: str) -> bool:
        """
        Clear _records and load _records from CSV file.
        :return: True if file exists, False otherwise
        """
        if not os.path.isfile(csv_file):
            return False

        # Setup database to CSV DB
        if self._db is not None:
            del self._db
            self._db = None
        self._db = CSVDB(csv_file)

        self._reload_from_db()

        return True

    def _reload_from_db(self) -> None:

        self.clear()  # will emit signals

        self._records = self._db.fetch_all(new_only=True)

        # Initialize additional fields
        for i, r in enumerate(self._records):
            r["status"] = UNVIEWED
            r["pron"] = "Unknown"
            r["para"] = r["ext"] = r["hint"] = ""
            r["img"] = None  # no image
            r["freq"] = 0
            r["card"] = "R"
            r["tips"] = ""
            r["source_enabled"] = (r["source"] != "")
            r["usage"] = r["usage"].replace(r["subject"], u"<b>%s</b>" % r["subject"])

            self.record_inserted.emit(i, True)

        self._counts[UNVIEWED] = len(self._records)
        self._counts[TOPROCESS] = self._counts[CONFIRMED] = self._counts[DISCARDED] = 0

        self.record_count_changed.emit()

    def save_all(self, output_path: str) -> str:
        """
        Helper function to save all _records
        :return: Saved filename
        """

        save_file = "%s/maple-%s.txt" % (output_path, datetime.now().strftime('%Y-%m-%d-%H%M%S'))
        exporter = DataExporter()
        exporter.open_file(save_file)

        record_count = len(self._records)
        for i in range(record_count):

            r = self._records[i]

            # Set UI
            if record_count < 150 or i % (int(record_count / 100)) == 0 or r["status"] in [CONFIRMED, DISCARDED]:
                # Only show parts of animation to accelerate saving process
                self.save_progress.emit(i)

            # Generate data
            if r["status"] == CONFIRMED:

                example = html_extract(r["usage"])
                if r["source_enabled"] and r["source"] != "":
                    example += "<br>" + '<div align="right">' + html_extract(r["source"]) + '</div>'
                mp3 = exporter.generate_media(r["subject"], r["pron"])
                para = html_extract(r["para"])
                if r["img"]:
                    img_file = exporter.new_random_filename("png")
                    r["img"].save("%s/%s" % (exporter.media_path, img_file))
                    para += '<div><br><img src="%s"><br></div>' % img_file
                exporter.write_entry(r["subject"],
                                     "[sound:%s]" % mp3,
                                     para,
                                     html_extract(r["ext"]),
                                     example,
                                     r["hint"],
                                     r["freq"],
                                     "1" if "R" in r["card"] else "",
                                     "1" if "S" in r["card"] else "",
                                     "1" if "D" in r["card"] else "")

            # Write back to DB
            if r["word_id"] is not None:
                if r["status"] == CONFIRMED or r["status"] == DISCARDED:
                    self._db.set_word_mature(r["word_id"], 100)

        if self._db is not None:
            self._db.commit_changes()

        exporter.close_file()

        self.has_changed = False

        return save_file

    def set_status(self, idx: int, status: int) -> None:
        """
        Set record status
        :param idx: index of record entry
        :param status: one of RecordStatus
        :return:
        """

        if self._records[idx]["status"] == status:  # nothing needs to be done
            return

        if status == CONFIRMED or status == DISCARDED:
            self.has_changed = True

        old_status = self._records[idx]["status"]

        self._counts[old_status] -= 1
        self._records[idx]["status"] = status
        self._counts[status] += 1

        self.record_status_changed.emit(idx, old_status, status)
        self.record_count_changed.emit()

    def add_new_single_entry(self, idx: int, subject: str = "", usage: str = "", source_enabled: bool = False,
                             source: str = '<div align="right" style="font-size:12px"></div>') -> None:
        new_entry = {
            "status": UNVIEWED,
            "word_id": None,
            "subject": subject,
            "pron": "Unknown",
            "para": "",
            "ext": "",
            "usage": usage,
            "source": source,
            "source_enabled": source_enabled,
            "hint": "",
            "img": None,  # no image
            "freq": 0,
            "card": "R",
            "tips": ""
        }

        self._records.insert(idx, new_entry)

        self.record_inserted.emit(idx, False)
        self.record_count_changed.emit()
