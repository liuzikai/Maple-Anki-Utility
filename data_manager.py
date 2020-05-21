#!/usr/bin/python
# -*- coding: utf-8 -*-

from data_source import *
from data_export import *
from html_cleaner import *
from PyQt5 import QtCore
from typing import Optional, Union


class DataManager(QtCore.QObject):
    UNVIEWED = 0  # not viewed yet
    TOPROCESS = 1  # already viewed at least one (has been pronounced)
    CONFIRMED = 2
    DISCARDED = 3

    # Signals
    record_status_changed = QtCore.pyqtSignal(int, int, int)  # index, old_status, new_status
    record_cleared = QtCore.pyqtSignal()
    record_inserted = QtCore.pyqtSignal(int, bool)  # index, batch_loading(True)/add_single(False)
    record_batch_load_finished = QtCore.pyqtSignal()
    record_count_changed = QtCore.pyqtSignal()

    def __init__(self, output_path: str):

        super().__init__()

        self._db: Union[None, KindleDB, CSVDB] = None

        self._records = []
        self._counts = [0] * 4

        self._output_path: str = output_path
        self._exporter: Optional[DataExporter] = None  # lazy construct

    def __del__(self):
        if self._db is not None:
            del self._db
        if self._exporter is not None:
            self._exporter.close_file()
            del self._exporter

    def get(self, idx: int) -> dict:
        return self._records[idx]

    def get_by_subject(self, subject: str) -> [dict]:
        ret = []
        for r in self._records:
            if r["subject"] == subject:
                ret.append(r)
        return ret

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
            r["status"] = self.UNVIEWED
            r["pron"] = "Unknown"
            r["para"] = r["ext"] = r["hint"] = ""
            r["img"] = None  # no image
            r["freq"] = 0
            r["card"] = "R"
            r["tips"] = ""
            r["source_enabled"] = (r["source"] != "")
            r["usage"] = r["usage"].replace(r["subject"], u"<b>%s</b>" % r["subject"])
            r["suggestion"] = None

            self.record_inserted.emit(i, True)

        self._counts[self.UNVIEWED] = len(self._records)
        self._counts[self.TOPROCESS] = self._counts[self.CONFIRMED] = self._counts[self.DISCARDED] = 0

        self.record_count_changed.emit()
        self.record_batch_load_finished.emit()

    def set_status(self, idx: int, status: int) -> None:
        """
        Set record status
        :param idx: index of record entry
        :param status: one of RecordStatus
        :return:
        """

        r = self._records[idx]
        if r["status"] == status:  # nothing needs to be done
            return

        old_status = r["status"]

        if old_status in [self.CONFIRMED, self.DISCARDED] and status in [self.UNVIEWED, self.TOPROCESS]:
            self._db.set_word_mature(r["word_id"], 0)  # retract db status

        if old_status == self.CONFIRMED:
            if self._exporter is not None:
                self._exporter.retract_subject(r["subject"])

        self._counts[old_status] -= 1
        r["status"] = status
        self._counts[status] += 1

        if status == self.CONFIRMED:
            if self._exporter is None:
                self._construct_exporter()
            self._save_entry(idx)

        if status in [self.CONFIRMED, self.DISCARDED]:
            if self._db and r.get("word_id") is not None:
                self._db.set_word_mature(r["word_id"], 100)
                self._db.commit_changes()

        self.record_status_changed.emit(idx, old_status, status)
        self.record_count_changed.emit()

    def _construct_exporter(self) -> None:
        save_file = "%s/maple-%s.txt" % (self._output_path, datetime.now().strftime('%Y-%m-%d-%H%M%S'))
        self._exporter = DataExporter()
        self._exporter.open_file(save_file)

    def _save_entry(self, idx: int) -> None:
        r = self._records[idx]

        example = clean_html(r["usage"])
        if r["source_enabled"] and r["source"] != "":
            example += "<br>" + '<div align="right" style="font-size:12px">' + clean_html(
                r["source"]) + '</div>'
        mp3 = self._exporter.generate_media(r["subject"], r["pron"]) if r["pron"] != "Unknown" else ""
        para = clean_html(r["para"])
        if r["img"]:
            img_file = self._exporter.new_random_filename("png")
            r["img"].save("%s/%s" % (self._exporter.media_path, img_file))
            para += '<div><br><img src="%s"><br></div>' % img_file
        self._exporter.write_entry(r["subject"],
                                   "[sound:%s]" % mp3,
                                   para,
                                   clean_html(r["ext"]),
                                   example,
                                   r["hint"],
                                   r["freq"],
                                   "1" if "R" in r["card"] else "",
                                   "1" if "S" in r["card"] else "",
                                   "1" if "D" in r["card"] else "")

    def add_new_single_entry(self, idx: int, subject: str = "", usage: str = "", source_enabled: bool = False,
                             source: str = '<div align="right" style="font-size:12px"></div>') -> None:
        new_entry = {
            "status": self.UNVIEWED,
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
        self._counts[self.UNVIEWED] += 1
        self.record_count_changed.emit()
