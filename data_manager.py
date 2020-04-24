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


class DataManager:

    def __init__(self):
        self.db = None
        self.has_changed = False

        self.records = []
        self.counts = [0] * 4

        self.save_progress = QtCore.pyqtSignal(int)
        self.record_status_changed = QtCore.pyqtSignal(int, int, int)
        self.record_cleared = QtCore.pyqtSignal()
        self.record_inserted = QtCore.pyqtSignal(int)
        self.record_count_changed = QtCore.pyqtSignal()

    def __del__(self):
        del self.db

    def clear_records(self) -> None:
        """
        Helper function to clear all records.
        :return: None
        """

        self.records = []
        self.counts = [0] * 4

        # Signals
        self.record_cleared.emit()
        self.record_count_changed.emit()

    def reload_kindle_data(self, db_file: str) -> bool:
        """
        Clear records and load records from Kindle.
        :return: True if file exists, False otherwise
        """
        if not os.path.isfile(db_file):
            return False

        # Set up database to KindleDB
        if self.db is not None:
            del self.db
            self.db = None
        self.db = KindleDB(db_file)

        self.reload_from_db()

        return True

    def reload_csv_data(self, csv_file: str) -> bool:
        """
        Clear records and load records from CSV file.
        :return: True if file exists, False otherwise
        """
        if not os.path.isfile(csv_file):
            return False

        # Setup database to CSV DB
        if self.db is not None:
            del self.db
            self.db = None
        self.db = CSVDB(csv_file)

        self.reload_from_db()

        return True

    def reload_from_db(self) -> None:

        self.clear_records()  # will emit signals

        self.records = self.db.fetch_all(new_only=True)

        # Initialize additional fields
        for r in self.records:
            r["status"] = UNVIEWED
            r["pron"] = "Unknown"
            r["para"] = r["ext"] = r["hint"] = ""
            r["img"] = None  # no image
            r["freq"] = 0
            r["card"] = "R"
            r["tips"] = ""
            r["source_enabled"] = (r["source"] != "")
            r["usage"] = r["usage"].replace(r["subject"], u"<b>%s</b>" % r["subject"])
            # TODO: record_insert emit

        self.counts[UNVIEWED] = len(self.records)

        self.record_count_changed.emit()

    def get_count(self, status=None) -> int:
        if status is None:
            return len(self.records)
        else:
            return self.counts[status]

    def save_all(self, output_path: str) -> str:
        """
        Helper function to save all records
        :return: Saved filename
        """

        save_file = "%s/maple-%s.txt" % (output_path, datetime.now().strftime('%Y-%m-%d-%H%M%S'))
        exporter = DataExporter()
        exporter.open_file(save_file)

        record_count = len(self.records)
        for i in range(record_count):

            r = self.records[i]

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
                    self.db.set_word_mature(r["word_id"], 100)

        if self.db is not None:
            self.db.commit_changes()

        exporter.close_file()

        self.has_changed = False

        return save_file

    def set_record_status(self, idx: int, status: int) -> None:
        """
        Set UI and change record entry.
        :param idx: index of record entry
        :param status: one of RecordStatus
        :return:
        """

        if self.records[idx]["status"] == status:  # nothing needs to be done
            return

        if status == CONFIRMED or status == DISCARDED:
            self.has_changed = True

        old_status = self.records[idx]["status"]

        self.counts[old_status] -= 1
        self.records[idx]["status"] = status
        self.counts[status] += 1

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

        self.records.insert(idx, new_entry)

        self.record_inserted.emit(idx)
        self.record_count_changed.emit()
